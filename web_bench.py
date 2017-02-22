#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading 
import time
import httplib
import argparse
import random

HOST = "127.0.0.1"
PORT = 80
URI = "/?test="
HEAD = {}
REQUESTS = 0
COMPLETED_REQUESTS = 0
THREAD_COUNT = 0
PER_REQUESTS = 0
PRINT_REQUESTS = 0
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
    parser.add_argument('-n', '--requests', type=int, default=10, help="Number of request to perform")
    parser.add_argument('-H', '--head', type=str, help="Set request headers and use '||' to separate diff")
    args = parser.parse_args()
    return args

def handle_head(head_str):
    head_dict = {}
    if head_str and '&&' in head_str:
        for hs in head_str.split('&&'):
            head_dict[str(hs.split(':')[0]).replace(' ', '')] = str(hs.split(':')[1])
    elif head_str:
        head_dict[str(head_str.split(':')[0]).replace(' ', '')] = str(head_str.split(':')[1])
    return head_dict

def print_runinfo():
    global THREAD_COUNT
    global COMPLETED_REQUESTS
    global REQUESTS
    global PRINT_REQUESTS
    if COMPLETED_REQUESTS % PRINT_REQUESTS == 0:
        print "Completed %s requests" % COMPLETED_REQUESTS
    if COMPLETED_REQUESTS == REQUESTS:
        print "Finished %s requests" % REQUESTS

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
        global COMPLETED_REQUESTS
        for i in range(PER_REQUESTS):
            try:
                st = time.time()
                conn = httplib.HTTPConnection(HOST, PORT, False)
                uri = URI + str(random.randint(0, 100000))
                conn.request('GET', uri, headers=HEAD)
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
            COMPLETED_REQUESTS += 1
            print_runinfo()
            time.sleep(0.1)

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
    THREAD_COUNT = args.concurrency
    PORT = args.port
    HEAD = handle_head(args.head)
    REQUESTS = args.requests if args.requests > THREAD_COUNT else THREAD_COUNT
    PER_REQUESTS = REQUESTS/THREAD_COUNT
    PRINT_REQUESTS = REQUESTS / 10
    print "==============test start=============="
    print "server_name: ", HOST
    print "server_port: ", PORT
    print "concurrency: ", THREAD_COUNT
    start_time = time.time()
    for i in xrange(THREAD_COUNT):
        t = RequestThread("thread" + str(i+1))
        t.setDaemon(True)
        t.start()

    try:
        while TOTAL < REQUESTS:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print "=============test end================="
    print "thread_count:", THREAD_COUNT
    print "total:%d, succ:%d, fail:%d, except:%d" % (TOTAL, SUCC, FAIL, EXCEPT)
    print 'response maxtime:', MAXTIME
    print 'response mintime:', MINTIME
    print 'great than 3 seconds:%d, percent:%0.2f' % (GT3, float(GT3)/(TOTAL if TOTAL else 1))
    print 'less than 3 seconds:%d, percent:%0.2f' % (LT3, float(LT3)/(TOTAL if TOTAL else 1))
    print 'average time: %0.2f' % (float(TOTALTIME)/(SUCC if SUCC else 1))

