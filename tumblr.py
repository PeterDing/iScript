#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
import re
import json
import requests
import argparse
import random
import subprocess
import time

api_key = 'fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4'

############################################################
# wget exit status
wget_es = {
    0: "No problems occurred.",
    2: "User interference.",
    1<<8: "Generic error code.",
    2<<8: "Parse error - for instance, when parsing command-line " \
        "optio.wgetrc or .netrc...",
    3<<8: "File I/O error.",
    4<<8: "Network failure.",
    5<<8: "SSL verification failure.",
    6<<8: "Username/password authentication failure.",
    7<<8: "Protocol errors.",
    8<<8: "Server issued an error response."
}
############################################################

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"https://api.tumblr.com/console//calls/blog/posts",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 " \
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

def check_queue(queue, cb):
    for f in queue:
        st = f[0].poll()
        if st is not None:
            if st == 0: cb(f[1])
            queue.remove(f)
    return queue

def sleep(size, num):
    t = float(size) / num
    time.sleep(t)

def async(tasks, queue, run=None, cb=None, num=10):
    queue = check_queue(queue, cb)
    sleep(len(queue), num)
    nsize = num - len(queue)
    for i in xrange(nsize):
        try:
            task = tasks.pop(0)
        except IndexError:
            break
        f = run(task)
        if f: queue.append(f)
    return tasks, queue

class tumblr(object):
    def __init__(self):
        self.queue = []
        self.tasks = []

    def save_json(self):
        with open(self.json_path, 'w') as g:
            g.write(json.dumps(
                {'key': self.key}, indent=4, sort_keys=True))

    def get_site_infos(self, postid=None):
        self.infos['photos'] = []
        self.url = 'http://api.tumblr.com/v2/blog/%s/posts/photo' \
            % self.infos['host']
        params = {
            "offset": self.key if not postid else "",
            "limit": 20 if not postid else "",
            "type": "photo",
            "filter": "text",
            "tag": args.tag,
            "id": postid if postid else "",
            "api_key": api_key
        }

        r = None
        while True:
            try:
                r = ss.get(self.url, params=params)
                break
            except Exception as e:
                print s % (1, 91, '  !! Error at get_infos'), e
                time.sleep(5)
        if r.ok:
            j = r.json()
            if j['response']['posts']:
                for i in j['response']['posts']:
                    index = 1
                    for ii in i['photos']:
                        durl = ii['original_size']['url'].encode('utf8')
                        filepath = os.path.join(self.infos['dir_'], '%s_%s.%s' \
                            % (i['id'], index, durl.split('.')[-1]))
                        filename = os.path.split(filepath)[-1]
                        t = {
                            'filepath': filepath,
                            'durl': durl,
                            'filename': filename
                        }
                        index += 1
                        self.infos['photos'].append(t)
            else:
                print s % (1, 92, '\n   --- job over ---')
                sys.exit(0)
        else:
            print s % (1, 91, '\n   !! Error, get_infos')
            print r.status_code, r.content
            sys.exit(1)

    def get_tag_infos(self):
        self.infos['photos'] = []
        self.url = 'http://api.tumblr.com/v2/tagged'
        params = {
            "limit": 20,
            "type": "photo",
            "tag": self.infos['tag'],
            "before": self.key,
            "api_key": api_key
        }

        r = None
        while True:
            try:
                r = ss.get(self.url, params=params)
                break
            except Exception as e:
                print s % (1, 91, '  !! Error at get_infos'), e
                time.sleep(5)
        if r.ok:
            j = r.json()
            if j['response']:
                for i in j['response']:
                    index = 1
                    if i.get('photos'):
                        for ii in i['photos']:
                            durl = ii['original_size']['url'].encode('utf8')
                            filepath = os.path.join(
                                self.infos['dir_'], '%s_%s.%s' \
                                % (i['id'], index, durl.split('.')[-1]))
                            filename = os.path.split(filepath)[-1]
                            t = {
                                'filepath': filepath,
                                'durl': durl,
                                'filename': filename,
                                'key': i['timestamp']
                            }
                            index += 1
                            self.infos['photos'].append(t)
            else:
                print s % (1, 92, '\n   --- job over ---')
                sys.exit(0)
        else:
            print s % (1, 91, '\n   !! Error, get_infos')
            print r.status_code, r.content
            sys.exit(1)

    def download(self):
        def run(i):
            if os.path.exists(i['filepath']):
                return
            num = random.randint(0, 7) % 7
            col = s % (1, num + 90, i['filepath'])
            print '  ++ download: %s' % col
            cmd = [
                'wget', '-c', '-q',
                '-O', '%s.tmp' % i['filepath'],
                '--user-agent', '"%s"' % headers['User-Agent'],
                '%s' % i['durl']
            ]
            f = subprocess.Popen(cmd)
            return f, i['filepath']

        def callback(filepath):
            os.rename('%s.tmp' % filepath, filepath)

        tasks = self.infos['photos'] + self.tasks
        self.tasks = []
        while True:
            tasks, self.queue = async(
                tasks, self.queue, run=run,
                cb=callback, num=self.processes)
            if len(tasks) <= self.processes:
                self.tasks = tasks
                break

    def download_site(self, url):
        self.infos = {
            'host': re.search(r'http(s|)://(.+?)($|/)', url).group(2)}
        self.infos['dir_'] = os.path.join(os.getcwd(), self.infos['host'])
        self.processes = int(args.processes)

        if not os.path.exists(self.infos['dir_']):
            os.makedirs(self.infos['dir_'])
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            self.key = 0
            print s % (1, 92, '\n   ## begin'), 'key = %s' % self.key
        else:
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            if os.path.exists(self.json_path):
                self.key = json.loads(open(self.json_path).read())['key'] - 20
                print s % (1, 92, '\n   ## begin'), 'key = %s' % self.key
            else:
                self.key = 0

        if args.check:
            t = os.listdir(self.infos['dir_'])
            t = [i[:i.find('_')] for i in t if i.endswith('.tmp')]
            ltmp = list(set(t))
            for postid in ltmp:
                self.get_site_infos(postid)
                self.download()
        else:
            while True:
                self.get_site_infos()
                self.key += 20
                self.save_json()
                self.download()

    def download_tag(self, tag):
        self.infos = {'tag': tag}
        self.infos['dir_'] = os.path.join(
            os.getcwd(), 'tumblr-%s' % self.infos['tag'])
        self.processes = int(args.processes)

        if not os.path.exists(self.infos['dir_']):
            os.makedirs(self.infos['dir_'])
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            self.key = int(time.time())
            print s % (1, 92, '\n   ## begin'), 'key = %s' % self.key
        else:
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            if os.path.exists(self.json_path):
                self.key = json.loads(open(self.json_path).read())['key']
                print s % (1, 92, '\n   ## begin'), 'key = %s' % self.key
            else:
                self.key = int(time.time())

        if args.check:
            t = os.listdir(self.infos['dir_'])
            t = [i[:i.find('_')] for i in t if i.endswith('.tmp')]
            ltmp = list(set(t))
            for postid in ltmp:
                self.get_site_infos(postid)
                self.download()
        else:
            while True:
                self.get_tag_infos()
                self.key = self.infos['photos'][-1]['key']
                self.save_json()
                self.download()

def main(argv):
    p = argparse.ArgumentParser(
        description='download from tumblr.com')
    p.add_argument('xxx', help='xxx')
    p.add_argument('-p', '--processes', action='store', default=10,
        help='指定多进程数,默认为10个,最多为20个 eg: -p 20')
    p.add_argument('-c', '--check', action='store_true',
        help='尝试修复未下载成功的图片')
    p.add_argument('-t', '--tag', action='store',
                   default=None, type=str,
                   help='下载特定tag的图片, eg: -t beautiful')
    global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    if 'http:' in xxx:
        x = tumblr()
        x.download_site(xxx)
    else:
        x = tumblr()
        x.download_tag(xxx)

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
