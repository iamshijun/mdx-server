# -*- coding: utf-8 -*-
# version: python 3.5

import threading
import re
import os
import sys

from wsgiref.simple_server import make_server
from file_util import *
from mdx_util import *
from mdict_query import IndexBuilder
from urllib.parse import parse_qs

"""
browser URL:
http://localhost:8000/test
"""

content_type_map = {
    'html': 'text/html; charset=utf-8',
    'js': 'application/x-javascript',
    'ico': 'image/x-icon',
    'css': 'text/css',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'mp3': 'audio/mpeg',
    'mp4': 'audio/mp4',
    'wav': 'audio/wav',
    'spx': 'audio/ogg',
    'ogg': 'audio/ogg',
    'eot': 'font/opentype',
    'svg': 'text/xml',
    'ttf': 'application/x-font-ttf',
    'woff': 'application/x-font-woff',
    'woff2': 'application/font-woff2',
}

try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    #base_path = sys._MEIPASS
    base_path = os.path.dirname(sys.executable)
except Exception:
    base_path = os.path.abspath(".")
        
resource_path = os.path.join(base_path, 'mdx')
print("resouce path : " + resource_path)
builder = None
builders = {}
dict_processor={}

def get_url_map():
    result = {}
    files = []

    # resource_path = '/mdx'
    file_util_get_files(resource_path, files)
    for p in files:
        if file_util_get_ext(p) in content_type_map:
            p = p.replace('\\', '/')
            result[re.match('.*?/mdx(/.*)', p).groups()[0]] = p
    return result


def application(environ, start_response):
     # 允许所有来源（生产环境应指定具体域名）
    headers = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
    ]
    if environ["REQUEST_METHOD"] == "OPTIONS":
        start_response("204 No Content", headers)
        return []
    
    path_info = environ['PATH_INFO'].encode('iso8859-1').decode('utf-8')
    query_string = environ['QUERY_STRING']
    
    print("path_info:", path_info)
    m = re.match('/(.*)', path_info)
    word = ''
    if m is not None:
        word = m.groups()[0]
    print('search word:',word)
    
    url_map = get_url_map()
    get_params = parse_qs(query_string)
    #print("url_map:",url_map)

    if path_info in url_map:
        url_file = url_map[path_info]
        content_type = content_type_map.get(file_util_get_ext(url_file), 'text/html; charset=utf-8')
        start_response('200 OK', [('Content-Type', content_type)])
        return [file_util_read_byte(url_file)]
    elif file_util_get_ext(path_info) in content_type_map:
        content_type = content_type_map.get(file_util_get_ext(path_info), 'text/html; charset=utf-8')
        start_response('200 OK', [('Content-Type', content_type)])
        if builder is None:
            return [b'']
        return get_definition_mdd(path_info, builder)
    else:
        start_response('200 OK', headers + [('Content-Type', 'text/html; charset=utf-8')])
       
        if 'dict' in get_params: #选择查询单个词典的    
            dict_name = get_params['dict'][0]
            print('use dict:',dict_name,dict_name in builders)    
            if dict_name in builders:
                index_builder = builders[dict_name]
                return get_definition_mdx(word, index_builder)
            else:
                return [b'<h1>Dict not found</h1>']
        # 列出所有词典的结果 
       
        results = []
        results.append(f"<title>{word}</title>".encode("utf-8"))
        results.append(_get_common_style().encode("utf-8"))
        
        for dict_name,index_builder in builders.items():
            query_result = get_definition_mdx(path_info[1:], index_builder)
            if query_result and len(query_result) > 0:
                results.append(f"<div data-name='{dict_name}' class='dict-query-result'>".encode('utf-8'))
                results.append(f"<h2>{dict_name}</h2>".encode('utf-8'))
                results.append(query_result[0])
                results.append(b"</div>")
                results.append(b"<hr/>")
        return results


    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [b'<h1>WSGIServer ok!</h1>']


def _get_common_style(): 
     # fixme 暂时 先这样写死 
    # 给 meaning，exg style给 "小学館デジタル大辞泉"的 ,exmaple标签在 明鏡国語辞典
    return """<style>
        span[data-name="用例"],
        span[data-name="語義"], 
        span[data-name="語義G"], 
        span[data-name="解説部"],
        span[data-name="準大語義num"],
        example {
            display: block;
        }        
        .example {
            padding: 0 7px;
        }
        meaning ,exg, maccentaudiog {
            display: block;
        }
        .meaning , span[data-name="用例"]{
            margin: 7px 0;
        }
        
        hinshisahen, span[data-name="rect"],span[data-name="logo"],  {
            margin: 0px 7px;
        }
        
        rect.L3.bold.FM {
            margin-right: 7px;
        }
        div[class="unit-example"] {
            margin: 7px 0;
        }
        div[class="unit-example"] p {
            display:inline;
        }
        span[class="example-source"]::after {
            content: ' - ';
        }
        ul.ncdata-sense-wrap {
            display: inline;
            list-style-type: none;
            padding-inline-start: 1px;
            word-break: break-word;
            word-wrap: break-word;
        }

        ul.ncdata-sense-wrap > li {
            display: inline;  
            word-break: break-word;
            word-wrap: break-word;
        }
        whitediamond::before , .divide-imgs::before {
            content: '\A';
            white-space: pre;
        }
        .divide-imgs + span {
            color: rgb(20, 62, 127);
        }
        fbox {
            margin: 0 10px;
        }     
    </style>"""

# 新线程执行的代码
def loop():
    # 创建一个服务器，IP地址为空，端口是8000，处理函数是application:
    httpd = make_server('', 8000, application)
    print("Serving HTTP on port 8000...")
    # 开始监听HTTP请求:
    httpd.serve_forever()

class MyDict :
    def __init__(self,path:str,dict_name:str = None,style_class:str = None):
        self.path = path
        if dict_name is None:
            dict_name = os.path.basename(path).replace('.mdx','').replace('.mdd','')
        self.dict_name = dict_name
        self.style_class = style_class
        if not os.path.exists(path):
            raise FileNotFoundError(f"MDX/MDD file {path} not exist")
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs='*', help="mdx file name")
    args = parser.parse_args() 

    dicts:list[MyDict] = []
    if len(args.filenames) < 1: #read config.toml
        import tomllib
        with open("config.toml","rb") as f:
            config = tomllib.load(f)
        
        dict_configs = config["dicts"]
        for dict_config in dict_configs :
            dicts.append(MyDict(dict_config["path"], dict_config.get("name", None)))
    else :
        for filename in args.filenames:  
            dict_name = None
            if ":" in filename: #可以在文件名称前面 用 "dict_name:filepath" 的格式 指定
                tokens = filename.split(":")
                dict_name = tokens[0]
                filename = tokens[1]
                
            if len(filename.strip()) == 0:
                continue    
            dicts.append(MyDict(filename,dict_name))
            
        
    for mdict in dicts:   
        print(f"add dict file: {mdict.path}, name: {mdict.dict_name}")    
        builders[mdict.dict_name] = IndexBuilder(mdict.path)
    
    t = threading.Thread(target=loop, args=())
    t.start()
