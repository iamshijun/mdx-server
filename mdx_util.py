# -*- coding: utf-8 -*-
# version: python 3.5

import sys
import re
from file_util import *
from mdict_query import IndexBuilder

def get_definition_mdx(word, builder:IndexBuilder):
    """根据关键字得到MDX词典的解释"""
    content = builder.mdx_lookup(word)
    # if len(content) < 1:
    #     fp = os.popen('python lemma.py ' + word) #找到词元
    #     word = fp.read().strip()
    #     fp.close()
    #     print("lemma: " + word)
    #     content = builder.mdx_lookup(word)
        
    if len(content) == 0:
        fuzzy_words = builder.get_mdx_keys(word,1) # 根据前缀模糊找第一个    
        if len(fuzzy_words) > 0:
            content = builder.mdx_lookup(fuzzy_words[0])
    # 还是没找到
    if len(content) == 0:
        #return None
        return [b'']
    
    pattern = re.compile(r"@@@LINK=(.*)")
    #print("found content: " + str(content))
    rst = pattern.match(content[0])
    if rst is not None:
        link = rst.group(1).strip()
        content = builder.mdx_lookup(link)
    str_content = ""
    if len(content) > 0:
        for c in content:
            process_content = c.replace("\r\n","").replace("entry:/","")
            process_content = re.sub(r"<rt[^>]*>[^<]*</rt>","", process_content) #去掉<ruby>标签下的 <rt> 注音或注释
            process_content = re.sub(r"<wari[^>]*>[^<]*</wari>","", process_content)#wari 是小学馆的注音方式
            process_content = re.sub(r'<span data-name="ルビ">.*?</span>',"", process_content)  #还有放在 自定义的样式里的
            process_content = re.sub(r'<img[^>]*/?>',"", process_content) #去掉img　标签
            process_content = re.sub(r"<HeaderTitle>[^<]*</HeaderTitle>","", process_content) 
            process_content = re.sub(r'<img[^>]*?alt="([^"]+)".*?/?>',r"\1",process_content)  # 将图片中的alt 提出来 替换掉img
            process_content = re.sub("<entry-index[^>]*>.*</entry-index>","", process_content,1,re.DOTALL)
            str_content += process_content

    injection = []
    injection_html = ''
    output_html = ''

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # base_path = sys._MEIPASS
        base_path = os.path.dirname(sys.executable)
    except Exception:
        base_path = os.path.abspath(".")
            
    resource_path = os.path.join(base_path, 'mdx')

    file_util_get_files(resource_path, injection)

    for p in injection:
        if file_util_is_ext(p, 'html'):
            injection_html += file_util_read_text(p)

    #return [bytes(str_content, encoding='utf-8')]
    output_html = str_content + injection_html
    return [output_html.encode('utf-8')]

def get_definition_mdd(word, builder:IndexBuilder):
    """根据关键字得到MDX词典的媒体"""
    word = word.replace("/","\\")
    content = builder.mdd_lookup(word)
    if len(content) > 0:
        return [content[0]]
    else:
        return []
