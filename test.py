# %%  
import re
word = 'いやいや【嫌嫌】'
word = re.sub(r"[^【]*【(.*)】",r"\1",word)
print(word)
# %%
import datetime
import re
upload_file = '/data/www/media/20250619_22.mp4'

regex = r'\d{8}_\d{2}'
match = re.search(regex, upload_file)
        
print(match.group() )
# %%
