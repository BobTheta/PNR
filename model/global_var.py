#!/usr/bin/env python2.7
#encoding=utf-8

DEBUG = 0

CACHE_FLAG = 1
WHOLE_INFO_RESULT = {}
LABEL_DICT = {}

STATISTIC_FLAG =1
CUT_WORDS_TIME1 = 0
CUT_WORDS_TIME2 = 0
APPEND_MENTIONS = 0
ACCESS_DATABASE_TIMES =0
ACCESS_DATABASE_TIME = 0
RANKING_TIME = 0
GET_ENTITY =0
GET_OBJ_PROPERTY = 0
CALCULATE_SIM = 0
ACCESS_TIME_DICT = {}

ANNOTATION_FLAG = 0
COMMENT_ANNOTATION = ''

PREFIX = 'http://keg.tsinghua.edu.cn/movie/'
GRAPH = 'keg-movie2'
SERVER_URL = 'http://10.1.1.23:5678/query'
CUT_URL = u'http://localhost:8000/seg?'

PUNCT = set(u''':!),.:;?]}¢'"、。〉》」』】〕〗〞︰︱︳﹐､﹒
        ﹔﹕﹖﹗﹚﹜﹞！），．：；？｜｝︴︶︸︺︼︾﹀﹂﹄﹏､～￠
        々‖•·ˇˉ―--′’”([{£¥'"‵〈《「『【〔〖（［｛￡￥〝︵︷︹︻
        ︽︿﹁﹃﹙﹛﹝（｛“‘-—_…''')

STOP_WORDS = []

MENTION_ENTITY = {}

