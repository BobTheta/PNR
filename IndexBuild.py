#-*-coding:utf-8-*-
'''
Created on 2015-1-27

@author: 张江涛
'''
import codecs
import re
import marisa_trie
from basecode import *
from WordsSplit import SplitByLanguage
import time

def is_blank(uchar):
        """判断一个unicode是否是空格"""
        if uchar == ' ' or uchar == '\t':
                return True
        else:
                return False
            
def is_chinese(uchar):
        """判断一个unicode是否是汉字"""
        if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
                return True
        else:
                return False
def is_chs(str):
        for uchar in str:
            if not is_chinese(uchar):
                return False
        return True

def is_number(uchar):
        """判断一个unicode是否是数字"""
        if uchar >= u'\u0030' and uchar<=u'\u0039':
                return True
        else:
                return False
def is_nums(str):
        for uchar in str:
            if not is_number(uchar):
                return False
        return True

def is_alphabet(uchar):
        """判断一个unicode是否是英文字母"""
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
                return True
        else:
                return False

def is_other(uchar):
        """判断是否非汉字，数字和英文字符"""
        if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
                return True
        else:
                return False
            
def is_other_alphabet(uchar):
        """判断是否非汉字和英文字符"""
        if not (is_chinese(uchar) or is_alphabet(uchar)):
                return True
        else:
                return False
def is_others(str):
        for uchar in str:
            if not is_other_alphabet(uchar):
                return False
        return True
            
def is_parentheses(uchar):
        """判断是否括号"""
        if uchar in "{（）【《》】[(])}":
                return True
        else:
                return False
            
def extract_cn_pre (str):
    for i in range(0,len(str)):
        if is_alphabet(str[i]) :
            break
    flag = True
    if i != 0 and i < len(str)-1:
        for c in str[i+1:]:
            if  is_chinese(c):
                flag = False
                break
    else :
        flag = False
    if flag :
        for offset in range(1,i+1):
            if is_other(str[i-offset]):
                offset +=1
            else:
                break
#         print(str)
        return str[:i-offset+1]
    else :
        return ""

def split_en_cn (str):
    for i in range(0,len(str)):
        if is_alphabet(str[i]) :
            break
    flag = True
    if i != 0 and i < len(str)-1:
        for c in str[i+1:]:
            if  is_chinese(c):
                flag = False
                break
    else :
        flag = False
    if flag :
        for offset in range(1,i+1):
            if is_other(str[i-offset]):
                offset +=1
            else:
                break
#         print(str)
        return [str[:i-offset+1],str[i:]]
    else :
        return []
    
def extract_parentheses (str):
    for i in range(0,len(str)):
        if is_parentheses(str[i]) :
            break
    if i < len(str)-1 :
        return str[:i].strip()
    else :
        return ""
    
def trunc_parentheses (str):
    par_exists = False
    for i in range(0,len(str)):
        if is_parentheses(str[i]) :
            par_exists = True
            break
    if par_exists :
        return str[:i].strip()
    else :
        return str
    
    
def trie_build(m2e) :
    mentions = m2e.keys()
    trie = marisa_trie.Trie(mentions)
    return trie
   
def m2e_build(fin) :
    fi=codecs.open(fin,'r',"utf-8")
#     print('open begin')
    m2e = dict();
    for line in fi:
#         print(line)
        pair = re.split('::;',line.strip())
        if len(pair)<4 :
            continue
        if pair[3] != 'title': 
            continue
        mention = pair[0]
        if len(mention) < 2:
            continue
        entity = pair[1]
        mention = mention.lower().strip()
        
        if len(mention) < 2:
            continue
        for token in re.split(':;',mention):
            if len(token) < 2:
                continue
            for p_name in re.split('[·-]',token):
                m2e[token] = list(set(m2e.get(token, []) +[entity]))
                person_name = token.replace("·","").replace("-","")
                if person_name != token:
                    if len(person_name) < 2:
                        continue
                    m2e[person_name] = list(set(m2e.get(person_name, []) +[entity]))
                
        if c_e:
            if len(trunc_parentheses(c_e[0])) < 2 or len(trunc_parentheses(c_e[1])) < 2:
                continue
            m2e[trunc_parentheses(c_e[0])] = list(set(m2e.get(trunc_parentheses(c_e[0]), []) +[entity]))
            m2e[trunc_parentheses(c_e[1])] = list(set(m2e.get(trunc_parentheses(c_e[1]), []) +[entity]))
 
        person_name = mention.replace("·","").replace("-","")
        if person_name != mention:
            if len(person_name) < 2 or len(trunc_parentheses(person_name)) < 2:
                continue
            m2e[person_name] = list(set(m2e.get(person_name, []) +[entity]))
            m2e[trunc_parentheses(person_name)] = list(set(m2e.get(trunc_parentheses(person_name), []) +[entity]))
            c_e = split_en_cn(person_name)
            if c_e:
                if len(trunc_parentheses(c_e[0])) < 2 or len(trunc_parentheses(c_e[1])) < 2:
                    continue
                m2e[trunc_parentheses(c_e[0])] = list(set(m2e.get(trunc_parentheses(c_e[0]), []) +[entity]))
                m2e[trunc_parentheses(c_e[1])] = list(set(m2e.get(trunc_parentheses(c_e[1]), []) +[entity]))   
        

    
    return m2e
    fi.close()
    
def m2e_build_www(fin) :
    fi=codecs.open(fin,'r',"utf-8")
#     print('open begin')

    m2e = dict();
    for line in fi:
#         print(line)
        pair = re.split(':',line.strip(),1)
        if len(pair)<2 :
            continue
        mention = pair[0]
        if len(mention) < 2 and (not is_chinese(mention)):
            continue
        entity = pair[1]
        mention = mention.lower()
        sbl = SplitByLanguage()
        split = sbl.splitNames(mention)
        for name in split:
            if len(name) < 2 and (not is_chinese(name)):
                continue
#             print(name +": " + entity)
            m2e[name] = list(set(m2e.get(name, []) +[entity]))
            if "·" in name :
                m2e[name.replace("·","")] = list(set(m2e.get(name.replace("·",""), []) +[entity]))
                for s in name.split('·'):
                    m2e[s] = list(set(m2e.get(s, []) +[entity]))
            
        
        
    
    return m2e
    fi.close()
    
def m2e_build_stopWords(f1,f2) :
    fi=codecs.open(f1,'r',"utf-8")
#     print('open begin')
    stop_words = []
    f = codecs.open(f2,'r',"utf-8")
    for word in f:
        stop_words.append(word.strip())
    f.close()
    m2e = dict();
    for line in fi:
        
        pair = re.split("::;",line.strip())
        if len(pair)<4 :
            
            continue
        if pair[3].strip() != 'title': 
            continue
        mention = pair[0].lower().strip()
        entity = pair[1]
        for token in re.split(':;',mention):
            if (token in stop_words) or is_others(token) or len(token) < 2:
                continue
            m2e[token] = list(set(m2e.get(token, []) +[entity]))
            m2e[token.replace(" ","")] = list(set(m2e.get(token.replace(" ",""), []) +[entity]))
            if " " in token:
                for m in re.split(' ',token):
                    if is_chs(m):
                        m2e[m] = list(set(m2e.get(m, []) +[entity]))
            if "·" in token or "-" in token :
                m2e[token.replace("·","").replace("-","")] = list(set(m2e.get(token.replace("·","").replace("-",""), []) +[entity]))
                for subs in re.split('[·-]',token):
                    if (subs in stop_words ) or is_others(subs) or len(subs) <2:
                        continue
                    m2e[subs] = list(set(m2e.get(subs, []) +[entity]))
           #         print(line)
       
    fi.close()
    return m2e
    
    
def save_m2e(m2e,fout):
    fo = codecs.open(fout,'w',"utf-8")
    for mention in m2e :
        fo.write(mention + ':::')
        enList = m2e[mention]
        for entity in enList :
            fo.write(entity + '::;')
        fo.write('\n')
    fo.close()
    
if __name__ == '__main__':
#     m2e = m2e_build_www('./data/movie.mentions_new.mentions')
    begin = time.time()
    m2e = m2e_build_stopWords('./data/movie.mentions.split','./data/EnglishStopWords.txt')
    end1 = time.time()
    print('m2e has been created! the time is : %.4f'%(end1-begin))
    save_m2e(m2e, './data/mention.entity.noalias')
    end2 = time.time()
    print('m2e has been written! the time is : %.4f'%(end2-end1))
#     trie = trie_build(m2e)
#     end3 = time.time()
#     print('trie has been created! the time is : %.4f'%(end3-end2))
#     trie.save('./data/m2e.trie')
#     print('trie has been written! the time is : %.4f'%(time.time()-end3))
    print('the total time is: %.4f'%(time.time()-begin))
    
    
#     m2e = m2e_build_www('./data/movie.mentions_new.mentions')
#     m2e = m2e_build_stopWords('./data/movies','./data/EnglishStopWords.txt')
#     print('m2e have been created!')
#     save_m2e(m2e, './data/m2e_test')
#     print('m2e have finished!')
#     trie = trie_build(m2e)
#     trie.save('./data/m2e_test.trie')
    
#     m2e = m2e_build_www('./data/movies')
# #     m2e = m2e_build_stopWords('./data/movies','./data/EnglishStopWords.txt')
#     print('m2e have been created!')
#     save_m2e(m2e, './data/m2e')
#     print('m2e have finished!')
#     trie = trie_build(m2e)
#     trie.save('./data/trie')
#     
#     trie = marisa_trie.Trie()
#     trie.load('./data/m2e.trie')
#     result = trie.keys(u'克里夫梅利森')
#     print(result)
#     result = trie.keys(u'她')
#     print(result)

#     str = u"爱德华诺顿(adh) Edward Norton"
#     str2 = "sjgiklgj"
#     set1 = (str) + (str2)
#     print(set1[0])
#     print(trunc_parentheses(str))
# #     print(extract_cn_pre(str))
#     print(trunc_parentheses(split_en_cn(str)[0]) +" " + trunc_parentheses(split_en_cn(str)[1]))
