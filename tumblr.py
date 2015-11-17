#!/usr/bin/env python2
# vim: set fileencoding=utf8

from __future__ import unicode_literals

import os
import sys
import re
import json
import collections
import multiprocessing
import requests
requests.packages.urllib3.disable_warnings()
import argparse
import random
import time
import select
import signal

API_KEY = 'fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4'

PID_PATH = '/tmp/tumblr.py.pid'

# statistic parameters
NET_ERRORS = multiprocessing.Value('i', 0)
UNCOMPLETION = multiprocessing.Value('i', 0)
DOWNLOAD_ERRORS = multiprocessing.Value('i', 0)
DOWNLOADS = multiprocessing.Value('i', 0)
COMPLETION = multiprocessing.Value('i', 0)
OFFSET = multiprocessing.Value('i', 0)

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

class Error(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def reset_statistic_params():
    NET_ERRORS.value = 0
    UNCOMPLETION.value = 0
    DOWNLOAD_ERRORS.value = 0
    DOWNLOADS.value = 0
    COMPLETION.value = 0
    OFFSET.value = 0

def play(urls, args):
    for url in urls:
        tumblr = Tumblr(args, url)
        while True:
            items = tumblr.get_item_generator()
            if not items:
                break
            play_do(items, args.quiet)

def play_do(items, quiet):
    for item in items:
        num = random.randint(0, 7) % 8
        col = s % (2, num + 90, item['durl'])
        print '  ++ play:', col
        quiet = ' --really-quiet' if quiet else ''
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

def remove_downloaded_items(items):
    N = len(items)
    for i in range(N):
        item = items.pop()
        filepath = os.path.join(item['dir_'], item['subdir'], item['filename'])
        if not os.path.exists(filepath):
            items.appendleft(item)

def download_run(item):
    filepath = os.path.join(item['dir_'], item['subdir'], item['filename'])
    # if os.path.exists(filepath):
        # return None
    # num = random.randint(0, 7) % 8
    # col = s % (1, num + 90, filepath)
    # print '  ++ download: %s' % col
    cmd = ' '.join([
        'wget', '-c', '-q', '-T', '10',
        '-O', '"%s.tmp"' % filepath,
        '--user-agent', '"%s"' % headers['User-Agent'],
        '"%s"' % item['durl'].replace('http:', 'https:')
    ])
    status = os.system(cmd)
    return status, filepath

def callback(filepath):
    os.rename('%s.tmp' % filepath, filepath)

class Downloader(multiprocessing.Process):
    def __init__(self, queue, lock):
        super(Downloader, self).__init__()
        self.queue = queue
        self.daemon = True
        self.lock = lock

    def run(self):
        while True:
            item = self.queue.get()
            self.queue.task_done()
            if not item:
                break
            status = download_run(item)
            if not status: # file was downloaded.
                continue
            status, filepath = status
            if status != 0:
                # print s % (1, 93, '[Error %s] at wget' % status), wget_es[status]
                self.lock.acquire()
                UNCOMPLETION.value += 1
                DOWNLOAD_ERRORS.value += 1
                self.lock.release()
            else:
                self.lock.acquire()
                DOWNLOADS.value += 1
                self.lock.release()
                callback(filepath)

class TumblrAPI(object):
    def _request(self, base_hostname, target, type, params):
        api_url = '/'.join(['https://api.tumblr.com/v2/blog',
                           base_hostname, target, type])
        params['api_key'] = API_KEY
        while True:
            try:
                res = ss.get(api_url, params=params, timeout=10)
                json_data = res.json()
                break
            except KeyboardInterrupt:
                sys.exit()
            except Exception as e:
                NET_ERRORS.value += 1  # count errors
                # print s % (1, 93, '[Error at requests]:'), e
                time.sleep(5)
        if json_data['meta']['msg'].lower() != 'ok':
            raise Error(s % (1, 91, json_data['meta']['msg']))

        return json_data['response']

    def _info(self, base_hostname):
        return self._request(base_hostname, 'info', '', None)

    def _photo(self, base_hostname, offset='', tag='', post_id='', to_items=True):
        def make_items(raw_data):
            items = collections.deque()
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
            items = collections.deque()
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
            items = collections.deque()
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
    def __init__(self, args, url):
        self.args = args
        self.offset = self.args.offset
        self.make_items = self.parse_urls(url)

    def save_json(self):
        with open(self.json_path, 'w') as g:
            g.write(json.dumps(
                {'offset': self.offset}, indent=4, sort_keys=True))

    def init_infos(self, base_hostname, target_type, tag=''):
        self.infos = {'host': base_hostname}
        if not tag:
            dir_ = os.path.join(os.getcwd(), self.infos['host'])
            json_path = os.path.join(dir_, 'json.json')

            if not os.path.exists(dir_):
                if not self.args.play:
                    os.makedirs(dir_)
            else:
                if os.path.exists(json_path):
                    self.offset = json.load(open(json_path))['offset'] - 60 \
                        if not self.args.update else self.args.offset
                    if self.offset < 0: self.offset = 0
        else:
            dir_ = os.path.join(os.getcwd(), 'tumblr-%s' % tag)
            json_path = os.path.join(dir_, 'json.json')

            if not os.path.exists(dir_):
                if not self.args.play:
                    os.makedirs(dir_)
                    self.offset = int(time.time())
            else:
                if os.path.exists(json_path):
                    self.offset = json.load(open(json_path))['offset'] \
                        if not self.args.update else int(time.time())

        self.infos['dir_'] = dir_
        self.json_path = json_path
        subdir = os.path.join(dir_, target_type)
        if not os.path.exists(subdir) and not self.args.play:
            os.makedirs(subdir)

        if not self.args.play:
            for fl in os.listdir(subdir):
                if not fl.endswith('.tmp'):
                    COMPLETION.value += 1
                else:
                    UNCOMPLETION.value += 1

        if self.args.offset:
            self.offset = self.args.offset

        print s % (1, 92, '## begin:'), 'offset = %s,' % self.offset, base_hostname
        print s % (1, 97, 'INFO:\n') + \
            'D = Downloads, R = Repair_Need\n' + \
            'C = Completion, NE = Net_Errors, O = Offset'

    def download_photos_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'photos')

        def do():
            items = self._photo(
                base_hostname, offset=self.offset if not post_id else '', post_id=post_id)
            if not items:
                return []
            self.offset += 20
            self.save_json()
            return items
        return do

    def download_photos_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'photos', tag=tag)

        def do():
            items = self._photo(base_hostname, tag=tag, before=self.offset)
            if not items:
                return []
            self.offset = items[-1]['timestamp']
            self.save_json()
            return items
        return do

    def download_videos_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'videos')

        def do():
            items = self._video(
                base_hostname, offset=self.offset, post_id=post_id)
            if not items:
                return []
            self.offset += 20
            if not self.args.play:
                self.save_json()
            return items
        return do

    def download_videos_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'videos', tag)

        def do():
            items = self._video(
                base_hostname, before=self.offset, tag=tag)
            if not items:
                return []
            self.offset = items[-1]['timestamp']
            if not self.args.play:
                self.save_json()
            return items
        return do

    def download_audios_by_offset(self, base_hostname, post_id):
        self.init_infos(base_hostname, 'audios')

        def do():
            items = self._audio(
                base_hostname, offset=self.offset if not post_id else '', post_id=post_id)
            if not items:
                return []
            self.offset += 20
            if not self.args.play:
                self.save_json()
            return items
        return do

    def download_audios_by_tag(self, base_hostname, tag):
        self.init_infos(base_hostname, 'audios', tag)

        def do():
            items = self._audio(
                base_hostname, before=self.offset, tag=tag)
            if not self.infos['items']:
                return []
            self.offset = self.infos['items'][-1]['timestamp']
            if not self.args.play:
                self.save_json()
            return items
        return do

    def download_photos(self, base_hostname, post_id='', tag=''):
        if tag:
            return self.download_photos_by_tag(base_hostname, tag)
        else:
            return self.download_photos_by_offset(base_hostname, post_id=post_id)

    def download_videos(self, base_hostname, post_id='', tag=''):
        if tag:
            return self.download_videos_by_tag(base_hostname, tag)
        else:
            return self.download_videos_by_offset(base_hostname, post_id=post_id)

    def download_audios(self, base_hostname, post_id='', tag=''):
        if tag:
            return self.download_audios_by_tag(base_hostname, tag)
        else:
            return self.download_audios_by_offset(base_hostname, post_id=post_id)

    def fix_photos(self, base_hostname):
        self.init_infos(base_hostname, 'photos')

        t = os.listdir(os.path.join(self.infos['dir_'], 'photos'))
        t = [i[:i.find('_')] for i in t if i.endswith('.tmp')]
        self.post_ids = list(set(t))

        def do():
            if len(self.post_ids):
                post_id = self.post_ids.pop()
                return self._photo(base_hostname, post_id=post_id)
            else:
                return []
        return do

    def parse_urls(self, url):
        _mod = re.search(r'(http://|https://|)(?P<hostname>.+\.tumblr.com)', url)
        if not _mod:
            print s % (1, 91, '[Error]:'), 'url is illegal.', '\n' + url.decode('utf8', 'ignore')
            return lambda: []
        base_hostname = _mod.group('hostname')
        if self.args.check:
            return self.fix_photos(base_hostname)

        if re.search(r'post/(\d+)', url):
            post_id = re.search(r'post/(\d+)', url).group(1)
        else:
            post_id = ''

        if self.args.video:
            return self.download_videos(base_hostname, post_id=post_id, tag=self.args.tag)
        elif self.args.audio:
            return self.download_audios(base_hostname, post_id=post_id, tag=self.args.tag)
        else:
            return self.download_photos(base_hostname, post_id=post_id, tag=self.args.tag)

    def get_item_generator(self):
        OFFSET.value = self.offset
        items = self.make_items()
        for item in items:
            item['dir_'] = self.infos['dir_']
        return items

def args_handler(argv):
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
    p.add_argument('--update', action='store_true',
                   help='update new things')
    p.add_argument('--redownload', action='store_true',
                   help='redownload all things')
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    if args.redownload: args.update = True
    return args, xxx

def print_msg(check):
    time.sleep(2) # initial interval

    while True:
        msg = "\r%s, %s, %s, %s, %s " % \
                (
                    'D: ' + s % (1, 92, DOWNLOADS.value),
                    'R: ' + s % (1, 93, UNCOMPLETION.value \
                        if not check \
                        else UNCOMPLETION.value - DOWNLOAD_ERRORS.value - DOWNLOADS.value),
                    'C: ' + s % (1, 97, COMPLETION.value + DOWNLOADS.value),
                    'NE: ' + s % (1, 91, NET_ERRORS.value),
                    'O: %s' % OFFSET.value
                )
        sys.stdout.write(msg)
        sys.stdout.flush()
        time.sleep(2)

def sighandler(signum, frame):
    # print s % (1, 91, "\n  !! Signal:"), signum
    # print s % (1, 91, "  !! Frame: %s" % frame)
    sys.exit()

def handle_signal():
    signal.signal(signal.SIGBUS, sighandler)
    signal.signal(signal.SIGHUP, sighandler)
    # http://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    signal.signal(signal.SIGQUIT, sighandler)
    signal.signal(signal.SIGSYS, sighandler)

    signal.signal(signal.SIGABRT, sighandler)
    signal.signal(signal.SIGFPE, sighandler)
    signal.signal(signal.SIGILL, sighandler)
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGSEGV, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

def main(argv):
    handle_signal()
    args, xxx = args_handler(argv)

    if args.play:
        play(xxx, args)

    lock = multiprocessing.Lock()
    queue = multiprocessing.JoinableQueue(maxsize=args.processes)
    thrs = []
    for i in range(args.processes):
        thr = Downloader(queue, lock)
        thr.start()
        thrs.append(thr)

    # massage thread
    msg_thr = multiprocessing.Process(target=print_msg, args=(args.check,))
    msg_thr.daemon = True
    msg_thr.start()

    for url in xxx:
        reset_statistic_params()
        tumblr = Tumblr(args, url)
        not_add = 0
        while True:
            items = tumblr.get_item_generator()
            if not items:
                break

            # Check the downloaded items.
            # It will be exited, if there is no new item to download
            # in 5 loops, unless with --redownload
            remove_downloaded_items(items)
            if not args.redownload:
                if not items:
                    not_add += 1
                    if not_add > 5:
                        print s % (1, 93, '\n[Warning]:'), \
                            'There is nothing new to download in 5 loops.\n', \
                            'If you want to scan all resources, using --redownload\n'  \
                            'or running the script again to next 5 loops.'
                        break
                    continue
                else:
                    not_add = 0

            for item in items:
                queue.put(item)

    while not queue.empty():
        time.sleep(2)

    for i in range(args.processes):
        queue.put(None)

    queue.join()

    for thr in thrs:
        thr.join()

    msg_thr.terminate()

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
