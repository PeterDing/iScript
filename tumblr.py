#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
import re
import json
import requests
import argparse
import random
import multiprocessing
import time
import subprocess

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
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

class tumblr(object):
    def __init__(self, burl):
        self.infos = {'host': re.search(r'http(s|)://(.+?)($|/)', burl).group(2)}
        self.infos['dir_'] = os.path.join(os.getcwd(), self.infos['host'])
        self.processes = int(args.processes)

        if not os.path.exists(self.infos['dir_']):
            os.makedirs(self.infos['dir_'])
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            self.offset = 0
            print s % (1, 92, '\n   ## begin'), 'offset = %s' % self.offset
        else:
            self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            if os.path.exists(self.json_path):
                self.offset = json.loads(open(self.json_path).read())['offset'] - 20
                print s % (1, 92, '\n   ## begin'), 'offset = %s' % self.offset
            else:
                self.offset = 0

    def save_json(self):
        with open(self.json_path, 'w') as g:
            g.write(json.dumps({'offset': self.offset}, indent=4, sort_keys=True))

    def get_infos(self, postid=None):
        self.infos['photos'] = []
        self.url = 'http://api.tumblr.com/v2/blog/%s/posts/photo' % self.infos['host']
        params = {
            "offset": self.offset if not postid else "",
            "limit": 20 if not postid else "",
            "type": "photo",
            "filter": "text",
            "tag": args.tag,
            #"id": postid if postid else "",
            "api_key": api_key
        }

        r = None
        while True:
            try:
                r = ss.get(self.url, params=params, timeout=10)
                break
            except Exception as e:
                print s % (1, 91, '  !! Error, ss.get'), e
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

    def download(self):
        def run(i):
            #if not os.path.exists(i['filepath']):
            num = random.randint(0, 7) % 7
            col = s % (1, num + 90, i['filepath'])
            print '\n  ++ 正在下载: %s' % col

            cmd = 'wget -c -T 4 -q -O "%s.tmp" ' \
                '--header "Referer: http://www.tumblr.com" ' \
                '--user-agent "%s" "%s"' \
                % (i['filepath'], headers['User-Agent'], i['durl'])

            status = os.system(cmd)
            if status != 0:     # other http-errors, such as 302.
                wget_exit_status_info = wget_es[status]
                print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> '\
                    '\x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
                    % (status, wget_exit_status_info))
                print s % (1, 91, '  ===> '), cmd
                sys.exit(1)
            else:
                os.rename('%s.tmp' % i['filepath'], i['filepath'])

        l = [self.infos['photos'][i:i+self.processes] \
            for i in range(len(self.infos['photos']))[::self.processes]]
        for yy in l:
            ppool = []
            for ii in yy:
                if not os.path.exists(ii['filepath']):
                    p = multiprocessing.Process(target=run, args=(ii,))
                    p.start()
                    print p
                    ppool.append(p)

            for p in ppool: p.join()

    def do(self):
        if args.check:
            t = subprocess.check_output('ls "%s" | grep ".tmp"' \
                % self.infos['dir_'], shell=True)
            t = re.findall(r'\d\d\d+', t)
            ltmp = list(set(t))
            for postid in ltmp:
                self.get_infos(postid)
                self.download()
        else:
            while True:
                self.get_infos()
                self.offset += 20
                self.save_json()
                self.download()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='download from tumblr.com')
    p.add_argument('url', help='url')
    p.add_argument('-p', '--processes', action='store', default=5, \
        help='指定多进程数,默认为5个,最多为20个 eg: -p 20')
    p.add_argument('-c', '--check', action='store_true', \
        help='尝试修复未下载成功的图片')
    p.add_argument('-t', '--tag', action='store', \
                   default=None, type=str, help='下载特定tag的图片, eg: -t beautiful')
    args = p.parse_args()
    url = args.url
    x = tumblr(url)
    x.do()
