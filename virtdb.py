#!/usr/bin/env python
#-*-coding=utf-8-*-
import os
import re
import sys
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding('utf8')
if not re.match('linux',sys.platform):
    from jpype import *
import urllib 
if sys.version[0] == '3':
    import urllib.request as urllib2
    from urllib.parse import urlencode    
else: 
    import urllib2
    from urllib import urlencode 
import json
import pyodbc
import time
from utils import *
import model.global_var

class VirtDB(object):
    """
    """

    def __init__(self, uid, pwd, graph, dsn=None,
                 driver=None, host=None, port=None):
        self.HOST = host
        self.PORT = port
        self.DSN = dsn
        self.DRIVER = driver
        self.UID = uid
        self.PWD = pwd
        self.GRAPH = graph
        self.charset = "UTF-8"

    def connect(self):
        raise NotImplementedError("Subclasses should implement this!")

    def query(self, sq):
        raise NotImplementedError("Subclasses should implement this!")

    def close(self):
        raise NotImplementedError("Subclasses should implement this!")

class HttpDB(VirtDB):
    def __init__(self, url, uid, pwd, graph, host, port, prefix, dsn, driver):
        VirtDB.__init__(self, uid, pwd, graph, dsn, driver, host, port)

        self.url = url
        self.prefix = model.global_var.PREFIX

    def connect(self):
        pass

    #def query(self, t, id_):
    def query2(self, sq):
        """
        request args need:
        id_
        type
        prefix
        graph
        host
        port
        uid
        pwd
        """

        param = {
                # "id_":id_,
                # "type":t,
                "sq": sq,
                "prefix": self.prefix,
                "graph": self.GRAPH,
                "uid": self.UID,
                "pwd": self.PWD,
                "host": self.HOST,
                "port": self.PORT,
                "dsn": self.DSN,
                "driver": self.DRIVER
                }
#         print(urlencode(param))
#         print(urlencode(param).encode('utf-8'))
#         print(urllib2.Request(self.url, urlencode(param).encode('utf-8')).full_url)
        f = urllib2.urlopen(urllib2.Request(self.url, urlencode(param).encode('utf-8')))
        resp = f.read()
        return json.loads(resp.decode('utf-8'))

    def close(self):
        pass


class OdbcVirtDB(VirtDB):
    """
    """

    def __init__(self, uid, pwd, graph, dsn=None, host=None, port=None, driver=None):
        VirtDB.__init__(self, uid, pwd, graph, dsn, driver, host, port)

        self.db = None
        self.driver = driver

    def connect(self):
        try:
            if self.DSN:
                self.db = pyodbc.connect("DSN=%s;UID=%s;PWD=%s;charset=%s"%(self.DSN, self.UID, self.PWD, self.charset) )
        except Exception as e:
            print (e)

            if self.driver:
                self.db = pyodbc.connect('DRIVER={%s};HOST=%s:%s;UID=%s;PWD=%s;charset=UTF-8'
                                         %(self.DRIVER, self.HOST, str(self.PORT), self.UID, self.PWD))
            else:
                raise ValueError("Need DSN or DRIVER&&HOST&&PORT")

    def query(self, sq):
        if not self.db:
            self.connect()

        sq = "sparql " + sq
        cursor = self.db.cursor()
#        print ("Query:%s"%sq)
        try:
            results = [(r[0][0], r[1][0]) for r in cursor.execute(sq).fetchall()]
            print(cursor.execute(sq).fetchall())
            #if results and len(results) > 0 and type(results[0]) == tuple:
            #    results = [r[0] for r in results]
        except TypeError:
            return []
        finally:
            cursor.close()
        return results

    def query2(self, sq):
        if model.global_var.STATISTIC_FLAG:
            model.global_var.ACCESS_DATABASE_TIMES +=1
            p = re.compile(r'/[^/]*>')
            entity_id = '<' +p.findall(sq)[0][1:-1] + '>'
            model.global_var.ACCESS_TIME_DICT[entity_id] =model.global_var.ACCESS_TIME_DICT.get(entity_id,0) +1
        if not self.db:
            self.connect()

        sq = "sparql " + sq
        cursor = self.db.cursor()
        try:
            results = []
            for r in cursor.execute(sq).fetchall():
                y = []
                for x in r:
                	if type(x) == type(""):y.append(x) 
                	else: y.append(x[0])
                results.append(tuple(y))
        except TypeError:
            return []
        finally:
            cursor.close()
            
#             Constant.model.global_var.ACCESS_DATABASE_TIMES +=1
#             interval = time.time() - Constant.interval
#             Constant.interval = time.time()
#             print(sq)
#             print("the times of accessing the virtuoso database is :%d"%Constant.model.global_var.ACCESS_DATABASE_TIMES)
#             print("the interval time is :%.4f"%interval)
        return results

    def close(self):
        self.db.close()


class JenaVirtDB(VirtDB):
    """
    """

    def __init__(self, uid, pwd, graph, host=None, port=None):
        if not host:
            raise ValueError("Need Value:HOST")
        if not port:
            raise ValueError("Need Value:PORT")
        VirtDB.__init__(self, uid, pwd, graph, host=host, port=port)

        #self.jvmpath = getDefaultJVMPath()
        #startJVM(self.jvmpath, "-ea", "-Djava.ext.dirs={0}".format(os.path.abspath('.')+"/java/"))
        startJVM("C:/Program Files/Java/jre7/bin/server/jvm.dll","-ea","-Djava.ext.dirs={0}".format(os.path.abspath('.')+"/java/"))
        print ("JVM Start")
        VtsDB = JClass('movie.MovieVirt')
        self.db = VtsDB(host, port, uid, pwd, graph)

    def connect(self):
        pass

    def query(self, sq):
        r_list = []
        result = self.db.query(sq)
        for r in result:
            r_list.append((r.getK(), r.getV()))
        return r_list

    def close(self):
        shutdownJVM()

if __name__ == "__main__":
    pass

