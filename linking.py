#!/usr/bin/env python
#-*-coding=utf-8-*-

import codecs
import jieba
import marisa_trie
import re
import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')
from model.query import Query
from model.little_entity import LittleEntity
from disambiguation import *
from db import *
import json
from time import *
from basecode import *
from extract_mentions import extract_mentions_ansj
import model.global_var


class MovieEL():

    def __init__(self,flag,comment,db ,movie_id ,movie_commented,threshold ):
        
        self.flag = flag
        self.movie_id = movie_id
        self.movie_commented = movie_commented
        self.comment = comment
        self.context_mentions = [] 
        self.queries = []
        self.db = db
        self.threshold = threshold
#         self.full_mentions = None        
        
    def destroy(self):
        del self.comment
        del self.context_mentions
        del self.db
        del self.queries
        del self.movie_id

    def set_topic_mentions(self, mentions):
        self.full_mentions = mentions
        
    def is_filtered(self,mention):
        
        if mention in model.global_var.STOP_WORDS or len(mention) < 2:
            return True
            
        if len(mention) < 3:
            for uchar in mention:
                if is_chinese(uchar):
                    return False
        else:
#             return False
            for uchar in mention:
                if is_chinese(uchar) or is_alphabet(uchar):
                    return False
        return True
    
    def run(self):
       
#         mentions = self.extract_mentions(self.comment)
#         print(self.comment)
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
        mentions = extract_mentions_ansj(self.comment)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.CUT_WORDS_TIME1 = time.time() - current_time
            current_time = time.time()
        for m in mentions:
#             print(m[0])
            if self.is_filtered(m[0]):
                continue
            self.queries.append(Query(m[0],m[1]))
            self.context_mentions.append(m[0])
        if model.global_var.STATISTIC_FLAG:
            model.global_var.APPEND_MENTIONS = time.time() - current_time
        self.get_entity()

      
    def word_segmentation(s):
        """
        Returns:
        seg_index: list of tuple, tuple(seg, place of this seg in s)
        """
        jieba.load_userdict('./data/usr.dict')
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
    
#     @staticmethod    
    def extract_mentions(self, comment):
        """
        Extract mentions from comment
        正向最大匹配中文分词算法
        http://hxraid.iteye.com/blog/667134
        """

        mentions = []
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
#         print ("comment:"+comment)
        segs = self.word_segmentation(comment)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.CUT_WORDS_TIME = time.time() - current_time
            print('model.global_var.CUT_WORDS_TIME: %.4f'%model.global_var.CUT_WORDS_TIME)
            print(segs)
        i = 0
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
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
                            offset -= 1 #逆向筛选时offset要回退，否则就会跳空分词
                            if t in self.trie:
                                #self.queries.append(Query(t, segs[i][1]))
                                mentions.append((t, segs[i][1]))
#                                 print(t)
                                break
                        if len(s) > 0 and s[0] in model.global_var.PUNCT:#加入len(s) > 0的判断是有可能s为空
                            offset = 1 #如果字符串的第一个字是标点，可能会影响匹配结果，跳过标点再匹配
                    break
            i += offset
#         print(mentions)
        if model.global_var.STATISTIC_FLAG:
            max_match_time = time.time() - current_time
            print('maxlen_match_time: %.4f'%max_match_time)
            print('extracted mentions :%d'%len(mentions))
            print(mentions)
        return mentions
    

    def get_entity(self):

#         mentions = [q.text for q in self.queries]
        entity_sim_scores = dict()
        total_cans = set()

        for q in self.queries:
            q.entities = []
            cans = model.global_var.MENTION_ENTITY.get(q.text, [])
       
            q.candidates = [c.strip().split("/")[-1] for c in cans]
            total_cans = total_cans.union(set(q.candidates))
        
            
        if total_cans:
#             if model.global_var.STATISTIC_FLAG:
#                 current_time = time.time()
            
            args = {
                    "movie_id":self.movie_id,
                    "movie_commented":self.movie_commented,
                    "cans":total_cans,
                    "context_mentions":self.context_mentions,
                    "db":self.db,
                    }
                      
            if self.flag:    
                ############# movie_known ########### 
                if self.threshold is None:    
                    self.threshold = 3.0 
                entity_sim_scores = movie_related_ranking(**args)                
            else:
                ############# movie_unknown ###########
                if self.threshold is None:    
                    self.threshold = 4.5
                entity_sim_scores = jaccard_sim_ranking(**args)
#             if model.global_var.STATISTIC_FLAG:
#                 model.global_var.RANKING_TIME = (time.time() - current_time)
        if model.global_var.DEBUG:
            self.threshold = 0.0
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
        for q in self.queries:
            c_sim = {}
            for c in q.candidates:
                c_sim[c] = entity_sim_scores[c]
            
                    
            best = max(c_sim.items(), key=lambda x:x[1][0])
            confidence = best[1][0]
#             print(self.comment)
#             print('q.text :' + q.text)
#             print('q.index :%d' %q.index)
#             print(self.comment[q.index-1])
#             print(self.comment[q.index+ len(q.text)])
            if (q.index > 0) and (q.index + len(q.text) < len(self.comment)):#括号内命名实体
                if self.comment[q.index-1] in u"《【[#" and self.comment[q.index + len(q.text)] in  u"》】]#":
                    confidence = best[1][0] if best[1][0] >= self.threshold else self.threshold
            if confidence >= self.threshold :
                uri = model.global_var.PREFIX + 'instance/' + best[0]
                e = LittleEntity(uri,best[1][1],confidence)
                q.entities.append(e)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.GET_ENTITY = (time.time() - current_time)


def load_mention_entity(fn):
    m_e = {}
    fi =codecs.open(fn,'r',"utf-8")
    for line in fi:
#         line = line.strip()
#         m,es = line.split(":::")
        m,es = re.split(":::",line.strip("\n"))
        es = es.split("::;")
        m_e[m] = es[:-1]

    return m_e

def load_stopwords(fin):
    fi = codecs.open(fin,'r',"utf-8")
    model.global_var.STOP_WORDS = []
    for word in fi:
        model.global_var.STOP_WORDS.append(word.strip())
    fi.close()
    return model.global_var.STOP_WORDS

def get_content(line):
    content = ''
    if "{" in line and "content" in line:            
        main = line[line.find("{"):]
        try:
            comment_dict = json.loads(main)
            content = comment_dict["content"].lower()
            
        except:
            print("error line: " +line)
            content = ''
    else:
        content = ''
    return content



def output(movieel,count,fw):
    mentions = 0
    if model.global_var.ANNOTATION_FLAG:                
        model.global_var.COMMENT_ANNOTATION = movieel.comment
        offset = 0
    for q in movieel.queries:
        if len(q.entities) > 0:
            mentions += 1
            if model.global_var.ANNOTATION_FLAG:
                model.global_var.COMMENT_ANNOTATION = model.global_var.COMMENT_ANNOTATION[:q.index+offset] + '[[' + q.text+'<||>' + ']]' + model.global_var.COMMENT_ANNOTATION[q.index+offset +len(q.text):]
                offset +=8
            for e in q.entities:
                result = {
                          "Comment_id":count,
                          "Mention":q.text,
                          "Pos":q.index,
                          "Uri":e.uri,
                          "Title":e.title,
                          "confidence":e.confidence
                          }
                
                dump = json.dumps(result,ensure_ascii=False,sort_keys = True)
                fw.write(dump)
#                 if model.global_var.DEBUG:
#                     fw.write('(')
#                     for s in e.sim:
#                         fw.write('[')
#                         if type(s) != type(set()):
#                             fw.write(s)
#                         else:
#                             for item in s:
#                                 fw.write(str(item) + ', ')
#                         fw.write('], ')
#                     fw.write(')')
                fw.write('\n')
    return mentions

    
    

def output_annotation(in_file,out_dir,annotation_dict):
    
        fw2 = codecs.open(out_dir +'/' + in_file.split('/')[-1] + '-annotation', 'w', "utf-8")
        annnotation_list = sorted(annotation_dict.items(),key=lambda x:x[0])
        for c in annnotation_list:
            fw2.write('{"comment_id":%d,"content":"%s"'%(c[0],c[1]))
            fw2.write('\n')
        fw2.close()

def open_file_handle(in_file,out_dir):
    
    if model.global_var.CACHE_FLAG:
        model.global_var.WHOLE_INFO_RESULT = {}
        model.global_var.LABEL_DICT = {}
               
    fw = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-result', 'w', "utf-8")
    if model.global_var.STATISTIC_FLAG:
        if model.global_var.CACHE_FLAG: 
            fw_s = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-statistic_cache.csv', 'w', "utf-8")
        else:
            fw_s = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-statistic.csv', 'w', "utf-8")
        fw_s.write('document_id,length,extracted_mentions,candidate_entities,\
                    linked_mentions,total_running_time,cut_words_time1,cut_words_time2,acess_db_time,access_db_times')
        fw_s.write('\n')
        
    if model.global_var.ANNOTATION_FLAG:
        annotation_dict =dict()    
    fi = codecs.open(in_file, 'r', "utf-8")
    return (fi,fw,fw_s)

def linking(flag,in_file,out_dir,title,movie_id,movie_commented,db,threshold):
         
    begin_time = time.time()
#     fi,fw,fw_s = open_file_handle(in_file,out_dir)
    if model.global_var.CACHE_FLAG:
        model.global_var.WHOLE_INFO_RESULT = {}
        model.global_var.LABEL_DICT = {}
               
    fw = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-result', 'w', "utf-8")
    if model.global_var.STATISTIC_FLAG:
        if model.global_var.CACHE_FLAG: 
            fw_s = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-statistic_cache.csv', 'w', "utf-8")
        else:
            fw_s = codecs.open(out_dir+'/' +in_file.split('/')[-1] + '-statistic.csv', 'w', "utf-8")
        fw_s.write('document_id,length,extracted_mentions,candidate_entities,duplicate_removal_candidate_entities,'+
                    'linked_mentions,total_running_time,cut_words_time1,cut_words_time2,get_obj_property,calculate_sim,append_mentions_time,' +
                    'get_entity_time,access_db_time,access_db_times')
        fw_s.write('\n')
        
    if model.global_var.ANNOTATION_FLAG:
        annotation_dict =dict()    
    fi = codecs.open(in_file, 'r', "utf-8")
    count = 0
    full_text = ""
    total_mentions = 0
    print("current article :  "+in_file)
    
    for line in  fi :
        if model.global_var.STATISTIC_FLAG:
            model.global_var.ACCESS_DATABASE_TIMES =0
            model.global_var.ACCESS_DATABASE_TIME = 0
            model.global_var.CUT_WORDS_TIME2 = 0
            model.global_var.GET_OBJ_PROPERTY = 0
            model.global_var.CALCULATE_SIM = 0
        
        c = get_content(line)
        if not c:
            continue
        count += 1
        c = c.strip("\n")
        args = {
                "flag":flag,
                "comment":c,
                "db":db,
                "movie_id":movie_id,
                "movie_commented":movie_commented,
                "threshold":threshold
                }
        movieel = MovieEL(**args)
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
        movieel.run()
#         if model.global_var.STATISTIC_FLAG:
        total_time = time.time() - current_time
        mentions = output(movieel,count,fw) 
        total_mentions +=mentions  
        print("-----linked mentions in the line %d:  %d       running time : %.4f"%(count,mentions,total_time))     
        if model.global_var.STATISTIC_FLAG:
            can_entities = 0
            unique_can_entities = set()
            for q in movieel.queries:
                can_entities += len(q.candidates)
                unique_can_entities = unique_can_entities.union(q.candidates)
    
            fw_s.write('%d,%d,%d,%d,%d,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%d'\
                     %(count,len(movieel.comment),len(movieel.queries),can_entities,len(unique_can_entities),mentions,total_time,\
                       model.global_var.CUT_WORDS_TIME1,model.global_var.CUT_WORDS_TIME2,model.global_var.GET_OBJ_PROPERTY,model.global_var.CALCULATE_SIM,\
                       model.global_var.APPEND_MENTIONS,model.global_var.GET_ENTITY,\
                       model.global_var.ACCESS_DATABASE_TIME,model.global_var.ACCESS_DATABASE_TIMES))
            fw_s.write('\n')
        
        if model.global_var.ANNOTATION_FLAG:
            if model.global_var.COMMENT_ANNOTATION.count('[[')>=2 and model.global_var.COMMENT_ANNOTATION.count(']]')>=2:
                annotation_dict[count]= model.global_var.COMMENT_ANNOTATION                           
                if len(annotation_dict) >=50:
                    break
                
        movieel.destroy()
        del movieel
        
    print("-----total linked mentions of this article: %d       runing time : %.4f"%(total_mentions,time.time()-begin_time))
    fw.close()
    if model.global_var.STATISTIC_FLAG:
        fw_s.close()
    if model.global_var.ANNOTATION_FLAG:
        output_annotation(in_file,out_dir,annotation_dict)
    fi.close()
            

    
    
def run(in_dir, out_dir,threshold=None):

    import os
    
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    import time
    
    db = MovieKB()  

    for sub_dir in os.listdir(in_dir):
        
        if model.global_var.STATISTIC_FLAG:
            if model.global_var.CACHE_FLAG: 
                fw_d = codecs.open(out_dir + sub_dir + '-database_access_cache', 'w', "utf-8")
            else:
                fw_d = codecs.open(out_dir + sub_dir + '-database_access', 'w', "utf-8")                
            model.global_var.ACCESS_TIME_DICT = {}
        args = {
                "flag":0,
                "in_file":'',
                "out_dir":'',
                "title":'',
                "movie_id":'',
                "movie_commented":{},
                "db":db,
                "threshold":threshold
                }

        if os.path.isdir(in_dir + sub_dir):
            if not os.path.isdir(out_dir + sub_dir ):
                os.mkdir(out_dir + sub_dir) 
            args["out_dir"] = out_dir + sub_dir
            if '-' in sub_dir:
                pair = sub_dir.split('-')
                title = pair[0]
                movie_id = pair[1]
                print(title)
                print(movie_id)
                movie_commented = db.get_whole_info_label(movie_id)
                if movie_commented:
                    args["flag"] = 1
                    args["title"] = title
                    args["movie_id"] = movie_id
                    args["movie_commented"] = movie_commented
                    
            for name in os.listdir(in_dir+sub_dir):
                args["in_file"] = in_dir + sub_dir + '/' + name
                linking(**args)  
        else:
            args["in_file"] = in_dir + sub_dir
            args["out_dir"] = out_dir
            linking(**args)
        

        if  model.global_var.STATISTIC_FLAG:
            access_times_desc = sorted(model.global_var.ACCESS_TIME_DICT.items(),key=lambda x:x[1], reverse=True)
            for pair in access_times_desc:
                fw_d.write('%s: %d'%(pair[0],pair[1]))
                fw_d.write('\n')
            fw_d.close()
    db.close()
    
if __name__=="__main__":


    begin = time.time()
    model.global_var.MENTION_ENTITY = load_mention_entity("./data/mention.entity.noalias")
    model.global_var.STOP_WORDS = load_stopwords("./data/EnglishStopWords.txt")
    print('dictionary has been loaded using : %.4f'%(time.time()-begin))
 
    if re.match('linux',sys.platform):
        if len(sys.argv) == 3:
            run(sys.argv[1],sys.argv[2])
        elif len(sys.argv) == 4:
            run(sys.argv[1],sys.argv[2],float(sys.argv[3]))
    else:
        run('./data/input/','./data/output/')
