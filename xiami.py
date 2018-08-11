#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import sys
from getpass import getpass
import os
import copy
import random
import time
import datetime
import json
import argparse
import requests
import urllib
import hashlib
import select
from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,APIC,TDRC,COMM,TPOS,USLT
from HTMLParser import HTMLParser

url_song = "http://www.xiami.com/song/%s"
url_album = "http://www.xiami.com/album/%s"
url_collect = "http://www.xiami.com/collect/ajax-get-list"
url_artist_albums = "http://www.xiami.com/artist/album/id/%s/page/%s"
url_artist_top_song = "http://www.xiami.com/artist/top-%s"
url_lib_songs = "http://www.xiami.com/space/lib-song/u/%s/page/%s"
url_recent = "http://www.xiami.com/space/charts-recent/u/%s/page/%s"

# 电台来源:来源于"收藏的歌曲","收藏的专辑","喜欢的艺人","我收藏的精选集"
url_radio_my = "http://www.xiami.com/radio/xml/type/4/id/%s"
# 虾米猜, 基于你的虾米试听行为所建立的个性电台
url_radio_c = "http://www.xiami.com/radio/xml/type/8/id/%s"

############################################################
# wget exit status
wget_es = {
    0:"No problems occurred.",
    2:"User interference.",
    1<<8:"Generic error code.",
    2<<8:"Parse error - for instance, when parsing command-line ' \
        'optio.wgetrc or .netrc...",
    3<<8:"File I/O error.",
    4<<8:"Network failure.",
    5<<8:"SSL verification failure.",
    6<<8:"Username/password authentication failure.",
    7<<8:"Protocol errors.",
    8<<8:"Server issued an error response."
}
############################################################

parser = HTMLParser()
s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template

cookie_file = os.path.join(os.path.expanduser('~'), '.Xiami.cookies')

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://www.xiami.com/",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"\
}

HEADERS2 = {
    'pragma': 'no-cache',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
    'cache-control': 'no-cache',
    'authority': 'www.xiami.com',
    'x-requested-with': 'XMLHttpRequest',
    'referer': 'https://www.xiami.com/play?ids=/song/playlist/id/',
}

ss = requests.session()
ss.headers.update(headers)

############################################################
# Regular Expression Templates
re_disc_description = r'disc (\d+) \[(.+?)\]'
############################################################

def decry(row, encryed_url):
    url = encryed_url
    urllen = len(url)
    rows = int(row)

    cols_base = urllen / rows  # basic column count
    rows_ex = urllen % rows    # count of rows that have 1 more column

    matrix = []
    for r in xrange(rows):
        length = cols_base + 1 if r < rows_ex else cols_base
        matrix.append(url[:length])
        url = url[length:]

    url = ''
    for i in xrange(urllen):
        url += matrix[i % rows][i / rows]

    return urllib.unquote(url).replace('^', '0')

def modificate_text(text):
    text = parser.unescape(text)
    text = re.sub(r'//*', '-', text)
    text = text.replace('/', '-')
    text = text.replace('\\', '-')
    text = re.sub(r'\s\s+', ' ', text)
    text = text.strip()
    return text

def modificate_file_name_for_wget(file_name):
    file_name = re.sub(r'\s*:\s*', u' - ', file_name)    # for FAT file system
    file_name = file_name.replace('?', '')      # for FAT file system
    file_name = file_name.replace('"', '\'')    # for FAT file system
    file_name = file_name.replace('$', '\\$')    # for command, see issue #7
    return file_name

def z_index(song_infos):
    size = len(song_infos)
    z = len(str(size))
    return z

########################################################

class Song(object):

    def __init__(self):
        self.__sure()
        self.track = 0
        self.year = 0
        self.cd_serial = 0
        self.disc_description = ''

        # z = len(str(album_size))
        self.z = 1

    def __sure(self):
        __dict__ = self.__dict__
        if '__keys' not in __dict__:
            __dict__['__keys'] = {}

    def __getattr__(self, name):
        __dict__ = self.__dict__
        return __dict__['__keys'].get(name)

    def __setattr__(self, name, value):
        __dict__ = self.__dict__
        __dict__['__keys'][name] = value

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def feed(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)


class XiamiH5API(object):

    URL = 'http://api.xiami.com/web'
    PARAMS = {
        'v': '2.0',
        'app_key': '1',
    }

    def __init__(self):
        self.cookies = {
            'user_from': '2',
            'XMPLAYER_addSongsToggler': '0',
            'XMPLAYER_isOpen': '0',
            '_xiamitoken': hashlib.md5(str(time.time())).hexdigest()
        }
        self.sess = requests.session()
        self.sess.cookies.update(self.cookies)

    def _request(self, url, method='GET', **kwargs):
        try:
            resp = self.sess.request(method, url, **kwargs)
        except Exception, err:
            print 'Error:', err
            sys.exit()

        return resp

    def _make_params(self, **kwargs):
        params = copy.deepcopy(self.PARAMS)
        params.update(kwargs)
        return params

    def song(self, song_id):
        params = self._make_params(id=song_id, r='song/detail')
        url = self.URL
        resp = self._request(url, params=params, headers=headers)

        info = resp.json()['data']['song']
        pic_url = re.sub('_\d+\.', '.', info['logo'])
        song = Song()
        song.feed(
            song_id=info['song_id'],
            song_name=info['song_name'],
            album_id=info['album_id'],
            album_name=info['album_name'],
            artist_id=info['artist_id'],
            artist_name=info['artist_name'],
            singers=info['singers'],
            album_pic_url=pic_url,
            comment='http://www.xiami.com/song/' + str(info['song_id'])
        )
        return song

    def album(self, album_id):
        url = self.URL
        params = self._make_params(id=album_id, r='album/detail')
        resp = self._request(url, params=params, headers=headers)

        info = resp.json()['data']
        songs = []
        album_id=info['album_id'],
        album_name=info['album_name'],
        artist_id = info['artist_id']
        artist_name = info['artist_name']
        pic_url = re.sub('_\d+\.', '.', info['album_logo'])
        for track, info_n in enumerate(info['songs'], 1):
            song = Song()
            song.feed(
                song_id=info_n['song_id'],
                song_name=info_n['song_name'],
                album_id=album_id,
                album_name=album_name,
                artist_id=artist_id,
                artist_name=artist_name,
                singers=info_n['singers'],
                album_pic_url=pic_url,
                track=track,
                comment='http://www.xiami.com/song/' + str(info_n['song_id'])
            )
            songs.append(song)
        return songs

    def collect(self, collect_id):
        url = self.URL
        params = self._make_params(id=collect_id, r='collect/detail')
        resp = self._request(url, params=params, headers=headers)

        info = resp.json()['data']
        collect_name = info['collect_name']
        collect_id = info['list_id']
        songs = []
        for info_n in info['songs']:
            pic_url = re.sub('_\d+\.', '.', info['album_logo'])
            song = Song()
            song.feed(
                song_id=info_n['song_id'],
                song_name=info_n['song_name'],
                album_id=info_n['album_id'],
                album_name=info_n['album_name'],
                artist_id=info_n['artist_id'],
                artist_name=info_n['artist_name'],
                singers=info_n['singers'],
                album_pic_url=pic_url,
                comment='http://www.xiami.com/song/' + str(info_n['song_id'])
            )
            songs.append(song)
        return collect_id, collect_name, songs

    def artist_top_songs(self, artist_id, page=1, limit=20):
        url = self.URL
        params = self._make_params(id=artist_id, page=page, limit=limit, r='artist/hot-songs')
        resp = self._request(url, params=params, headers=headers)

        info = resp.json()['data']
        for info_n in info['songs']:
            song_id = info_n['song_id']
            yield self.song(song_id)

    def search_songs(self, keywords, page=1, limit=20):
        url = self.URL
        params = self._make_params(key=keywords, page=page, limit=limit, r='search/songs')
        resp = self._request(url, params=params, headers=headers)

        info = resp.json()['data']
        for info_n in info['songs']:
            pic_url = re.sub('_\d+\.', '.', info['album_logo'])
            song = Song()
            song.feed(
                song_id=info_n['song_id'],
                song_name=info_n['song_name'],
                album_id=info_n['album_id'],
                album_name=info_n['album_name'],
                artist_id=info_n['artist_id'],
                artist_name=info_n['artist_name'],
                singers=info_n['singer'],
                album_pic_url=pic_url,
                comment='http://www.xiami.com/song/' + str(info_n['song_id'])
            )
            yield song

    def get_song_id(self, *song_sids):
        song_ids = []
        for song_sid in song_sids:
            if isinstance(song_sid, int) or song_sid.isdigit():
                song_ids.append(int(song_sid))

            url = 'https://www.xiami.com/song/playlist/id/{}/cat/json'.format(song_sid)
            resp = self._request(url, headers=headers)
            info = resp.json()
            song_id = int(str(info['data']['trackList'][0]['song_id']))
            song_ids.append(song_id)
        return song_ids


class XiamiWebAPI(object):

    URL = 'https://www.xiami.com/song/playlist/'

    def __init__(self):
        self.sess = requests.session()

    def _request(self, url, method='GET', **kwargs):
        try:
            resp = self.sess.request(method, url, **kwargs)
        except Exception, err:
            print 'Error:', err
            sys.exit()

        return resp

    def _make_song(self, info):
        song = Song()

        location=info['location']
        row = location[0]
        encryed_url = location[1:]
        durl = decry(row, encryed_url)

        song.feed(
            song_id=info['song_id'],
            song_sub_title=info['song_sub_title'],
            songwriters=info['songwriters'],
            singers=info['singers'],
            song_name=parser.unescape(info['name']),

            album_id=info['album_id'],
            album_name=info['album_name'],

            artist_id=info['artist_id'],
            artist_name=info['artist_name'],

            composer=info['composer'],
            lyric_url='http:' + info['lyric_url'],

            track=info['track'],
            cd_serial=info['cd_serial'],
            album_pic_url='http:' + info['album_pic'],
            comment='http://www.xiami.com/song/' + str(info['song_id']),

            length=info['length'],
            play_count=info['playCount'],

            location=info['location'],
            location_url=durl
        )
        return song

    def _find_z(self, album):
        zs = []
        song = album[0]

        for i, song in enumerate(album[:-1]):
            next_song = album[i+1]

            cd_serial = song.cd_serial
            next_cd_serial = next_song.cd_serial

            if cd_serial != next_cd_serial:
                z = len(str(song.track))
                zs.append(z)

        z = len(str(song.track))
        zs.append(z)

        for song in album:
            song.z = zs[song.cd_serial - 1]

    def song(self, song_id):
        url = self.URL + 'id/%s/cat/json' % song_id
        resp = self._request(url, headers=HEADERS2)

        # there is no song
        if not resp.json().get('data'):
            return None

        info = resp.json()['data']['trackList'][0]
        song = self._make_song(info)
        return song

    def songs(self, *song_ids):
        url = self.URL + 'id/%s/cat/json' % '%2C'.join(song_ids)
        resp = self._request(url, headers=HEADERS2)

        # there is no song
        if not resp.json().get('data'):
            return None

        info = resp.json()['data']
        songs = []
        for info_n in info['trackList']:
            song = self._make_song(info_n)
            songs.append(song)
        return songs

    def album(self, album_id):
        url = self.URL + 'id/%s/type/1/cat/json' % album_id
        resp = self._request(url, headers=HEADERS2)

        # there is no album
        if not resp.json().get('data'):
            return None

        info = resp.json()['data']
        songs = []
        for info_n in info['trackList']:
            song = self._make_song(info_n)
            songs.append(song)

        self._find_z(songs)
        return songs

    def collect(self, collect_id):
        url = self.URL + 'id/%s/type/3/cat/json' % collect_id
        resp = self._request(url, headers=HEADERS2)

        info = resp.json()['data']
        songs = []
        for info_n in info['trackList']:
            song = self._make_song(info_n)
            songs.append(song)
        return songs

    def search_songs(self, keywords):
        url = 'https://www.xiami.com/search?key=%s&_=%s' % (
            urllib.quote(keywords), int(time.time() * 1000))
        resp = self._request(url, headers=headers)

        html = resp.content
        song_ids = re.findall(r'song/(\w+)"', html)
        songs = self.songs(*song_ids)
        return songs


class xiami(object):
    def __init__(self):
        self.dir_ = os.getcwdu()
        self.template_record = 'https://www.xiami.com/count/playrecord?sid={song_id}&ishq=1&t={time}&object_id={song_id}&object_name=default&start_point=120&_xiamitoken={token}'

        self.collect_id = ''
        self.album_id = ''
        self.artist_id = ''
        self.song_id = ''
        self.user_id = ''
        self.cover_id = ''
        self.cover_data = ''

        self.html = ''
        self.disc_description_archives = {}

        self.download = self.play if args.play else self.download
        self._is_play = bool(args.play)

        self._api = XiamiWebAPI()

    def init(self):
        if os.path.exists(cookie_file):
            try:
                cookies = json.load(open(cookie_file))
                ss.cookies.update(cookies.get('cookies', cookies))
                if not self.check_login():
                    print s % (1, 91, '  !! cookie is invalid, please login\n')
                    sys.exit(1)
            except:
                open(cookie_file, 'w').close()
                print s % (1, 97, '  please login')
                sys.exit(1)
        else:
            print s % (1, 91, '  !! cookie_file is missing, please login')
            sys.exit(1)

    def check_login(self):
        #print s % (1, 97, '\n  -- check_login')
        url = 'http://www.xiami.com/task/signin'
        r = self._request(url)
        if r.content:
            #print s % (1, 92, '  -- check_login success\n')
            # self.save_cookies()
            return True
        else:
            print s % (1, 91, '  -- login fail, please check email and password\n')
            return False

    def _request(self, url, headers=None, params=None, data=None, method='GET', timeout=30, retry=2):
        for _ in range(retry):
            try:
                headers = headers or ss.headers
                resp = ss.request(method, url, headers=headers, params=params, data=data, timeout=timeout)
            except Exception, err:
                continue

            if not resp.ok:
                raise Exception("response is not ok, status_code = %s" % resp.status_code)

            # save cookies
            self.save_cookies()

            return resp
        raise err

    # manually, add cookies
    # you must know how to get the cookie
    def add_cookies(self, cookies):
        _cookies = {}
        for item in cookies.strip('; ').split('; '):
            k, v = item.split('=', 1)
            _cookies[k] = v
        self.save_cookies(_cookies)
        ss.cookies.update(_cookies)

    def login(self, email, password):
        print s % (1, 97, '\n  -- login')

        #validate = self.get_validate()
        data = {
            'email': email,
            'password': password,
            #'validate': validate,
            'remember': 1,
            'LoginButton': '登录'
        }

        hds = {
            'Origin': 'http://www.xiami.com',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cache-Control': 'max-age=1',
            'Referer': 'http://www.xiami.com/web/login',
            'Connection': 'keep-alive',
            '_xiamitoken': hashlib.md5(str(time.time())).hexdigest()
        }

        url = 'https://login.xiami.com/web/login'

        for i in xrange(2):
            res = self._request(url, headers=hds, data=data)
            if ss.cookies.get('member_auth'):
                return True
            else:
                if 'checkcode' not in res.content:
                    return False
                validate = self.get_validate(res.content)
                data['validate'] = validate

        return False

    # {{{ code from https://github.com/ly0/xiami-tools/blob/master/xiami.py
    def login_taobao(self, username, password):
        print s % (1, 97, '\n  -- login taobao')

        p = {
            "lang": "zh_cn",
            "appName": "xiami",
            "appEntrance": "taobao",
            "cssLink": "",
            "styleType": "vertical",
            "bizParams": "",
            "notLoadSsoView": "",
            "notKeepLogin": "",
            "appName": "xiami",
            "appEntrance": "taobao",
            "cssLink": "https://h.alipayobjects.com/static/applogin/" \
                        "assets/login/mini-login-form-min.css",
            "styleType": "vertical",
            "bizParams": "",
            "notLoadSsoView": "true",
            "notKeepLogin": "true",
            "rnd": str(random.random()),
        }
        url = 'https://passport.alipay.com/mini_login.htm'
        r = ss.get(url, params=p, verify=True)
        cm = r.content

        data = {
            "loginId": username,
            "password": password,
            "appName": "xiami",
            "appEntrance": "taobao",
            "hsid": re.search(r'"hsid" value="(.+?)"', cm).group(1),
            "cid": re.search(r'"cid" value="(.+?)"', cm).group(1),
            "rdsToken": re.search(r'"rdsToken" value="(.+?)"', cm).group(1),
            "umidToken": re.search(r'"umidToken" value="(.+?)"', cm).group(1),
            "_csrf_token": re.search(r'"_csrf_token" value="(.+?)"', cm).group(1),
            "checkCode": "",
        }
        url = 'https://passport.alipay.com/newlogin/login.do?fromSite=0'
        theaders = headers
        theaders['Referer'] = 'https://passport.alipay.com/mini_login.htm'

        while True:
            r = ss.post(url, data=data, headers=theaders, verify=True)
            j = r.json()

            if j['content']['status'] == -1:
                if 'titleMsg' not in j['content']['data']: continue
                err_msg = j['content']['data']['titleMsg']
                if err_msg == u'请输入验证码' or err_msg == u'验证码错误，请重新输入':
                    captcha_url = 'http://pin.aliyun.com/get_img?' \
                        'identity=passport.alipay.com&sessionID=%s' % data['cid']
                    tr = self._request(captcha_url, headers=theaders)
                    path = os.path.join(os.path.expanduser('~'), 'vcode.jpg')
                    with open(path, 'w') as g:
                        img = tr.content
                        g.write(img)
                    print "  ++ 验证码已经保存至", s % (2, 91, path)
                    captcha = raw_input(
                        (s % (2, 92, '  ++ %s: ' % err_msg)).encode('utf8'))
                    data['checkCode'] = captcha
                    continue

            if not j['content']['data'].get('st'):
                print s % (2, 91, "  !! 输入的 username 或 password 有误.")
                sys.exit(1)

            url = 'http://www.xiami.com/accounts/back?st=%s' \
                % j['content']['data']['st']
            self._request(url, headers=theaders)

            self.save_cookies()
            return
    # }}}

    def get_validate(self, cn):
        #url = 'https://login.xiami.com/coop/checkcode?forlogin=1&%s' \
            #% int(time.time())
        url = re.search(r'src="(http.+checkcode.+?)"', cn).group(1)
        path = os.path.join(os.path.expanduser('~'), 'vcode.png')
        with open(path, 'w') as g:
            data = self._request(url).content
            g.write(data)
        print "  ++ 验证码已经保存至", s % (2, 91, path)
        validate = raw_input(s % (2, 92, '  请输入验证码: '))
        return validate

    def save_cookies(self, cookies=None):
        if not cookies:
            cookies = ss.cookies.get_dict()
        with open(cookie_file, 'w') as g:
            json.dump(cookies, g)

    def get_durl(self, id_):
        while True:
            try:
                if not args.low:
                    url = 'http://www.xiami.com/song/gethqsong/sid/%s'
                    j = self._request(url % id_).json()
                    t = j['location']
                else:
                    url = 'http://www.xiami.com/song/playlist/id/%s'
                    cn = self._request(url % id_).text
                    t = re.search(r'location>(.+?)</location', cn).group(1)
                if not t: return None
                row = t[0]
                encryed_url = t[1:]
                durl = decry(row, encryed_url)
                return durl
            except Exception, e:
                print s % (1, 91, '  |-- Error, get_durl --'), e
                time.sleep(5)

    # FIXME, this request alway returns 405
    def record(self, song_id, album_id):
        return
        #  token = ss.cookies.get('_xiamitoken', '')
        #  t = int(time.time() * 1000)
        #  self._request(self.template_record.format(
            #  song_id=song_id, album_id=album_id, token=token, time=t))

    def get_cover(self, info):
        if info['album_name'] == self.cover_id:
            return self.cover_data
        else:
            self.cover_id = info['album_name']
            while True:
                url = info['album_pic_url']
                try:
                    self.cover_data = self._request(url).content
                    if self.cover_data[:5] != '<?xml':
                        return self.cover_data
                except Exception, e:
                    print s % (1, 91, '   \\\n   \\-- Error, get_cover --'), e
                    time.sleep(5)

    def get_lyric(self, info):
        def lyric_parser(data):
            # get ' ' from http://img.xiami.net/lyric/1_13772259457649.lrc
            if len(data) < 10:
                return None

            if re.search(r'\[\d\d:\d\d', data):
                title = ' title: %s\n' % info['song_name'].encode('utf8')
                album = ' album: %s\n' % info['album_name'].encode('utf8')
                artist = 'artist: %s\n' % info['artist_name'].encode('utf8')

                tdict = {}
                for line in data.split('\n'):
                    if re.search(r'^\[\d\d:', line):
                        cn = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', line)
                        time_tags = re.findall(r'\[\d{2}:\d{2}\.\d{2}\]', line)
                        for tag in time_tags: tdict[tag] = cn + '\n'
                time_tags = tdict.keys()
                time_tags.sort()
                data = ''.join([title, album, artist,
                                '\n------------------\n\n'] + \
                               [tdict[tag] for tag in time_tags])
                return data
            else:
                # for http://img.xiami.net/lyric/upload/19/1770983119_1356864643.lrc
                return data

        url = 'http://www.xiami.com/song/playlist/id/%s' % info['song_id']
        xml = self._request(url).content
        t = re.search('<lyric>(http.+?)</lyric>', xml)
        if not t: return None
        lyric_url = t.group(1)
        data = self._request(lyric_url).content.replace('\r\n', '\n')
        data = lyric_parser(data)
        if data:
            return data.decode('utf8', 'ignore')
        else:
            return None

    def get_disc_description(self, album_url, info):
        if not self.html:
            self.html = self._request(album_url).text
            t = re.findall(re_disc_description, self.html)
            t = dict([(a, modificate_text(parser.unescape(b))) \
                      for a, b in t])
            self.disc_description_archives = dict(t)
        if self.disc_description_archives.has_key(info['cd_serial']):
            disc_description = self.disc_description_archives[info['cd_serial']]
            return u'(%s)' % disc_description
        else:
            return u''

    def modified_id3(self, file_name, info):
        id3 = ID3()
        id3.add(TRCK(encoding=3, text=str(info['track'])))
        id3.add(TDRC(encoding=3, text=str(info['year'])))
        id3.add(TIT2(encoding=3, text=info['song_name']))
        id3.add(TALB(encoding=3, text=info['album_name']))
        id3.add(TPE1(encoding=3, text=info['artist_name']))
        id3.add(TPOS(encoding=3, text=str(info['cd_serial'])))
        lyric_data = self.get_lyric(info)
        id3.add(USLT(encoding=3, text=lyric_data)) if lyric_data else None
        #id3.add(TCOM(encoding=3, text=info['composer']))
        #id3.add(WXXX(encoding=3, desc=u'xiami_song_url', text=info['song_url']))
        #id3.add(TCON(encoding=3, text=u'genre'))
        #id3.add(TSST(encoding=3, text=info['sub_title']))
        #id3.add(TSRC(encoding=3, text=info['disc_code']))
        id3.add(COMM(encoding=3, desc=u'Comment', \
            text=info['comment']))
        id3.add(APIC(encoding=3, mime=u'image/jpeg', type=3, \
            desc=u'Front Cover', data=self.get_cover(info)))
        id3.save(file_name)

    def url_parser(self, urls):
        for url in urls:
            if '/collect/' in url:
                self.collect_id = re.search(r'/collect/(\w+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析精选集信息 ...'))
                self.download_collect()

            elif '/album/' in url:
                self.album_id = re.search(r'/album/(\w+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析专辑信息 ...'))
                self.download_album()

            elif '/artist/' in url or 'i.xiami.com' in url:
                def get_artist_id(url):
                    html = self._request(url).text
                    artist_id = re.search(r'artist_id = \'(\w+)\'', html).group(1)
                    return artist_id

                self.artist_id = re.search(r'/artist/(\w+)', url).group(1) \
                    if '/artist/' in url else get_artist_id(url)
                code = raw_input('  >> a  # 艺术家所有专辑.\n' \
                    '  >> r  # 艺术家 radio\n' \
                    '  >> t  # 艺术家top 20歌曲.\n  >> ')
                if code == 'a':
                    #print(s % (2, 92, u'\n  -- 正在分析艺术家专辑信息 ...'))
                    self.download_artist_albums()
                elif code == 't':
                    #print(s % (2, 92, u'\n  -- 正在分析艺术家top20信息 ...'))
                    self.download_artist_top_20_songs()
                elif code == 'r':
                    self.download_artist_radio()
                else:
                    print(s % (1, 92, u'  --> Over'))

            elif '/song/' in url:
                self.song_id = re.search(r'/song/(\w+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析歌曲信息 ...'))
                self.download_song()

            elif '/u/' in url:
                self.user_id = re.search(r'/u/(\w+)', url).group(1)
                code = raw_input(
                    '  >> m   # 该用户歌曲库.\n'
                    '  >> c   # 最近在听\n'
                    '  >> s   # 分享的音乐\n'
                    '  >> r   # 歌曲试听排行 - 一周\n'
                    '  >> rt  # 歌曲试听排行 - 全部 \n'
                    '  >> rm  # 私人电台:来源于"收藏的歌曲","收藏的专辑",'
                    '           "喜欢的艺人","收藏的精选集"\n'
                    '  >> rc  # 虾米猜:基于试听行为所建立的个性电台\n  >> ')
                if code == 'm':
                    #print(s % (2, 92, u'\n  -- 正在分析用户歌曲库信息 ...'))
                    self.download_user_songs(url_lib_songs, u'收藏的歌曲')
                elif code == 'c':
                    self.download_user_songs(url_recent, u'最近在听的歌曲')
                elif code == 's':
                    url_shares = 'http://www.xiami.com' \
                        '/space/feed/u/%s/type/3/page/%s' % (self.user_id, '%s')
                    self.download_user_shares(url_shares)
                elif code == 'r':
                    url = 'http://www.xiami.com/space/charts/u/%s/c/song/t/week' % self.user_id
                    self.download_ranking_songs(url, 'week')
                elif code == 'rt':
                    url = 'http://www.xiami.com/space/charts/u/%s/c/song/t/all' % self.user_id
                    self.download_ranking_songs(url, 'all')
                elif code == 'rm':
                    #print(s % (2, 92, u'\n  -- 正在分析该用户的虾米推荐 ...'))
                    url_rndsongs = url_radio_my
                    self.download_user_radio(url_rndsongs)
                elif code == 'rc':
                    url_rndsongs = url_radio_c
                    self.download_user_radio(url_rndsongs)
                else:
                    print(s % (1, 92, u'  --> Over'))

            elif '/chart/' in url:
                self.chart_id = re.search(r'/c/(\d+)', url).group(1) \
                    if '/c/' in url else 101
                type_ = re.search(r'/type/(\d+)', url).group(1) \
                    if '/type/' in url else 0
                self.download_chart(type_)

            elif '/genre/' in url:
                if '/gid/' in url:
                    self.genre_id = re.search(r'/gid/(\d+)', url).group(1)
                    url_genre = 'http://www.xiami.com' \
                        '/genre/songs/gid/%s/page/%s'
                elif '/sid/' in url:
                    self.genre_id = re.search(r'/sid/(\d+)', url).group(1)
                    url_genre = 'http://www.xiami.com' \
                        '/genre/songs/sid/%s/page/%s'
                else:
                    print s % (1, 91, '  !! Error: missing genre id at url')
                    sys.exit(1)

                code = raw_input('  >> t  # 风格推荐\n' \
                    '  >> r  # 风格radio\n  >> ')
                if code == 't':
                    self.download_genre(url_genre)
                elif code == 'r':
                    self.download_genre_radio(url_genre)

            elif 'luoo.net' in url:
                self.hack_luoo(url)

            elif 'sid=' in url:
                _mod = re.search(r'sid=([\w+,]+\w)', url)
                if _mod:
                    song_ids = _mod.group(1).split(',')
                    self.download_songs(song_ids)

            else:
                print s % (2, 91, u'   请正确输入虾米网址.')

    def make_file_name(self, song, cd_serial_auth=False):
        z = song['z']
        file_name = str(song['track']).zfill(z) + '.' \
            + song['song_name'] \
            + ' - ' + song['artist_name'] + '.mp3'
        if cd_serial_auth:
            song['file_name'] = ''.join([
                '[Disc-',
                str(song['cd_serial']),
                ' # ' + song['disc_description'] \
                    if song['disc_description'] else '', '] ',
                file_name])
        else:
            song['file_name'] = file_name

    def get_songs(self, album_id, song_id=None):
        songs = self._api.album(album_id)

        if not songs:
            return []

        cd_serial_auth = int(songs[-1]['cd_serial']) > 1
        for song in songs:
            self.make_file_name(song, cd_serial_auth=cd_serial_auth)

        songs = [i for i in songs if i['song_id'] == song_id] \
                 if song_id else songs
        return songs

    def get_song(self, song_id):
        song = self._api.song(song_id)

        if not song:
            return []

        self.make_file_name(song)
        return [song]

    def download_song(self):
        songs = self.get_song(self.song_id)
        print(s % (2, 97, u'\n  >> ' + u'1 首歌曲将要下载.')) \
            if not args.play else ''
        #self.song_infos = [song_info]
        self.download(songs)

    def download_songs(self, song_ids):
        for song_id in song_ids:
            self.song_id = song_id
            songs = self.get_song(self.song_id)
            self.download(songs)

    def download_album(self):
        songs = self.get_songs(self.album_id)
        if not songs:
            return

        song = songs[0]

        d = song['album_name'] + ' - ' + song['artist_name']
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)

        amount_songs = unicode(len(songs))
        songs = songs[args.from_ - 1:]
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        self.download(songs, amount_songs, args.from_)

    def download_collect(self):
        page = 1
        song_ids = []
        while True:
            params = {
                'id': self.collect_id,
                'p': page,
                'limit': 50,
            }
            infos = self._request(url_collect, params=params).json()
            for info in infos['result']['data']:
                song_ids.append(str(info['song_id']))

            if infos['result']['total_page'] == page:
                break
            page += 1

        html = self._request('http://www.xiami.com/collect/%s' % self.collect_id).text
        html = html.split('<div id="wall"')[0]
        collect_name = re.search(r'<title>(.+?)<', html).group(1)
        d = collect_name
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        amount_songs = unicode(len(song_ids))
        song_ids = song_ids[args.from_ - 1:]
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        n = args.from_
        for i in song_ids:
            songs = self.get_song(i)
            self.download(songs, amount_songs, n)
            self.html = ''
            self.disc_description_archives = {}
            n += 1

    def download_artist_albums(self):
        ii = 1
        album_ids = []
        while True:
            html = self._request(
                url_artist_albums % (self.artist_id, str(ii))).text
            t = re.findall(r'/album/(\w+)"', html)
            if album_ids == t: break
            album_ids = t
            if album_ids:
                for i in album_ids:
                    print '  ++ http://www.xiami.com/album/%s' % i
                    self.album_id = i
                    self.download_album()
                    self.html = ''
                    self.disc_description_archives = {}
            else:
                break
            ii += 1

    def download_artist_top_20_songs(self):
        html = self._request(url_artist_top_song % self.artist_id).text
        song_ids = re.findall(r'/music/send/id/(\d+)', html)
        artist_name = re.search(
            r'<p><a href="/artist/\w+">(.+?)<', html).group(1)
        d = modificate_text(artist_name + u' - top 20')
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        amount_songs = unicode(len(song_ids))
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        n = 1
        for i in song_ids:
            songs = self.get_song(i)
            self.download(songs, amount_songs, n)
            self.html = ''
            self.disc_description_archives = {}
            n += 1

    def download_artist_radio(self):
        html = self._request(url_artist_top_song % self.artist_id).text
        artist_name = re.search(
            r'<p><a href="/artist/\w+">(.+?)<', html).group(1)
        d = modificate_text(artist_name + u' - radio')
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)

        url_artist_radio = "http://www.xiami.com/radio/xml/type/5/id/%s" \
            % self.artist_id
        n = 1
        while True:
            xml = self._request(url_artist_radio).text
            song_ids = re.findall(r'<song_id>(\d+)', xml)
            for i in song_ids:
                songs = self.get_song(i)
                self.download(songs, n=n)
                self.html = ''
                self.disc_description_archives = {}
                n += 1

    def download_user_songs(self, url, desc):
        dir_ = os.path.join(os.getcwdu(),
            u'虾米用户 %s %s' % (self.user_id, desc))
        self.dir_ = modificate_file_name_for_wget(dir_)
        ii = 1
        n = 1
        while True:
            html = self._request(url % (self.user_id, str(ii))).text
            song_ids = re.findall(r'/song/(.+?)"', html)
            if song_ids:
                for i in song_ids:
                    songs = self.get_song(i)
                    self.download(songs, n)
                    self.html = ''
                    self.disc_description_archives = {}
                    n += 1
            else:
                break
            ii += 1

    def download_user_shares(self, url_shares):
        d = modificate_text(u'%s 的分享' % self.user_id)
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        page = 1
        while True:
            html = self._request(url_shares % page).text
            shares = re.findall(r'play.*\(\'\d+\'\)', html)
            for share in shares:
                if 'album' in share:
                    self.album_id = re.search(r'\d+', share).group()
                    self.download_album()
                else:
                    self.song_id = re.search(r'\d+', share).group()
                    self.download_song()
            if not shares: break
            page += 1

    def download_ranking_songs(self, url, tp):
        d = modificate_text(u'%s 的试听排行 - %s' % (self.user_id, tp))
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        page = 1
        n = 1
        while True:
            html = self._request(url + '/page/' + str(page)).text
            song_ids = re.findall(r"play\('(\d+)'", html)
            if not song_ids:
                break
            for song_id in song_ids:
                songs = self.get_song(song_id)
                self.download(songs, n=n)
                self.html = ''
                self.disc_description_archives = {}
                n += 1
            page += 1

    def download_user_radio(self, url_rndsongs):
        d = modificate_text(u'%s 的虾米推荐' % self.user_id)
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        n = 1
        while True:
            xml = self._request(url_rndsongs % self.user_id).text
            song_ids = re.findall(r'<song_id>(\d+)', xml)
            for i in song_ids:
                songs = self.get_song(i)
                self.download(songs, n=n)
                self.html = ''
                self.disc_description_archives = {}
                n += 1

    def download_chart(self, type_):
        html = self._request('http://www.xiami.com/chart/index/c/%s' \
                      % self.chart_id).text
        title = re.search(r'<title>(.+?)</title>', html).group(1)
        d = modificate_text(title)
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)

        html = self._request(
            'http://www.xiami.com/chart/data?c=%s&limit=200&type=%s' \
            % (self.chart_id, type_)).text
        song_ids = re.findall(r'/song/(\d+)', html)
        n = 1
        for i in song_ids:
            songs = self.get_song(i)
            self.download(songs, n=n)
            self.html = ''
            self.disc_description_archives = {}
            n += 1

    def download_genre(self, url_genre):
        html = self._request(url_genre % (self.genre_id, 1)).text
        if '/gid/' in url_genre:
            t = re.search(
                r'/genre/detail/gid/%s".+?title="(.+?)"' \
                % self.genre_id, html).group(1)
        elif '/sid/' in url_genre:
            t = re.search(
                r'/genre/detail/sid/%s" title="(.+?)"' \
                % self.genre_id, html).group(1)
        d = modificate_text(u'%s - 代表曲目 - xiami' % t)
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)

        n = 1
        page = 2
        while True:
            song_ids = re.findall(r'/song/(\d+)', html)
            if not song_ids: break
            for i in song_ids:
                songs = self.get_song(i)
                self.download(songs, n=n)
                self.html = ''
                self.disc_description_archives = {}
                n += 1
            html = self._request(url_genre % (self.chart_id, page)).text
            page += 1

    def download_genre_radio(self, url_genre):
        html = self._request(url_genre % (self.genre_id, 1)).text
        if '/gid/' in url_genre:
            t = re.search(
                r'/genre/detail/gid/%s".+?title="(.+?)"' \
                % self.genre_id, html).group(1)
            url_genre_radio = "http://www.xiami.com/radio/xml/type/12/id/%s" \
                % self.genre_id
        elif '/sid/' in url_genre:
            t = re.search(
                r'/genre/detail/sid/%s" title="(.+?)"' \
                % self.genre_id, html).group(1)
            url_genre_radio = "http://www.xiami.com/radio/xml/type/13/id/%s" \
                % self.genre_id
        d = modificate_text(u'%s - radio - xiami' % t)
        dir_ = os.path.join(os.getcwdu(), d)
        self.dir_ = modificate_file_name_for_wget(dir_)

        n = 1
        while True:
            xml = self._request(url_genre_radio).text
            song_ids = re.findall(r'<song_id>(\d+)', xml)
            for i in song_ids:
                songs = self.get_song(i)
                self.download(songs, n=n)
                self.html = ''
                self.disc_description_archives = {}
                n += 1

    def hack_luoo(self, url):
        # parse luoo.net
        theaders = headers
        theaders.pop('Referer')
        r = requests.get(url)
        if not r.ok:
            return None
        cn = r.content
        songs_info = re.findall(r'<p class="name">(.+?)</p>\s+'
                                r'<p class="artist">(?:Artist:|艺人：)(.+?)</p>\s+'
                                r'<p class="album">(?:Album:|专辑：)(.+?)</p>', cn)

        # search song at xiami
        for name, artist, album in songs_info:
            name = name.strip()
            artist = artist.strip()
            album = album.strip()

            songs = self._api.search_songs(name + ' ' + artist)
            if not songs:
                print s % (1, 93, '  !! no find:'), ' - '.join([name, artist, album])
                continue

            self.make_file_name(songs[0])
            self.download(songs[:1], n=1)

    def display_infos(self, i, nn, n, durl):
        length = datetime.datetime.fromtimestamp(i['length']).strftime('%M:%S')
        print n, '/', nn
        print s % (2, 94, i['file_name'])
        print s % (2, 95, i['album_name'])
        print s % (2, 93, length)
        print 'http://www.xiami.com/song/%s' % i['song_id']
        print 'http://www.xiami.com/album/%s' % i['album_id']
        print durl
        if i['durl_is_H'] == 'h':
            print s % (1, 97, 'MP3-Quality:'), s % (1, 92, 'High')
        else:
            print s % (1, 97, 'MP3-Quality:'), s % (1, 91, 'Low')
        print '—' * int(os.popen('tput cols').read())

    def get_mp3_quality(self, durl):
        if 'm3.file.xiami.com' in durl \
                or 'm6.file.xiami.com' in durl \
                or '_h.mp3' in durl \
                or 'm320.xiami.net' in durl:
            return 'h'
        else:
            return 'l'

    def play(self, songs, nn=u'1', n=1):
        if args.play == 2:
            songs = sorted(songs, key=lambda k: k['play_count'], reverse=True)

        for i in songs:
            self.record(i['song_id'], i['album_id'])
            durl = self.get_durl(i['song_id'])
            if not durl:
                print s % (2, 91, '  !! Error: can\'t get durl'), i['song_name']
                continue

            cookies = '; '.join(['%s=%s' % (k, v) for k, v in ss.cookies.items()])
            mp3_quality = self.get_mp3_quality(durl)
            i['durl_is_H'] = mp3_quality
            self.display_infos(i, nn, n, durl)
            n = int(n) + 1
            cmd = 'mpv --really-quiet ' \
                '--cache 8146 ' \
                '--user-agent "%s" ' \
                '--http-header-fields "Referer: http://img.xiami.com' \
                '/static/swf/seiya/1.4/player.swf?v=%s",' \
                '"Cookie: %s" ' \
                '"%s"' \
                % (headers['User-Agent'], int(time.time()*1000), cookies, durl)
            os.system(cmd)
            timeout = 1
            ii, _, _ = select.select([sys.stdin], [], [], timeout)
            if ii:
                sys.exit(0)
            else:
                pass

    def download(self, songs, amount_songs=u'1', n=1):
        dir_ = modificate_file_name_for_wget(self.dir_)
        cwd = os.getcwd()
        if dir_ != cwd:
            if not os.path.exists(dir_):
                os.mkdir(dir_)


        ii = 1
        for i in songs:
            num = random.randint(0, 100) % 8
            col = s % (2, num + 90, i['file_name'])
            t = modificate_file_name_for_wget(i['file_name'])
            file_name = os.path.join(dir_, t)
            if os.path.exists(file_name):  ## if file exists, no get_durl
                if args.undownload:
                    self.modified_id3(file_name, i)
                    ii += 1
                    n += 1
                    continue
                else:
                    ii += 1
                    n += 1
                    continue

            if not args.undownload:
                if n == None:
                    print(u'\n  ++ download: #%s/%s# %s' \
                        % (ii, amount_songs, col))
                else:
                    print(u'\n  ++ download: #%s/%s# %s' \
                        % (n, amount_songs, col))
                    n += 1

                durl = self.get_durl(i['song_id'])
                if not durl:
                    print s % (2, 91, '  |-- Error: can\'t get durl')
                    continue

                mp3_quality = self.get_mp3_quality(durl)
                if mp3_quality == 'h':
                    print '  |--', s % (1, 97, 'MP3-Quality:'), s % (1, 91, 'High')
                else:
                    print '  |--', s % (1, 97, 'MP3-Quality:'), s % (1, 91, 'Low')

                cookies = '; '.join(['%s=%s' % (k, v) for k, v in ss.cookies.items()])
                file_name_for_wget = file_name.replace('`', '\`')
                quiet = ' -q' if args.quiet else ' -nv'
                cmd = 'wget -c%s ' \
                    '-U "%s" ' \
                    '--header "Referer:http://img.xiami.com' \
                    '/static/swf/seiya/1.4/player.swf?v=%s" ' \
                    '--header "Cookie: member_auth=%s" ' \
                    '-O "%s.tmp" %s' \
                    % (quiet, headers['User-Agent'], int(time.time()*1000), cookies, file_name_for_wget, durl)
                cmd = cmd.encode('utf8')
                status = os.system(cmd)
                if status != 0:     # other http-errors, such as 302.
                    wget_exit_status_info = wget_es[status]
                    print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> \x1b[1;91m%d ' \
                        '(%s)\x1b[0m   ###--- \n\n' % (status, wget_exit_status_info))
                    print s % (1, 91, '  ===> '), cmd
                    sys.exit(1)
                else:
                    os.rename('%s.tmp' % file_name, file_name)

            self.modified_id3(file_name, i)
            ii += 1
            time.sleep(5)

    def _save_do(self, id_, type, tags):
        data = {
            "tags": tags,
            "type": type,
            "id": id_,
            "desc": "",
            "grade": "",
            "share": 0,
            "shareTo": "all",
            "_xiamitoken": ss.cookies['_xiamitoken'],
        }
        url = 'https://www.xiami.com/ajax/addtag'
        r = self._request(url, data=data, method='POST')
        j = r.json()
        if j['status'] == 'ok':
            return 0
        else:
            return j['status']

    def save(self, urls):
        tags = args.tags
        for url in urls:
            if '/collect/' in url:
                collect_id = re.search(r'/collect/(\w+)', url).group(1)
                print s % (1, 97, u'\n  ++ save collect:'), \
                    'http://www.xiami.com/song/collect/' + collect_id
                result = self._save_do(collect_id, 4, tags)

            elif '/album/' in url:
                album_id = re.search(r'/album/(\w+)', url).group(1)
                album = self._api.album(album_id)
                album_id = album[0].album_id
                print s % (1, 97, u'\n  ++ save album:'), \
                    'http://www.xiami.com/album/' + str(album_id)
                result = self._save_do(album_id, 5, tags)

            elif '/artist/' in url:
                artist_id = re.search(r'/artist/(\w+)', url).group(1)
                print s % (1, 97, u'\n  ++ save artist:'), \
                    'http://www.xiami.com/artist/' + artist_id
                result = self._save_do(artist_id, 6, tags)

            elif '/song/' in url:
                song_id = re.search(r'/song/(\w+)', url).group(1)
                song = self._api.song(song_id)
                song_id = song.song_id
                print s % (1, 97, u'\n  ++ save song:'), \
                    'http://www.xiami.com/song/' + str(song_id)
                result = self._save_do(song_id, 3, tags)

            elif '/u/' in url:
                user_id = re.search(r'/u/(\d+)', url).group(1)
                print s % (1, 97, u'\n  ++ save user:'), \
                    'http://www.xiami.com/u/' + user_id
                result = self._save_do(user_id, 1, tags)

            else:
                result = -1
                print(s % (2, 91, u'   请正确输入虾米网址.'))

            if result == 0:
                print s % (1, 92, '  ++ success.\n')
            else:
                print s % (1, 91, '  !! Error at _save_do.'), result, '\n'

def main(argv):
    if len(argv) < 2:
        sys.exit()

    ######################################################
    # for argparse
    p = argparse.ArgumentParser(description='downloading any xiami.com')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-p', '--play', action='count', \
        help='play with mpv')
    p.add_argument('-l', '--low', action='store_true', \
        help='low mp3')
    p.add_argument('-q', '--quiet', action='store_true', \
        help='quiet for download')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    p.add_argument('-d', '--undescription', action='store_true', \
        help='no add disk\'s distribution')
    p.add_argument('-t', '--tags', action='store', \
        type=str, default='', help='tags. eg: piano,cello')
    p.add_argument('-n', '--undownload', action='store_true', \
        help='no download, using to renew id3 tags')
    global args
    args = p.parse_args(argv[2:])
    comd = argv[1]
    xxx = args.xxx

    if comd == 'login' or comd == 'g':
        # or comd == 'logintaobao' or comd == 'gt':
        # taobao has updated login algorithms which is hard to hack
        # so remove it.
        if len(xxx) < 1:
            email = raw_input(s % (1, 97, '  username: ') \
                if comd == 'logintaobao' or comd == 'gt' \
                else s % (1, 97, '     email: '))
            cookies = getpass(s % (1, 97, '  cookies: '))
        elif len(xxx) == 1:
            # for add_member_auth
            if '; ' in xxx[0]:
                email = None
                cookies = xxx[0]
            else:
                email = xxx[0]
                cookies = getpass(s % (1, 97, '  cookies: '))
        elif len(xxx) == 2:
            email = xxx[0]
            cookies = xxx[1]
        else:
            msg = ('login: \n'
                   'login cookies')
            print s % (1, 91, msg)
            return

        x = xiami()
        x.add_cookies(cookies)
        is_signin = x.check_login()
        if is_signin:
            print s % (1, 92, '  ++ login succeeds.')
        else:
            print s % (1, 91, '  login failes')

    elif comd == 'signout':
        g = open(cookie_file, 'w')
        g.close()

    elif comd == 'd' or comd == 'download':
        urls = xxx
        x = xiami()
        x.init()
        x.url_parser(urls)

    elif comd == 'p' or comd == 'play':
        if not args.play: args.play = 1
        urls = xxx
        x = xiami()
        x.init()
        x.url_parser(urls)

    elif comd == 's' or comd == 'save':
        urls = xxx
        x = xiami()
        x.init()
        x.save(urls)

    else:
        print s % (2, 91, u'  !! 命令错误\n')

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
