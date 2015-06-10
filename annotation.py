#encoding=utf-8
'''
Created on 2014-11-18

@author: 张江涛
'''
import codecs
import re
import json
import os
import marisa_trie
import jieba
from basecode import *
import time

PUNCT = set(u''':!),.:;?]}¢'"、。〉》」』】〕〗〞︰︱︳﹐､﹒
        ﹔﹕﹖﹗﹚﹜﹞！），．：；？｜｝︴︶︸︺︼︾﹀﹂﹄﹏､～￠
        々‖•·ˇˉ―--′’”([{£¥'"‵〈《「『【〔〖（［｛￡￥〝︵︷︹︻
        ︽︿﹁﹃﹙﹛﹝（｛“‘-—_…''')

def load_stopwords(fin):
    fi = codecs.open(fin,'r',"utf-8")
    stop_words = []
    for word in fi:
        stop_words.append(word.strip())
    fi.close()
    return stop_words

class annotation ():
    def __init__(self,trie,stop_words):
        self.trie = trie
        self.stop_words = stop_words
        
    def word_segmentation(self, s):
        """
        Returns:
        seg_index: list of tuple, tuple(seg, place of this seg in s)
        """
        seg_list = jieba.cut(s, cut_all=False)
#         print (seg_list)
        seg_index = []
        last = 0
        for seg in seg_list:
            seg = seg.strip("/")
            #print re.split('(《》)', seg)[0]
            begin = s.index(seg, last)
            last = begin + len(seg)
            seg_index.append((seg, begin))
    
        return seg_index
    def extract_mentions(self, comment):
        """
        Extract mentions from comment
                    正向最大匹配中文分词算法
        http://hxraid.iteye.com/blog/667134
        """

        mentions = []

#         print ("comment:"+comment)
        segs = self.word_segmentation(comment)
    
        i = 0
        while i < len(segs):
            offset = 1
            temp = []
            while True:
                s = "".join([seg[0] for seg in segs[i:i+offset]])
                if len(self.trie.keys(s)) > 0 and i+offset <= len(segs):# s is prefix or word 
                    temp.append(s) #把可能在tree里找到的都存起来,如： a, aa, aaa 
                    offset += 1
                else: # not prefix or word, search end
                    if len(temp) > 0:
                        temp.reverse() #从最长的字符串开始查找，看是不是在tree里,如果有，就结束查找，生成Query，这部分的遍历就结束了,如：如果有aaa，那aaa就是要找的字符串，aa和a都不要
                        for t in temp:
                            offset -= 1 #张江涛：逆向筛选时offset要回退，否则就会跳空分词
                            if t in self.trie:
                                #self.queries.append(Query(t, segs[i][1]))
                                mentions.append((t, segs[i][1]))
#                                 print(t)
                                break
                        if len(s) > 0 and s[0] in PUNCT:#zjt:加入len(s) > 0的判断是有可能s为空
                            offset = 1 #如果字符串的第一个字是标点，可能会影响匹配结果，跳过标点再匹配
                    break
            i += offset
#         print(mentions)
        return mentions
    
    def is_filtered(self,context,mention):
        
        
        
        if (mention[1] > 0) and (mention[1] + len(mention[0]) < len(context)):#括号内命名实体
            if context[mention[1]-1] in u"《【[#" and context[mention[1] + len(mention[0])] in  u"》】]#":
                return False
            
        if mention[0] in self.stop_words:
            return True
        
        if len(mention[0]) <2:
            return True 
            
        if len(mention[0]) < 3:
            for uchar in mention[0]:
                if is_chinese(uchar):
                    return False
        else:
#             return False
            for uchar in mention[0]:
                if is_chinese(uchar) or is_alphabet(uchar):
                    return False
        return True
    

    
    def mention_labelling(self,in_dir,out_dir):
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        for sub_dir in os.listdir(in_dir):
            if not os.path.isdir(out_dir + sub_dir):
                os.mkdir(out_dir + sub_dir)
            for name in os.listdir(in_dir + sub_dir):
                begin_time = time.time()
                fw = codecs.open(out_dir + sub_dir +'/' + name + '-annotation','w','utf-8')
                fi = codecs.open(in_dir + sub_dir + '/' + name, 'r', 'utf-8')
                count = 0
                for line in fi:
                    if count >= 100: break
                    if '{' in line and 'content' in line:
                        main = line[line.find('{'):]
                        try:
                            comment_dict = json.loads(main)
                            comment = comment_dict['content']
                        except:
                            print('error line: ' + line)
                            continue
                        count += 1
                        comment = comment.strip('\n')
                        mentions = self.extract_mentions(comment)
                        offset = 0
                        for m in mentions:
                            if self.is_filtered(comment,m):
                                continue
                            comment = comment[:m[1]+offset] + '[[' + m[0] + ']]' + comment[m[1]+offset +len(m[0]):]
                            offset +=4
                        fw.write('{"comment_id":%d,"content":"%s"'%(count,comment))
                        fw.write('\n')
                
                print('%s has been completed! run time is :%0.4f'%(sub_dir+name,time.time()-begin_time))
                fw.close()
                fi.close()
                        
        
if __name__ == '__main__':
    trie = marisa_trie.Trie()
    trie.load('./data/m2e.trie') 
    stop_words = load_stopwords("./data/EnglishStopWords.txt")  
    ann = annotation(trie,stop_words)
    ann.mention_labelling("./data/split/", "./data/annotion/")
    
                
                