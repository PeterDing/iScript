#!/usr/bin/env python2
# vim: set fileencoding=utf8

import re
import sys
from getpass import getpass
import os
import random
import time
import json
import argparse
import requests
import urllib
import select
from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,APIC,TDRC,COMM,TPOS,USLT
from HTMLParser import HTMLParser

#############################################################
# Xiami api for android
#{{{
# url_action_fav = "http://www.xiami.com/app/android/fav?id=%s&type=%s"
# url_action_unfav = "http://www.xiami.com/app/android/unfav?id=%s&type=%s"
# url_album = "http://www.xiami.com/app/android/album?id=%s&uid=%s"
# url_song = "http://www.xiami.com/app/android/song?id=%s&uid=%s"
# url_artist = "http://www.xiami.com/app/android/artist?id=%s"
# url_artist_albums = "http://www.xiami.com/app/android/artist-albums?id=%s&page=%s"
# url_artist_radio = "http://www.xiami.com/app/android/radio-artist?id=%s"
# url_artist_top_song = "http://www.xiami.com/app/android/artist-topsongs?id=%s"
# url_artsit_similars = "http://www.xiami.com/app/android/artist-similar?id=%s"
# url_collect = "http://www.xiami.com/app/android/collect?id=%s&uid=%s"
# url_grade = "http://www.xiami.com/app/android/grade?id=%s&grade=%s"
# url_lib_albums = "http://www.xiami.com/app/android/lib-albums?uid=%s&page=%s"
# url_lib_artists = "http://www.xiami.com/app/android/lib-artists?uid=%s&page=%s"
# url_lib_collects = "http://www.xiami.com/app/android/lib-collects?uid=%s&page=%s"
# url_lib_songs = "http://www.xiami.com/app/android/lib-songs?uid=%s&page=%s"
# url_myplaylist = "http://www.xiami.com/app/android/myplaylist?uid=%s"
# url_myradiosongs = "http://www.xiami.com/app/android/lib-rnd?uid=%s"
# url_playlog = "http://www.xiami.com/app/android/playlog?id=%s&uid=%s"
# url_push_songs = "http://www.xiami.com/app/android/push-songs?uid=%s&deviceid=%s"
# url_radio = "http://www.xiami.com/app/android/radio?id=%s&uid=%s"
# url_radio_categories = "http://www.xiami.com/app/android/radio-category"
# url_radio_similar = "http://www.xiami.com/app/android/radio-similar?id=%s&uid=%s"
# url_rndsongs = "http://www.xiami.com/app/android/rnd?uid=%s"
# url_search_all = "http://www.xiami.com/app/android/searchv1?key=%s"
# url_search_parts = "http://www.xiami.com/app/android/search-part?key=%s&type=%s&page=%s"
#}}}
#############################################################

############################################################
# Xiami api for android
# {{{
url_song = "http://www.xiami.com/app/android/song?id=%s"
url_album = "http://www.xiami.com/app/android/album?id=%s"
url_collect = "http://www.xiami.com/app/android/collect?id=%s"
url_artist_albums = "http://www.xiami.com/app/android/artist-albums?id=%s&page=%s"
url_artist_top_song = "http://www.xiami.com/app/android/artist-topsongs?id=%s"
url_lib_songs = "http://www.xiami.com/app/android/lib-songs?uid=%s&page=%s"
# }}}
############################################################

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
s = u'\x1b[%d;%dm%s\x1b[0m'       # terminual color template

cookie_file = os.path.join(os.path.expanduser('~'), '.Xiami.cookies')

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://www.xiami.com/",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
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
    return text

def modificate_file_name_for_wget(file_name):
    file_name = re.sub(r'\s*:\s*', u' - ', file_name)    # for FAT file system
    file_name = file_name.replace('?', '')      # for FAT file system
    file_name = file_name.replace('"', '\'')    # for FAT file system
    return file_name

def z_index(song_infos):
    size = len(song_infos)
    z = len(str(size))
    return z

########################################################

class xiami(object):
    def __init__(self):
        self.song_infos = []
        self.dir_ = os.getcwd().decode('utf8')
        self.template_wgets = 'wget -c -T 5 -nv -U "%s" -O' \
            % headers['User-Agent'] + ' "%s.tmp" %s'
        self.template_song = 'http://www.xiami.com/song/gethqsong/sid/%s'
        self.template_record = 'http://www.xiami.com/count/playrecord?sid=%s'

        self.showcollect_id = ''
        self.album_id = ''
        self.artist_id = ''
        self.song_id = ''
        self.user_id = ''
        self.cover_id = ''
        self.cover_data = ''

        self.html = ''
        self.disc_description_archives = {}

        self.download = self.play if args.play else self.download

    def init(self):
        if os.path.exists(cookie_file):
            try:
                t = json.loads(open(cookie_file).read())
                ss.cookies.update(t.get('cookies', t))
                if not self.check_login():
                    print s % (1, 91, '  !! cookie is invalid, please login\n')
                    sys.exit(1)
            except:
                g = open(cookie_file, 'w')
                g.close()
                print s % (1, 97, '  please login')
                sys.exit(1)
        else:
            print s % (1, 91, '  !! cookie_file is missing, please login')
            sys.exit(1)

    def check_login(self):
        #print s % (1, 97, '\n  -- check_login')
        url = 'http://www.xiami.com/task/signin'
        r = ss.get(url)
        if r.content:
            #print s % (1, 92, '  -- check_login success\n')
            self.save_cookies()
            return True
        else:
            print s % (1, 91, '  -- login fail, please check email and password\n')
            return False

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

        url = 'http://www.xiami.com/web/login'
        ss.post(url, data=data)
        self.save_cookies()

    def get_validate(self):
        url = 'https://login.xiami.com/coop/checkcode?forlogin=1&%s' \
            % int(time.time())
        path = os.path.join(os.path.expanduser('~'), 'vcode.png')
        with open(path, 'w') as g:
            data = ss.get(url).content
            g.write(data)
        print "  ++ 验证码已经保存至", s % (2, 91, path)
        print s % (2, 92, u'  请输入验证码:')
        validate = raw_input()
        return validate

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            c = {'cookies': ss.cookies.get_dict()}
            g.write(json.dumps(c, indent=4, sort_keys=True))

    def get_durl(self, id_):
        while True:
            try:
                j = ss.get(self.template_song % id_).json()
                t = j['location']
                row = t[0]
                encryed_url = t[1:]
                durl = decry(row, encryed_url)
                return durl
            except Exception as e:
                print s % (1, 91, '   \\\n    \\-- Error, get_durl --'), e
                time.sleep(5)

    def record(self, id_):
        ss.get(self.template_record % id_)

    def get_cover(self, info):
        if info['album_name'] == self.cover_id:
            return self.cover_data
        else:
            self.cover_id = info['album_name']
            while True:
                url = info['album_pic_url']
                try:
                    self.cover_data = ss.get(url).content
                    if self.cover_data[:5] != '<?xml':
                        return self.cover_data
                except Exception as e:
                    print s % (1, 91, '   \\\n   \\-- Error, get_cover --'), e
                    time.sleep(5)

    def get_lyric(self, lyric_url):
        if lyric_url:
            data = ss.get(lyric_url).content
            return data.decode('utf8')
        else:
            return u''

    def get_disc_description(self, album_url, info):
        if not self.html:
            self.html = ss.get(album_url).content
            t = re.findall(re_disc_description, self.html)
            t = dict([(a, modificate_text(parser.unescape(b.decode('utf8')))) for a, b in t])
            self.disc_description_archives = dict(t)
        if self.disc_description_archives.has_key(info['cd_serial']):
            disc_description = self.disc_description_archives[info['cd_serial']]
            return u'(%s)' % disc_description
        else:
            return u''

    def modified_id3(self, file_name, info):
        id3 = ID3()
        id3.add(TRCK(encoding=3, text=info['track']))
        id3.add(TDRC(encoding=3, text=info['year']))
        id3.add(TIT2(encoding=3, text=info['song_name']))
        id3.add(TALB(encoding=3, text=info['album_name']))
        id3.add(TPE1(encoding=3, text=info['artist_name']))
        id3.add(TPOS(encoding=3, text=info['cd_serial']))
        #id3.add(USLT(encoding=3, text=self.get_lyric(info['lyric_url'])))
        #id3.add(TCOM(encoding=3, text=info['composer']))
        #id3.add(WXXX(encoding=3, desc=u'xiami_song_url', text=info['song_url']))
        #id3.add(TCON(encoding=3, text=u'genres'))
        #id3.add(TSST(encoding=3, text=info['sub_title']))
        #id3.add(TSRC(encoding=3, text=info['disc_code']))
        id3.add(COMM(encoding=3, desc=u'Comment', \
            text=u'\n\n'.join([info['song_url'], info['album_description']])))
        id3.add(APIC(encoding=3, mime=u'image/jpeg', type=3, \
            desc=u'Front Cover', data=self.get_cover(info)))
        id3.save(file_name)

    def url_parser(self, urls):
        for url in urls:
            if '/showcollect/' in url:
                self.showcollect_id = re.search(r'/showcollect/id/(\d+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析精选集信息 ...'))
                self.download_collect()
            elif '/album/' in url:
                self.album_id = re.search(r'/album/(\d+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析专辑信息 ...'))
                self.download_album()
            elif '/artist/' in url:
                self.artist_id = re.search(r'/artist/(\d+)', url).group(1)
                code = raw_input('  >> 输入 a 下载该艺术家所有专辑.\n' \
                    '  >> 输入 t 下载该艺术家top 20歌曲.\n  >> ')
                if code == 'a':
                    #print(s % (2, 92, u'\n  -- 正在分析艺术家专辑信息 ...'))
                    self.download_artist_albums()
                elif code == 't':
                    #print(s % (2, 92, u'\n  -- 正在分析艺术家top20信息 ...'))
                    self.download_artist_top_20_songs()
                else:
                    print(s % (1, 92, u'  --> Over'))
            elif '/song/' in url:
                self.song_id = re.search(r'/song/(\d+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析歌曲信息 ...'))
                self.download_song()
            elif '/u/' in url:
                self.user_id = re.search(r'/u/(\d+)', url).group(1)
                #print(s % (2, 92, u'\n  -- 正在分析用户歌曲库信息 ...'))
                self.download_user_songs()
            else:
                print(s % (2, 91, u'   请正确输入虾米网址.'))

    def get_song_info(self, album_description, z, cd_serial_auth, i):
        song_info = {}
        song_info['song_id'] = i['song_id']
        song_info['song_url'] = u'http://www.xiami.com/song/' + i['song_id']
        song_info['track'] = i['track']
        song_info['album_description'] = album_description
        #song_info['lyric_url'] = i['lyric']
        #song_info['sub_title'] = i['sub_title']
        #song_info['composer'] = i['composer']
        #song_info['disc_code'] = i['disc_code']
        #if not song_info['sub_title']: song_info['sub_title'] = u''
        #if not song_info['composer']: song_info['composer'] = u''
        #if not song_info['disc_code']: song_info['disc_code'] = u''
        t = time.gmtime(int(i['gmt_publish']))
        #song_info['year'] = unicode('-'.join([str(t.tm_year), \
            #str(t.tm_mon), str(t.tm_mday)]))
        song_info['year'] = unicode('-'.join([str(t.tm_year), \
            str(t.tm_mon), str(t.tm_mday)]))
        song_info['song_name'] = modificate_text(i['name']).strip()
        song_info['artist_name'] = modificate_text(i['artist_name']).strip()
        song_info['album_pic_url'] = re.sub(r'_\d*\.', '_4.', i['album_logo'])
        song_info['cd_serial'] = i['cd_serial']
        if cd_serial_auth:
            if not args.undescription:
                disc_description = self.get_disc_description(\
                    'http://www.xiami.com/album/%s' % i['album_id'], song_info)
                if u''.join(self.disc_description_archives.values()) != u'':
                    if disc_description:
                        song_info['album_name'] = modificate_text(i['title']).strip() \
                            + ' [Disc-' + song_info['cd_serial'] + '] ' + disc_description
                        file_name = '[Disc-' + song_info['cd_serial'] + '] ' \
                            + disc_description + ' ' + song_info['track'] + '.' \
                            + song_info['song_name'] + ' - ' + song_info['artist_name'] + '.mp3'
                        song_info['file_name'] = file_name
                        #song_info['cd_serial'] = u'1'
                    else:
                        song_info['album_name'] = modificate_text(i['title']).strip() \
                            + ' [Disc-' + song_info['cd_serial'] + ']'
                        file_name = '[Disc-' + song_info['cd_serial'] + '] ' \
                            + song_info['track'] + '.' + song_info['song_name'] \
                            + ' - ' + song_info['artist_name'] + '.mp3'
                        song_info['file_name'] = file_name
                        #song_info['cd_serial'] = u'1'
                else:
                    song_info['album_name'] = modificate_text(i['title']).strip()
                    file_name = '[Disc-' + song_info['cd_serial'] + '] ' \
                        + song_info['track'] + '.' + song_info['song_name'] \
                        + ' - ' + song_info['artist_name'] + '.mp3'
                    song_info['file_name'] = file_name
            else:
                song_info['album_name'] = modificate_text(i['title']).strip()
                file_name = '[Disc-' + song_info['cd_serial'] + '] ' + song_info['track'] \
                    + '.' + song_info['song_name'] + ' - ' + song_info['artist_name'] + '.mp3'
                song_info['file_name'] = file_name

        else:
            song_info['album_name'] = modificate_text(i['title']).strip()
            file_name = song_info['track'].zfill(z) + '.' + song_info['song_name'] \
                + ' - ' + song_info['artist_name'] + '.mp3'
            song_info['file_name'] = file_name
        # song_info['low_mp3'] = i['location']
        return song_info

    def get_song_infos(self, song_id):
        j = ss.get(url_song % song_id).json()
        album_id = j['song']['album_id']
        j = ss.get(url_album % album_id).json()
        t = j['album']['description']
        t = parser.unescape(t)
        t = parser.unescape(t)
        t = re.sub(r'<.+?(http://.+?)".+?>', r'\1', t)
        t = re.sub(r'<.+?>([^\n])', r'\1', t)
        t = re.sub(r'<.+?>(\r\n|)', u'\n', t)
        album_description = re.sub(r'\s\s+', u'\n', t).strip()
        cd_serial_auth = j['album']['songs'][-1]['cd_serial'] > u'1'
        z = 0
        if not cd_serial_auth:
            z = z_index(j['album']['songs'])
        for i in j['album']['songs']:
            if i['song_id'] == song_id:
                song_info = self.get_song_info(album_description, z, cd_serial_auth, i)
                return song_info

    def get_album_infos(self, album_id):
        j = ss.get(url_album % album_id).json()
        t = j['album']['description']
        t = parser.unescape(t)
        t = parser.unescape(t)
        t = re.sub(r'<.+?(http://.+?)".+?>', r'\1', t)
        t = re.sub(r'<.+?>([^\n])', r'\1', t)
        t = re.sub(r'<.+?>(\r\n|)', u'\n', t)
        album_description = re.sub(r'\s\s+', u'\n', t).strip()
        d = modificate_text(j['album']['title'] + ' - ' + j['album']['artist_name'])
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        cd_serial_auth = j['album']['songs'][-1]['cd_serial'] > u'1'
        z = 0
        if not cd_serial_auth:
            z = z_index(j['album']['songs'])
        song_infos = []
        for i in j['album']['songs']:
            song_info = self.get_song_info(album_description, z, cd_serial_auth, i)
            song_infos.append(song_info)
        return song_infos

    def download_song(self):
        song_info = self.get_song_infos(self.song_id)
        print(s % (2, 97, u'\n  >> ' + u'1 首歌曲将要下载.')) \
            if not args.play else ''
        self.song_infos = [song_info]
        self.download()

    def download_album(self):
        self.song_infos = self.get_album_infos(self.album_id)
        amount_songs = unicode(len(self.song_infos))
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        self.download(amount_songs)

    def download_collect(self):
        j = ss.get(url_collect % self.showcollect_id).json()
        d = modificate_text(j['collect']['name'])
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        amount_songs = unicode(len(j['collect']['songs']))
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        n = 1
        for i in j['collect']['songs']:
            song_id = i['song_id']
            song_info = self.get_song_infos(song_id)
            self.song_infos = [song_info]
            self.download(amount_songs, n)
            self.html = ''
            self.disc_description_archives = {}
            n += 1

    def download_artist_albums(self):
        ii = 1
        while True:
            j = ss.get(url_artist_albums % (self.artist_id, str(ii))).json()
            if j['albums']:
                for i in j['albums']:
                    self.album_id = i['album_id']
                    self.download_album()
                    self.html = ''
                    self.disc_description_archives = {}
            else:
                break
            ii += 1

    def download_artist_top_20_songs(self):
        j = ss.get(url_artist_top_song % self.artist_id).json()
        d = modificate_text(j['songs'][0]['artist_name'] + u' - top 20')
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        amount_songs = unicode(len(j['songs']))
        print(s % (2, 97, u'\n  >> ' + amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        n = 1
        for i in j['songs']:
            song_id = i['song_id']
            song_info = self.get_song_infos(song_id)
            self.song_infos = [song_info]
            self.download(amount_songs, n)
            self.html = ''
            self.disc_description_archives = {}
            n += 1

    def download_user_songs(self):
        dir_ = os.path.join(os.getcwd().decode('utf8'), \
            u'虾米用户 %s 收藏的歌曲' % self.user_id)
        self.dir_ = modificate_file_name_for_wget(dir_)
        ii = 1
        n = 1
        while True:
            j = ss.get(url_lib_songs % (self.user_id, str(ii))).json()
            if j['songs']:
                for i in j['songs']:
                    song_id = i['song_id']
                    song_info = self.get_song_infos(song_id)
                    self.song_infos = [song_info]
                    self.download(n)
                    self.html = ''
                    self.disc_description_archives = {}
                    n += 1
            else:
                break
            ii += 1

    def display_infos(self, i):
        print '\n  ----------------'
        print '  >>', s % (2, 94, i['file_name'])
        print '  >>', s % (2, 95, i['album_name'])
        print '  >>', s % (2, 92, 'http://www.xiami.com/song/%s' % i['song_id'])
        if i['durl_is_H']:
            print '  >>', s % (1, 97, '     < High rate >')
        else:
            print '  >>', s % (1, 97, '     < Low rate >')
        print ''

    def get_mp3_quality(self, durl):
        if 'm3.file.xiami.com' in durl or 'm6.file.xiami.com' in durl:
            return True
        else:
            return False

    def play(self, nnn=None, nn=None):
        for i in self.song_infos:
            self.record(i['song_id'])
            durl = self.get_durl(i['song_id'])
            i['durl_is_H'] = 'm3.file' in durl
            self.display_infos(i)
            os.system('mpv --really-quiet %s' % durl)
            timeout = 1
            ii, _, _ = select.select([sys.stdin], [], [], timeout)
            if ii:
                sys.exit(0)
            else:
                pass

    def download(self, amount_songs=u'1', n=None):
        dir_ = modificate_file_name_for_wget(self.dir_)
        cwd = os.getcwd().decode('utf8')
        if dir_ != cwd:
            if not os.path.exists(dir_):
                os.mkdir(dir_)
        ii = 1
        for i in self.song_infos:
            num = random.randint(0, 100) % 7
            col = s % (2, num + 90, i['file_name'])
            t = modificate_file_name_for_wget(i['file_name'])
            file_name = os.path.join(dir_, t)
            if os.path.exists(file_name):  ## if file exists, no get_durl
                if args.undownload:
                    self.modified_id3(file_name, i)
                    ii += 1
                    continue
                else:
                    ii += 1
                    continue
            file_name_for_wget = file_name.replace('`', '\`')
            if not args.undownload:
                durl = self.get_durl(i['song_id'])
                mp3_quality = self.get_mp3_quality(durl)
                if n == None:
                    print(u'\n  ++ 正在下载: #%s/%s# %s' \
                        % (ii, amount_songs, col))
                else:
                    print(u'\n  ++ 正在下载: #%s/%s# %s' \
                        % (n, amount_songs, col))
                if mp3_quality == 'L':
                    print s % (1, 91, ' !!! Warning: '), 'gaining LOW quality mp3 link.'
                wget = self.template_wgets % (file_name_for_wget, durl)
                wget = wget.encode('utf8')
                status = os.system(wget)
                if status != 0:     # other http-errors, such as 302.
                    wget_exit_status_info = wget_es[status]
                    print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> \x1b[1;91m%d ' \
                        '(%s)\x1b[0m   ###--- \n\n' % (status, wget_exit_status_info))
                    print s % (1, 91, '  ===> '), wget
                    sys.exit(1)
                else:
                    os.rename('%s.tmp' % file_name, file_name)

            self.modified_id3(file_name, i)
            ii += 1
            time.sleep(0)

def main(argv):
    if len(argv) <= 2:
        sys.exit()

    ######################################################
    # for argparse
    p = argparse.ArgumentParser(description='downloading any xiami.com')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-d', '--undescription', action='store_true', \
        help='no add disk\'s distribution')
    p.add_argument('-c', '--undownload', action='store_true', \
        help='no download, using to renew id3 tags')
    global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    if xxx[0] == 'login' or xxx[0] == 'g':
        if len(xxx[1:]) < 1:
            email = raw_input(s % (1, 97, '     email: '))
            password = getpass(s % (1, 97, '  password: '))
        elif len(xxx[1:]) == 1:
            email = xxx[1]
            password = getpass(s % (1, 97, '  password: '))
        elif len(xxx[1:]) == 2:
            email = xxx[1]
            password = xxx[2]
        else:
            print s % (1, 91, '  login\n  login email\n  login email password')

        x = xiami()
        x.login(email, password)
        is_signin = x.check_login()
        if is_signin:
            print s % (1, 92, '  ++ login succeeds.')
        else:
            print s % (1, 91, '  login failes')

    elif xxx[0] == 'signout':
        g = open(cookie_file, 'w')
        g.close()

    else:
        urls = xxx
        x = xiami()
        x.init()
        x.url_parser(urls)

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
