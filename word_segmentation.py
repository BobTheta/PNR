#-*-coding:utf-8-*-
'''
Created on 2014-12-5

@author: 张江涛
'''
import sys
import jieba
import time
import jieba.posseg as pseg
def word_segmentation(s):
    """
    Returns:
    seg_index: list of tuple, tuple(seg, place of this seg in s)
    """
    jieba.load_userdict('./data/usr.dict')
    seg_list = jieba.cut(s, cut_all=False)
#     result = pseg.cut(s)
#     for seg in result:
#         print(seg.word + '/' + seg.flag)

    seg_index = []
    last = 0
    print(seg_list)
    for seg in seg_list:
        seg = seg.strip("/")
        #print re.split('(《》)', seg)[0]
        begin = s.index(seg, last)
        last = begin + len(seg)
        seg_index.append((seg, begin))
        if sys.version[0] == '2':
            print ('(%s,%d)'%(seg,begin)),
#         elif sys.version[0] == '3':
#             print('(%s,%d)'%(seg,begin),end ="")
    print('\n')
    return seg_index
if __name__=="__main__":

    s = u"看过《银河护卫队》的观众，都记住了这个叫星爵(Star-Lord)的逗比。而他的扮演者，是漫威家族又一位Chris——Chris Pratt克里斯·帕拉特(前有雷神扮演者：克里斯·海姆斯沃斯Chris Hemsworth，后有美国队长扮演者：克里斯·埃文斯Chris Evans)。 然而，作为喜剧咖的普拉特，并非像两位克里斯前辈一样生来C罩杯、6块腹肌+人鱼线。   你看到的星爵是这样的…… 你可曾知道，出演星爵之前的帕拉特是这样的？ 电影《通缉令》中，他被詹一美(詹姆斯·麦卡沃伊)轰了一键盘 电影《她》中，他是没有腰的男子 这些角色，你可能都没记住。 半红不紫多年后，一场试镜，改变了帕拉特的命运。为了塑造好星爵这个角色，他每天在健身房挥汗如雨4个小时，坚持了半年之后，成功减肥51公斤！ 逆袭成功之后，集喜感与帅气于一身的帕拉特赢得了影迷们的喜爱。 然而，招致女粉丝们心碎的是，他拍写真也不离手的婚戒，他出席首映礼必带的女人 这个人，无论是在他胖的时候，还是他瘦的时候，爆红的时候，还是低迷的时候，英俊的时候，还是傻缺的时候，都没有改变过对他的爱。她就是他的妻子，也是好莱坞明星安娜·法瑞丝。 2007年，两人在电影《今晚带我回家》的片场相识。“我对他一见钟情！”法瑞丝坦言。后来帕拉特接受采访时说：“遇到她不久后，我就想把她娶回家！” 2009年7月，两人在巴厘岛喜结连理。蜜月过后参加酒会，依然黏在一起停不下来。   “你，就是我眼中最美的风景。”   你，就是我握住的最好的幸福。   时不时，一家“五口”出去散散步。   红了，或者没红，依然过我们的小日子！   也许，这真是一个看脸的时代，但爱情不应该是。"
    print(len(s))
#     s = s.replace(' ','_')
#     movieel = MovieEL(s,trie,m_e,stop_words)
    begin = time.time()
    slist = word_segmentation(s)
    print('the cut time is : %.4f'%(time.time()-begin))
#     print(slist)
