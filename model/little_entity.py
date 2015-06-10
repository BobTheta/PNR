#!/usr/bin/env/python2.7
#-*-coding:UTF-8-*-

class LittleEntity():

    def __init__(self, uri, title,confidence=0.0, sim=None ):
        self.uri        = uri
        self.title    = title
        self.sim      = sim
        self.confidence = confidence
        self.alias    = None
        self.abstract = None
        self.image    = None
        

    def __str__(self):
        return "title:"+str(self.title)+"\n"+"uri:"+str(self.uri)+"\nimage:"+str(self.image)+"\nabstract:"+str(self.abstract)+"\nsimilarity:"+str(self.sim)+"\n"




