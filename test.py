# %%  
import re
word = 'いやいや【嫌嫌】'
word = re.sub(r"[^【]*【(.*)】",r"\1",word)
print(word)
# %%
