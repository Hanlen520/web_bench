#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading 
from multiprocessing import cpu_count,  Pool, Lock, Manager
import time
import httplib
import argparse
import random

HOST = "127.0.0.1"
PORT = 80
URIS = ["/?test=", "/?test1=", "/?test2=", "/?test3=", "/?test4="]
HEAD = {}
REQUESTS = 0
THREAD_COUNT = 0
mu = Lock()
TOTAL = 0
SUCC = 0
FAIL = 0
EXCEPT = 0
GT3 = 0
LT3 = 0
COMPLETED_REQUESTS = 0
MAXTIME = 0
MINTIME = 100
EXCEPT_REASON = ''
FAIL_CODE = ''
TOTALTIME = 0


def parse_args():
    parser = argparse.ArgumentParser(description="Web performace test")
    parser.add_argument('host', type=str, help="The target server name")
    parser.add_argument('-p', '--port', type=int, default=80, help="The target port")
    parser.add_argument('-c', '--concurrency', type=int, default=10, help="Number of multiple requests to make at a time")
    parser.add_argument('-n', '--requests', type=int, default=10, help="Number of request to perform")
    parser.add_argument('-H', '--head', type=str, help="Set request headers and use '&&' to separate different header")
    args = parser.parse_args()
    return args


def handle_host(host_str):
    return host_str.replace("http://", '').replace("https://", '').strip('/')


def handle_head(head_str):
    head_dict = {}
    if head_str and '&&' in head_str:
        for hs in head_str.split('&&'):
            head_dict[str(hs.split(':')[0]).replace(' ', '')] = str(hs.split(':')[1])
    elif head_str:
        head_dict[str(head_str.split(':')[0]).replace(' ', '')] = str(head_str.split(':')[1])
    return head_dict


class RequestThread(threading.Thread):
    def __init__(self, thread_requests, thread_name, t_lock):
        threading.Thread.__init__(self, name=thread_name)
        self.thread_requests = thread_requests
        self.t_lock = t_lock

    def run(self):
        self.test_performace()

    def test_performace(self):
        global TOTAL
        global SUCC
        global FAIL
        global EXCEPT
        global FAIL_CODE
        global EXCEPT_REASON
        global GT3
        global LT3
        global TOTALTIME
        global COMPLETED_REQUESTS
        global URIS
        for _ in xrange(self.thread_requests):
            try:
                st = time.time()
                conn = httplib.HTTPConnection(handle_host(HOST), PORT, False)
                uri = random.choice(URIS) + str(random.randint(0, 10000))
                conn.request('GET', uri, headers=HEAD)
                res = conn.getresponse()
                time_span = time.time() - st
                # self.t_lock.acquire()
                if res.status == 200:
                    SUCC += 1
                    TOTALTIME += time_span
                else:
                    if not FAIL_CODE:
                        FAIL_CODE = res.status
                    FAIL += 1
                self.maxtime(time_span)
                self.mintime(time_span)
                if time_span > 3:
                    GT3 += 1
                else:
                    LT3 += 1
            except Exception as e:
                if not EXCEPT_REASON:
                    EXCEPT_REASON = str(e)
                EXCEPT += 1
            # mu.acquire()
            TOTAL += 1
            COMPLETED_REQUESTS += 1
            # self.t_lock.release()
            conn.close()
            time.sleep(0.01)

    def maxtime(self, ts):
        global MAXTIME
        if ts > MAXTIME:
            MAXTIME = ts

    def mintime(self, ts):
        global MINTIME
        if ts < MINTIME:
            MINTIME = ts


# 创建线程
def create_threads(n, tr):
    ts = []
    t_lock = threading.Lock()
    for i in xrange(n):
        t = RequestThread(tr, ("thread" + str(i+1)), t_lock)
        t.start()
        ts.append(ts)
    for t in range(ts):
        ts.join()
    data = {'total': TOTAL,
            'succ': SUCC,
            'fail': FAIL,
            'except': EXCEPT,
            'fail_code': FAIL_CODE,
            'except_reason': EXCEPT_REASON,
            'total_time': TOTALTIME,
            'gt3': GT3,
            'lt3': LT3,
            'completed_requests': COMPLETED_REQUESTS,
            'maxtime': MAXTIME,
            'mintime': MINTIME}
    return data


# 创建同cpu核心数相同的进程数
def create_processes():
    global THREAD_COUNT
    global REQUESTS
    global TOTAL
    global SUCC
    global FAIL
    global EXCEPT
    global GT3
    global LT3
    global TOTALTIME
    global EXCEPT_REASON
    global FAIL_CODE
    global COMPLETED_REQUESTS
    thread_requests = REQUESTS / THREAD_COUNT
    pool = Pool(processes=cpu_count())
    per_cpu_threads = THREAD_COUNT / cpu_count()
    _per_cpu_threads = per_cpu_threads + (THREAD_COUNT % cpu_count())
    process_list = []
    for _ in range(cpu_count()-1):
        res = pool.apply_async(create_threads, (per_cpu_threads, thread_requests))
        process_list.append(res)
    res = pool.apply_async(create_threads, (_per_cpu_threads, thread_requests))
    process_list.append(res)
    pool.close()
    pool.join()
    # print process_list[0].get()
    for p in process_list:
        TOTAL += p.get()['total']
        SUCC += p.get()['succ']
        FAIL += p.get()['fail']
        EXCEPT += p.get()['except']
        GT3 += p.get()['gt3']
        LT3 += p.get()['lt3']
        TOTALTIME += p.get()['total_time']
        EXCEPT_REASON = p.get()['except_reason']
        FAIL_CODE = p.get()['fail_code']
        COMPLETED_REQUESTS += p.get()['completed_requests']
        if MAXTIME < p.get()['maxtime']:
            MAXTIME = p.get()['maxtime']
        if MINTIME > p.get()['mintime']:
            MINTIME = p.get()['mintime']

if __name__ == '__main__':
    args = parse_args()
    HOST = args.host
    THREAD_COUNT = args.concurrency
    PORT = args.port
    HEAD = handle_head(args.head)
    REQUESTS = args.requests if args.requests > THREAD_COUNT else THREAD_COUNT
    print "==============test start=============="
    print "server_name: ", HOST
    print "server_port: ", PORT
    print "concurrency: ", THREAD_COUNT
    print "requests: ", REQUESTS
    start_time = time.time()
    create_processes()
    try:
        while TOTAL < REQUESTS:
            if (REQUESTS <= 1000 and not COMPLETED_REQUESTS % 100) \
                    or (REQUESTS > 1000 and not COMPLETED_REQUESTS % 1000):
                print "Completed %s requests" % COMPLETED_REQUESTS
            if COMPLETED_REQUESTS == REQUESTS:
                print "Finished %s requests" % REQUESTS
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    end_time = time.time()
    print "=============test end================="
    print "thread_count:", THREAD_COUNT
    print "total:%d, succ:%d, fail:%d, except:%d" % (TOTAL, SUCC, FAIL, EXCEPT)
    print "except reason: ", EXCEPT_REASON
    print "fail code: ", FAIL_CODE
    print 'response maxtime:', MAXTIME
    print 'response mintime:', MINTIME
    print 'great than 3 seconds:%d, percent:%0.2f' % (GT3, (float(GT3)/(TOTAL if TOTAL else 1)))
    print 'less than 3 seconds:%d, percent:%0.2f' % (LT3, (float(LT3)/(TOTAL if TOTAL else 1)))
    print 'average time: %0.2f' % (float(TOTALTIME)/(SUCC if SUCC else 1))
    print "real time: %0.2f" % (end_time - start_time)
