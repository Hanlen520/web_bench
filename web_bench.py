# coding=utf8

import threading 
import time
import httplib
import argparse
import random

HOST = "127.0.0.1"
PORT = 80
URI = "/?test="
TOTAL = 0
SUCC = 0
FAIL = 0
EXCEPT = 0
MAXTIME = 0
MINTIME = 100
GT3 = 0
LT3 = 0
TOTALTIME = 0

def parse_args():
    parser = argparse.ArgumentParser(description="Web performace test")
    parser.add_argument('host', type=str, help="The target server name")
    parser.add_argument('-p', '--port', type=int, default=80, help="The target port")
    parser.add_argument('-c', '--concurrency', type=int, default=10, help="Number of multiple requests to make at a time")
    parser.add_argument('-H', '--head', type=str, help="Set request head")
    args = parser.parse_args()
    return args

class RequestThread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.test_count = 0

    def run(self):
        self.test_performace()

    def test_performace(self):
        global TOTAL
        global SUCC
        global FAIL
        global EXCEPT
        global GT3
        global LT3
        global TOTALTIME
        try:
            st = time.time()
            conn = httplib.HTTPConnection(HOST, PORT, False)
            uri = URI + str(random.randint(0, 100000))
            conn.request('GET', uri)
            res = conn.getresponse()
            time_span = time.time() - st
            if res.status == 200:
                TOTAL += 1
                SUCC += 1
                TOTALTIME += time_span
            else:
                TOTAL += 1
                FAIL += 1
            self.maxtime(time_span)
            self.mintime(time_span)
            if time_span > 3:
                GT3 += 1
            else:
                LT3 += 1
        except Exception as e:
            TOTAL += 1
            EXCEPT += 1
        conn.close()

    def maxtime(self, ts):
        global MAXTIME
        if ts>MAXTIME:
            MAXTIME = ts

    def mintime(self, ts):
        global MINTIME
        if  ts<MINTIME:
            MINTIME = ts


if __name__=='__main__':
    args = parse_args()
    HOST = args.host
    thread_count = args.concurrency
    PORT = args.port
    HEAD = args.head
    print "==============test start=============="
    print "server_name: ", HOST
    print "server_port: ", PORT
    print "concurrency: ", thread_count
    start_time = time.time()
    for i in xrange(thread_count):
        t = RequestThread("thread" + str(i+1))
        t.start()

    t = 0
    while TOTAL < thread_count and t < 60:
        t += 1
        time.sleep(1)

    print "=============test end================="
    print '\n'
    print "thread_count:", thread_count
    print "total:%d, succ:%d, fail:%d, except:%d" % (TOTAL, SUCC, FAIL, EXCEPT)
    print 'response maxtime:', MAXTIME
    print 'response mintime:', MINTIME
    print 'great than 3 seconds:%d, percent:%0.2f' % (GT3, float(GT3)/TOTAL)
    print 'less than 3 seconds:%d, percent:%0.2f' % (LT3, float(LT3)/TOTAL)
    print 'average time: %0.2f' % (float(TOTALTIME)/SUCC)

