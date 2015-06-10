#!/usr/bin/env python
#-*-coding:utf-8-*-

import nltk
import string
import math
import re
import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')
import jieba
from collections import Counter
from model.query import Query
from db import *
from basecode import *
from WordsSplit import SplitByLanguage
import model.global_var
from extract_mentions import extract_mentions_ansj

def normalize(d):
    a = d.values()
    n = len(a)
    mean = sum(a) / n
    std = math.sqrt(sum((x-mean)**2 for x in a) / n)

    for k, v in d.items():
        meanRemoved = v - mean #减去均值  
        stded = meanRemoved / (std+1) #用标准差归一化  
        d[k] = stded
    return d

################# Strategy ####################
def context_sim(mention, cans, doc, db, num=0, threshold=None):
    """
    Compare context of comment and abstract of entity 
    """
    c_sim = {}
    
    def similar_cal(t, cans):
#         print ("candiates:" + ' '+candidates)
        for c in cans:
            print (c)
            a = db.get_abstract(c)
            if a:
                print (c+' ' +'has abstract')

                seg_list = jieba.cut(t, cut_all=False)
                t = " ".join(seg_list)
                seg_list = jieba.cut(a, cut_all=False)
                a = " ".join(seg_list)

                try:
                    c_sim[c] = similarity(t, a)
                except:
                    c_sim[c] = 0.0


                for k,v in c_sim.items():
                    print (k +' ' + str(v))
            else:
                c_sim[c] = 0.0

    def similarity(t1, t2):
        return Distance.cosine_distance(t1.lower(), t2.lower());
    #if len(self.candidates) == 1:
    #    return self.candidates[0]

    similar_cal(doc, cans)

    if threshold:
        for k,v in c_sim.items():
            if v < threshold:
                c_sim.popitem(k)

    return c_sim

def is_person(m):
    result = False
    for type in m.get("instanceOf",[]):
        if type in [u'演员',u'导演',u'制片人',u'编剧',u'摄影师',u'音乐指导','配音','主持人']:
            result = True
            break
    return result

def jaccard_sim_ranking(db,context_mentions,cans,movie_id,movie_commented):
    context_mentions = set(context_mentions)    
    c_sim = {}
#     print('cocntext_mentions is ')
#     for m in context_mentions:
#         print m + ' ',
#     print('\n')
    for c in cans:
        ontology_text_mentions = set()
        ontology_property_mentions = set()
        ontology_name_mentions = set()
        can_obj = db.get_whole_info_label(c)
        for key,value in list(can_obj.items()):
            if key in ('description/zh','summary') and value is not None:
                if model.global_var.STATISTIC_FLAG:
                    current_time = time.time()
                ontology_text_mentions=ontology_text_mentions.union({m[0].decode('utf-8') for m in extract_mentions_ansj(value[0])})
                if model.global_var.STATISTIC_FLAG:
                    model.global_var.CUT_WORDS_TIME2 += (time.time() - current_time)
            elif key in ('label/zh','alias'):
                for token in value:
                    try:
                        ontology_name_mentions=ontology_name_mentions.union(set([t.decode('utf-8') for t in token.split()]))
                    except:
#                         print("entity id:%s  key:%s   token:%s"%(c,key,token))
                        continue
            elif key  not in ('image','toplic_equivalent_webpage','firstimage','alias','label/zh'):
                if model.global_var.STATISTIC_FLAG:
                    current_time = time.time()
                for token in value:
                    try:
                        ontology_property_mentions=ontology_property_mentions.union(set([t.decode('utf-8') for t in token.split()]))
                    except:
#                         print("entity id:%s  key:%s   token:%s"%(c,key,token))
                        continue
                if model.global_var.STATISTIC_FLAG:
                    model.global_var.GET_OBJ_PROPERTY += (time.time() - current_time)
#         print('the candidate is:%s'%c)
#         print('ontology_text_mentions intersect is')
#         for m in ontology_text_mentions & context_mentions:
#             print m + ' ',
#         print('\n')
#         print('ontology_property_mentions intersect is \n')
#         for m in ontology_property_mentions & context_mentions:
#             print m + ' ',
#         print('\n')
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
        if is_person(can_obj):
            score = (float(len(ontology_text_mentions& context_mentions)) \
                    +float(len(ontology_name_mentions& context_mentions)) + 6.0\
                    +5.0*float(len(ontology_property_mentions& context_mentions))) \
                    / math.log10(float(len((context_mentions)))+1)
        else:
            score = (float(len(ontology_text_mentions& context_mentions)) \
                    +float(len(ontology_name_mentions& context_mentions)) \
                    +5.0*float(len(ontology_property_mentions& context_mentions))) \
                    / math.log10(float(len((context_mentions)))+1)
        title = can_obj.get("label/zh",[""])[0]
        c_sim[c] = (score,title)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.CALCULATE_SIM += (time.time() - current_time)
                    

    return c_sim  
            

def movie_related_ranking(db,context_mentions,cans,movie_id,movie_commented):
    """
            利用被评论电影的信息进行ranking
    """
    def movie2movie_sim(m1,m2):
        es = set()
        for key in m1:
            if key not in ("description/zh","summary","image","instanceOf","firstimage","imdb","topic_equivalent_webpage") :
                if key in m2:
                    if key != "actor_list":
                        common = list(set(m1[key])&set(m2[key]))
                        if len(common) :
                            es.add(common[0])
                        
#                     print(key + ":" +str(m1[key]))
#                     print(key + ":" +str(m2[key]))
#                     print(set(m1[key])&set(m2[key]))
                    else:
                        es = es.union(set(m1[key])&set(m2[key]))
        return es
    
    
    def get_obj_list(m):
        obj_list = []
        obj_list += m.get("actor_list",[])
        obj_list += m.get("directed_by",[])
        obj_list += m.get("produced_by",[])
        obj_list += m.get("written_by",[])
        obj_list += m.get("cinematograph_by",[])
        obj_list += m.get("music_by",[])
        obj_list += m.get("presenter",[])
        obj_list += m.get("dubbing_performances",[])
        return obj_list
        
    
#     movie_commented = db.get_whole_info_label(movie_id)
#    print(movie_commented)
#    print(db)
    c_sim = {}
    for c in  cans:
#         print("Can ID: " + c)
        can_obj = db.get_whole_info_label(c)
#	print(can_obj.get("instanceOf",[]))
        es1 = set()#两个电影比较，共现属性名集合
        es2 = set()#人物与电影比较，该人物出现在电影相应人物属性列表中则进该集合，权重*8
        es3 = set()#候选实体为人物，进该集合。权重*3
#         es4 = set()#放在各种括号内的实体一定要加分 权重 *4
        
#         if (location > 0) and (location + len(mention) < len(context)):#括号内命名实体
#             if context[location-1] in u"《【[#" and context[location + len(mention)] in  u"》】]#":
#                 es4.add(mention)
        

#         if len(mention) >=2 or len(es4):
        
        if is_person(can_obj):#候选实体为人物
#             sbl = SplitByLanguage()
            if sys.version[0] == '3':
                p_name = can_obj.get("label/zh",[u""])[0].lower()
            elif sys.version[0] == '2':
                p_name = can_obj.get("label/zh",[u""])[0].lower().decode('utf8')
# #                 print("the person name is :" +p_name.decode('utf8') )
# #                 print(sbl.splitNames(p_name.decode('utf8')))
#             for s in sbl.splitNames(p_name) :#候选实体为人物，且mention与该候选实体的正名相同
#                 if mention in s.split("·") or mention == s:
#                     es3.add(mention)
            es3.add(p_name)
                
        if u'电影' in can_obj.get("instanceOf",[]) or u'电视' in can_obj.get("instanceOf",[]):#候选实体为影视作品
            es1 = movie2movie_sim(movie_commented,can_obj)
            
        else:
            for item in can_obj.get("label/zh",[]) + can_obj.get("alias",[]):
#                 if item in movie_commented["actor_list"]:
                if item in get_obj_list(movie_commented):
                    es2.add(item)

        score = len(es1)+8*len(es2)+3*len(es3) 
        title = can_obj.get("label/zh",[""])[0]   
        c_sim[c] = (score,title)

    return c_sim
            
        
    
    
def entity_cooccur(db, mention, mentions, context_mentions,cans, threshold=None):
    """
    """

    c_sim = {}
    mentions = set(mentions)
    context_mentions = set(context_mentions)

    for c in cans:
        print ("Can ID:"+c)
        es = db.get_prop_entities(c)
        print ("    Entities in graph:")
        print ("    "+",".join(es))
        if not es or len(es) == 0:
            c_sim[c] = 0.0
        else:
            print ("    common: "+",".join(set(context_mentions)&set(es)))
            c_sim[c] = len(set(context_mentions)&set(es))

    for k,v in c_sim.items():
        print (k+" "+str(v))
        #c_sim[k] = v*1.0/len(mentions)
        c_sim[k] = v*1.0/len(context_mentions)

    #c_sim = normalize(c_sim)

    if threshold:
        for k,v in list(c_sim.items()):
            if v < threshold:
                c_sim.pop(k)


    return c_sim

class Disambiguation():

    def __init__(self, func=None, args={}):

        if not func:
            raise ValueError("Not add strategy")
        self.func = func
        self.args = args

    def get_best(self):
        import operator
        c_sim = self.func(**self.args)
        if len(c_sim) == 0:
            return {}
        best = max(c_sim.items(), key=operator.itemgetter(1))
        return [best]

    def get_sorted_cans(self, num=0):
        """
        Returns:
            return all candidate with their similarity
        """
        if model.global_var.STATISTIC_FLAG:
            current_time = time.time()
        c_sim = self.func(**self.args)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.DISAMBIGUATION_TIME += (time.time() - current_time)
            current_time = time.time()
        best = sorted(c_sim.items(), key=lambda x:x[1][0], reverse=True)
        if model.global_var.STATISTIC_FLAG:
            model.global_var.SORT_TIME += (time.time() - current_time)
        if num:
            return best[:num]
        else:
            return best


class Distance():

    @staticmethod
    def cosine_distance(t1, t2):
        """
        Return the cosine distance between two strings
        """

        def cosine(u, v):
            """
            Returns the cosine of the angle between vectors v and u. This is equal to u.v / |u||v|.
            """
            import numpy
            import math
            return numpy.dot(u, v) / (math.sqrt(numpy.dot(u, u)) * math.sqrt(numpy.dot(v, v)))

        tp = TextProcesser()
        c1 = dict(tp.get_count(t1))
        c2 = dict(tp.get_count(t2))
        keys = c1.keys() + c2.keys()
        word_set = set(keys)
        words = list(word_set)
        v1 = [c1.get(w,0) for w in words]
        v2 = [c2.get(w,0) for w in words]
        return cosine(v1, v2)

    @staticmethod
    def levenshtein(first, second):
        """
        Edit Distance
        """
        if len(first) > len(second):
            first,second = second,first
        if len(first) == 0:
            return len(second)
        if len(second) == 0:
            return len(first)
        first_length = len(first) + 1
        second_length = len(second) + 1
        distance_matrix = [range(second_length) for x in range(first_length)]
        #print distance_matrix 
        for i in range(1,first_length):
            for j in range(1,second_length):
                deletion = distance_matrix[i-1][j] + 1
                insertion = distance_matrix[i][j-1] + 1
                substitution = distance_matrix[i-1][j-1]
                if first[i-1] != second[j-1]:
                    substitution += 1
                distance_matrix[i][j] = min(insertion,deletion,substitution)
        return distance_matrix[first_length-1][second_length-1]


class TextProcesser():

    def __init__(self):
        pass

    def get_tokens(self, t):
        lowers = t.lower()
        #remove the punctuation using the character deletion step of translate
        #no_punctuation = lowers.translate(None, string.punctuation)
        no_punctuation = lowers.translate(string.punctuation)
        tokens = nltk.word_tokenize(no_punctuation)
        from nltk.corpus import stopwords
        tokens = [w for w in tokens if not w in stopwords.words('english')]
        return tokens

    def stem_tokens(self, tokens, stemmer):
        stemmed = []
        for item in tokens:
            stemmed.append(stemmer.stem(item))
        return stemmed

    def get_count(self, t):
        return Counter(self.get_tokens(t)).most_common()

if __name__== '__main__':
#     getNamesFromMention() 
    s = u"韩梓轩 zixuan han"

    sbl = SplitByLanguage()
    print(sbl.splitNames(s))


