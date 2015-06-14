#!/usr/bin/env python2
# vim: set fileencoding=utf8

from __future__ import unicode_literals

import os
import sys
import re
import json
from collections import deque
import requests
import urlparse
import argparse
import random
import subprocess
import time
import select

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

def async(tasks, queue, dir_, run=None, cb=None, num=10):
    queue = check_queue(queue, cb)
    sleep(len(queue), num)
    nsize = num - len(queue)
    for i in xrange(nsize):
        try:
            task = tasks.popleft()
        except IndexError:
            break
        f = run(task, dir_)
        if f: queue.append(f)
    #return tasks, queue

class Error(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class TumblrAPI(object):
    def _request(self, base_hostname, target, type, params):
        api_url = '/'.join(['https://api.tumblr.com/v2/blog',
                           base_hostname, target, type])
        params['api_key'] = api_key
        res = ss.get(api_url, params=params)
        if not res:
            raise Error(s % (1, 91, 'api request error.'))

        json_data = res.json()
        if json_data['meta']['msg'].lower() != 'ok':
            raise Error(s % (1, 91, json_data['meta']['msg']))

        return json_data['response']

    def _info(self, base_hostname):
        return self._request(base_hostname, 'info', '', None)

    def _photo(self, base_hostname, offset='', tag='', post_id='', to_items=True):
        def make_items(raw_data):
            items = []
            for i in raw_data['posts']:
                index = 1
                if i.get('photos'):
                    for ii in i['photos']:
                        durl = ii['original_size']['url'].replace('http:', 'https:')
                        filename = os.path.join(
                            '%s_%s.%s' % (i['id'], index, durl.split('.')[-1]))
                        t = {
                            'durl': durl,
                            'filename': filename,
                            'key': i['timestamp'],
                            'subdir': 'photos',
                        }
                        index += 1
                        items.append(t)
            return items

        params = {
            'offset': offset,
            'before': offset if tag else '',
            'tag': tag,
            'id': post_id,
            'limit': 20 if not tag and not post_id else '',
            'filter': 'text'
        }
        raw_data = self._request(base_hostname, 'posts', 'photo', params)
        if to_items:
            return make_items(raw_data)
        else:
            return raw_data

    def _audio(self, base_hostname, offset='', tag='', post_id='', to_items=True):
        def make_items(raw_data):
            items = []
            for i in raw_data['posts']:
                durl = i['audio_url'].replace('http:', 'https:')
                filename = os.path.join(
                    '%s_%s.%s' % (i['id'], i['track_name'], durl.split('.')[-1]))
                t = {
                    'durl': durl,
                    'filename': filename,
                    'timestamp': i['timestamp'] if tag else '',
                    'subdir': 'audios'
                }
                items.append(t)
            return items

        params = {
            'offset': offset,
            'before': offset if tag else '',
            'tag': tag,
            'id': post_id,
            'limit': 20 if not tag and not post_id else '',
            'filter': 'text'
        }
        raw_data = self._request(base_hostname, 'posts', 'audio', params)
        if to_items:
            return make_items(raw_data)
        else:
            return raw_data

    def _video(self, base_hostname, offset='', tag='', post_id='', to_items=True):
        def make_items(raw_data):
            items = []
            for i in raw_data['posts']:
                if not i.get('video_url'):
                    continue
                durl = i['video_url'].replace('http:', 'https:')
                filename = os.path.join(
                    '%s.%s' % (i['id'], durl.split('.')[-1]))
                t = {
                    'durl': durl,
                    'filename': filename,
                    'timestamp': i['timestamp'] if tag else '',
                    'subdir': 'videos'
                }
                items.append(t)
            return items

        params = {
            'offset': offset,
            'before': offset if tag else '',
            'tag': tag,
            'id': post_id,
            'limit': 20 if not tag and not post_id else '',
            'filter': 'text'
        }
        raw_data = self._request(base_hostname, 'posts', 'video', params)
        if to_items:
            return make_items(raw_data)
        else:
            return raw_data

class Tumblr(TumblrAPI):
    def __init__(self, args):
        self.args = args
        self.queue = []
        self.tasks = deque()
        self.offset = self.args.offset
        self.processes = int(self.args.processes)
        if self.args.play:
            self.download = self.play

    def save_json(self):
        with open(self.json_path, 'w') as g:
            g.write(json.dumps(
                {'offset': self.offset}, indent=4, sort_keys=True))

    def init_infos(self, base_hostname, target_type, tag=''):
        self.infos = {'host': base_hostname}
        if not tag:
            self.infos['dir_'] = os.path.join(os.getcwd(), self.infos['host'])

            if not os.path.exists(self.infos['dir_']):
                if not self.args.play:
                    os.makedirs(self.infos['dir_'])
                    self.json_path = os.path.join(self.infos['dir_'], 'json.json')
            else:
                self.json_path = os.path.join(self.infos['dir_'], 'json.json')
                if os.path.exists(self.json_path):
                    self.offset = json.load(open(self.json_path))['offset'] - 20
        else:
            self.infos['dir_'] = os.path.join(os.getcwd(), 'tumblr-%s' % tag)

            if not os.path.exists(self.infos['dir_']):
                if not self.args.play:
                    os.makedirs(self.infos['dir_'])
                    self.json_path = os.path.join(self.infos['dir_'], 'json.json')
                    self.offset = int(time.time())
            else:
                self.json_path = os.path.join(self.infos['dir_'], 'json.json')
                if os.path.exists(self.json_path):
                    self.offset = json.load(open(self.json_path))['offset']

        if not os.path.exists(os.path.join(self.infos['dir_'], target_type)):
            if not self.args.play:
                os.makedirs(os.path.join(self.infos['dir_'], target_type))

        if self.args.offset:
            self.offset = self.args.offset

        print s % (1, 92, '\n   ## begin'), 'offset = %s' % self.offset

    def download(self):
        def run(i, dir_):
            filepath = os.path.join(dir_, i['subdir'], i['filename'])
            if os.path.exists(filepath):
                return None
            num = random.randint(0, 7) % 8
            col = s % (1, num + 90, filepath)
            print '  ++ download: %s' % col
            cmd = [
                'wget', '-c', '-q',
                '-O', '%s.tmp' % filepath,
                '--user-agent', '"%s"' % headers['User-Agent'],
                '%s' % i['durl'].replace('http:', 'https:')
            ]
            f = subprocess.Popen(cmd)
            return f, filepath

        def callback(filepath):
            os.rename('%s.tmp' % filepath, filepath)

        self.tasks.extend(self.infos['items'])
        while True:
            async(self.tasks, self.queue, dir_=self.infos['dir_'], run=run,
                cb=callback, num=self.processes)
            if len(self.tasks) <= self.processes:
                break

    def play(self):
        for item in self.infos['items']:
            num = random.randint(0, 7) % 8
            col = s % (2, num + 90, item['durl'])
            print '  ++ play:', col
            quiet = ' --really-quiet' if self.args.quiet else ''
            cmd = 'mpv%s --no-ytdl --cache-default 20480 --cache-secs 120 ' \
                '--http-header-fields "User-Agent:%s" ' \
                '"%s"' \
                % (quiet, headers['User-Agent'], item['durl'])

            os.system(cmd)
            timeout = 1
            ii, _, _ = select.select([sys.stdin], [], [], timeout)
            if ii:
                sys.exit(0)
            else:
                pass

    def download_photos_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'photos')

        while True:
            self.infos['items'] = self._photo(
                base_hostname, offset=self.offset if not post_id else '', post_id=post_id)
            if not self.infos['items']:
                break
            self.offset += 20
            self.save_json()
            self.download()
            if post_id: break

    def download_photos_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'photos', tag=tag)

        while True:
            self.info['items'] = self._photo(base_hostname, tag=tag, before=self.offset)
            if not self.infos['items']:
                break
            self.offset = self.infos['items'][-1]['timestamp']
            self.save_json()
            self.download()

    def download_videos_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'videos')

        while True:
            self.infos['items'] = self._video(
                base_hostname, offset=self.offset, post_id=post_id)
            if not self.infos['items']:
                break
            self.offset += 20
            self.save_json() if not self.args.play else None
            self.download()
            if post_id: break

    def download_videos_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'videos', tag)

        while True:
            self.infos['items'] = self._video(
                base_hostname, before=self.offset, tag=tag)
            if not self.infos['items']:
                break
            self.offset = self.infos['items'][-1]['timestamp']
            self.save_json() if not self.args.play else None
            self.download()

    def download_audios_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'audios')

        while True:
            self.infos['items'] = self._audio(
                base_hostname, offset=self.offset if not post_id else '', post_id=post_id)
            if not self.infos['items']:
                break
            self.offset += 20
            self.save_json() if not self.args.play else None
            self.download()
            if post_id: break

    def download_audios_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'audios', tag)

        while True:
            self.infos['items'] = self._audio(
                base_hostname, before=self.offset, tag=tag)
            if not self.infos['items']:
                break
            self.offset = self.infos['items'][-1]['timestamp']
            self.save_json() if not self.args.play else None
            self.download()

    def download_photos(self, base_hostname, post_id='', tag=''):
        if tag:
            self.download_photos_by_tag(base_hostname, tag)
        else:
            self.download_photos_by_offset(base_hostname, post_id=post_id)

    def download_videos(self, base_hostname, post_id='', tag=''):
        if tag:
            self.download_videos_by_tag(base_hostname, tag)
        else:
            self.download_videos_by_offset(base_hostname, post_id=post_id)

    def download_audios(self, base_hostname, post_id='', tag=''):
        if tag:
            self.download_audios_by_tag(base_hostname, tag)
        else:
            self.download_audios_by_offset(base_hostname, post_id=post_id)

    def fix_photos(self, base_hostname):
        self.init_infos(base_hostname, 'photos')
        t = os.listdir(os.path.join(self.infos['dir_'], 'photos'))
        t = [i[:i.find('_')] for i in t if i.endswith('.tmp')]
        ltmp = list(set(t))
        for post_id in ltmp:
            self.infos['items'] = self._photo(base_hostname, post_id=post_id)
            self.download()

    def parse_urls(self, urls):
        for url in urls:
            if not url.startswith('http'):
                raise Error(s % (1, 91, 'url must start with http:// or https://'))

            base_hostname = urlparse.urlparse(url).netloc
            if self.args.check:
                self.fix_photos(base_hostname)
                continue

            if re.search(r'post/(\d+)', url):
                post_id = re.search(r'post/(\d+)', url).group(1)
            else:
                post_id = ''

            if self.args.video:
                self.download_videos(base_hostname, post_id=post_id, tag=self.args.tag)
            elif self.args.audio:
                self.download_audios(base_hostname, post_id=post_id, tag=self.args.tag)
            else:
                self.download_photos(base_hostname, post_id=post_id, tag=self.args.tag)

def main(argv):
    p = argparse.ArgumentParser(
        description='download from tumblr.com')
    p.add_argument('xxx', type=str, nargs='*', help='命令对象.')
    p.add_argument('-p', '--processes', action='store', type=int, default=10,
                   help='指定多进程数,默认为10个,最多为20个 eg: -p 20')
    p.add_argument('-f', '--offset', action='store', type=int, default=0,
                   help='offset')
    p.add_argument('-q', '--quiet', action='store_true',
                   help='quiet')
    p.add_argument('-c', '--check', action='store_true',
                   help='尝试修复未下载成功的图片')
    p.add_argument('-P', '--play', action='store_true',
                   help='play with mpv')
    p.add_argument('-V', '--video', action='store_true',
                   help='download videos')
    p.add_argument('-A', '--audio', action='store_true',
                   help='download audios')
    p.add_argument('-t', '--tag', action='store',
                   default=None, type=str,
                   help='下载特定tag的图片, eg: -t beautiful')
    #global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    tumblr = Tumblr(args)
    tumblr.parse_urls(xxx)

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
