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
Dict = Manager().dict()
Dict['TOTAL'] = 0
Dict['SUCC'] = 0
Dict['FAIL'] = 0
Dict['EXCEPT'] = 0
Dict['GT3'] = 0
Dict['LT3'] = 0
Dict['COMPLETED_REQUESTS'] = 0
Dict['MAXTIME'] = 0
Dict['MINTIME'] = 100
Dict['EXCEPT_REASON'] = ''
Dict['FAIL_REASON'] = ''
Dict['TOTALTIME'] = 0


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
        # self.p_lock = p_lock

    def run(self):
        self.test_performace()

    def test_performace(self):
        global Dict
        global URIS
        for _ in xrange(self.thread_requests):
            try:
                st = time.time()
                conn = httplib.HTTPConnection(handle_host(HOST), PORT, False)
                uri = random.choice(URIS) + str(random.randint(0, 10000))
                conn.request('GET', uri, headers=HEAD)
                res = conn.getresponse()
                time_span = time.time() - st
                # self.p_lock.acquire()
                # self.t_lock.acquire()
                if res.status == 200:
                    Dict['SUCC'] += 1
                    Dict['TOTALTIME'] += time_span
                else:
                    if not Dict['FAIL_REASON']:
                        Dict['FAIL_REASON'] = res.status
                    Dict['FAIL'] += 1
                self.maxtime(time_span)
                self.mintime(time_span)
                if time_span > 3:
                    Dict['GT3'] += 1
                else:
                    Dict['LT3'] += 1
            except Exception as e:
                if not Dict['EXCEPT_REASON']:
                    Dict['EXCEPT_REASON'] = str(e)
                Dict['EXCEPT'] += 1
            # mu.acquire()
            Dict['TOTAL'] += 1
            Dict['COMPLETED_REQUESTS'] += 1
            # self.t_lock.release()
            # self.p_lock.release()
            # mu.release()
            if (REQUESTS <= 1000 and not Dict['COMPLETED_REQUESTS'] % 100) \
                    or (REQUESTS > 1000 and not Dict['COMPLETED_REQUESTS'] % 1000):
                print "Completed %s requests" % Dict['COMPLETED_REQUESTS']
            if Dict['COMPLETED_REQUESTS'] == REQUESTS:
                print "Finished %s requests" % REQUESTS
            conn.close()
            # print 'TOTAL: ', Dict['TOTAL']
            time.sleep(0.01)

    def maxtime(self, ts):
        global Dict
        if ts > Dict['MAXTIME']:
            Dict['MAXTIME'] = ts

    def mintime(self, ts):
        global Dict
        if ts < Dict['MINTIME']:
            Dict['MINTIME'] = ts


# 创建线程
def create_threads(n, tr, p_lock):
    ts = []
    t_lock = threading.Lock()
    for i in xrange(n):
        t = RequestThread(tr, ("thread" + str(i+1)), t_lock)
        t.start()
        ts.append(ts)
    for t in range(ts):
        ts.join()


# 创建同cpu核心数相同的进程数
def create_processes():
    global THREAD_COUNT
    global REQUESTS
    p_lock = Manager().Lock()
    thread_requests = REQUESTS / THREAD_COUNT
    pool = Pool(processes=cpu_count())
    per_cpu_threads = THREAD_COUNT / cpu_count()
    _per_cpu_threads = per_cpu_threads + (THREAD_COUNT % cpu_count())
    for _ in range(cpu_count()-1):
        pool.apply_async(create_threads, (per_cpu_threads, thread_requests, p_lock))
    pool.apply_async(create_threads, (_per_cpu_threads, thread_requests, p_lock))


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
        while Dict['TOTAL'] < REQUESTS:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    end_time = time.time()
    print "=============test end================="
    print "thread_count:", THREAD_COUNT
    print "total:%d, succ:%d, fail:%d, except:%d" % (Dict['TOTAL'], Dict['SUCC'], Dict['FAIL'], Dict['EXCEPT'])
    print "except reason: ", Dict['EXCEPT_REASON']
    print "fail code: ", Dict['FAIL_REASON']
    print 'response maxtime:', Dict['MAXTIME']
    print 'response mintime:', Dict['MINTIME']
    print 'great than 3 seconds:%d, percent:%0.2f' % (Dict['GT3'], float(Dict['GT3'])/(Dict['TOTAL'] if Dict['TOTAL'] else 1))
    print 'less than 3 seconds:%d, percent:%0.2f' % (Dict['LT3'], float(Dict['LT3'])/(Dict['TOTAL'] if Dict['TOTAL'] else 1))
    print 'average time: %0.2f' % (float(Dict['TOTALTIME'])/(Dict['SUCC'] if Dict['SUCC'] else 1))
    print "real time: %0.2f" % (end_time - start_time)
