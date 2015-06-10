#encoding=utf-8
'''
Created on 2014-12-21

@author: 张江涛
'''

import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')    
import urllib 
if sys.version[0] == '3':
    import urllib.request as urllib2
    from urllib.parse import urlencode    
else: 
    import urllib2
    from urllib import urlencode 
import model.global_var 
import time


def extract_mentions_ansj(text):
    text = text.replace("/"," ")
    mentions = []
    param = {u'text':text}

    url = model.global_var.CUT_URL + urlencode(param).encode('utf-8')
    
#     if model.global_var.STATISTIC_FLAG:
#         current_time = time.time()
#         print(url)
    segs = urllib2.urlopen(url).read().decode('utf-8')
    
#     if model.global_var.STATISTIC_FLAG:
#         model.global_var.CUT_WORDS_TIME = time.time() - current_time
# #             print('model.global_var.CUT_WORDS_TIME: %.4f'%model.global_var.CUT_WORDS_TIME)
#         current_time = time.time()
#     print(segs)
    last = 0
    for seg in segs.split(' '):
        token = seg.split("/")[0]
        if token in model.global_var.MENTION_ENTITY:
#                 print(token),
#             mentions.append((token.replace('+',' '),last))
            mentions.append((token,last))
#             print('%s:%d,'%(token,len(token))),
        last += len(token)
    
#         print('\n')
#     if model.global_var.STATISTIC_FLAG:
#         model.global_var.EXACT_MATCH_TIME = time.time() - current_time
        
    return mentions

if __name__ == "__main__":
    text = u'《深夜前的五分钟》最吸引我的，不是主演刘诗诗和张孝全，'
    param = {u'text':text}
    url = model.global_var.CUT_URL + urlencode(param).encode('utf-8')
    segs = urllib2.urlopen(url).read().decode('utf-8')
    print(segs)
    