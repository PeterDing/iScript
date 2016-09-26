#!/usr/bin/env python2
# vim: set fileencoding=utf8

import re
import sys
import os
import random
import time
import json
import argparse
import urllib
import requests
import select
import md5
from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,APIC,TDRC,COMM,TPOS,USLT
from HTMLParser import HTMLParser

parser = HTMLParser()
s = u'\x1b[%d;%dm%s\x1b[0m'       # terminual color template

############################################################
# music.163.com api
# {{{
url_song = "http://music.163.com/api/song/detail?id=%s&ids=%s"
url_album = "http://music.163.com/api/album/%s"
url_playlist = "http://music.163.com/api/playlist/detail?id=%s&ids=%s"
url_dj = "http://music.163.com/api/dj/program/detail?id=%s&ids=%s"
url_artist_albums = "http://music.163.com\
    /api/artist/albums/%s?offset=0&limit=1000"
url_artist_top_50_songs = "http://music.163.com/artist?id=%s"
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

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://music.163.com/",
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) " \
        "AppleWebKit/537.36 (KHTML, like Gecko) " \
        "Chrome/40.0.2214.91 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

def encrypted_id(id):
    byte1 = bytearray('3go8&$8*3*3h0k(2)2')
    byte2 = bytearray(id)
    byte1_len = len(byte1)
    for i in xrange(len(byte2)):
        byte2[i] = byte2[i]^byte1[i%byte1_len]
    m = md5.new()
    m.update(byte2)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result

def modificate_text(text):
    text = parser.unescape(text)
    text = re.sub(r'//*', '-', text)
    text = text.replace('/', '-')
    text = text.replace('\\', '-')
    text = re.sub(r'\s\s+', ' ', text)
    return text

# for FAT file system
def modificate_file_name_for_wget(file_name):
    file_name = re.sub(r'\s*:\s*', u' - ', file_name)
    file_name = file_name.replace('?', '')
    file_name = file_name.replace('"', '\'')
    return file_name

def z_index(size):
    z = len(str(size))
    return z

########################################################

class neteaseMusic(object):
    def __init__(self, url):
        self.url = url
        self.song_infos = []
        self.dir_ = os.getcwd().decode('utf8')

        self.playlist_id = ''
        self.dj_id = ''
        self.album_id = ''
        self.artist_id = ''
        self.song_id = ''
        self.cover_id = ''
        self.cover_data = ''
        self.amount_songs = u'1'

        self.download = self.play if args.play else self.download

    def get_durl(self, i):
        for q in ('hMusic', 'mMusic', 'lMusic'):
            if i[q]:
                dfsId = str(i[q]['dfsId'])
                edfsId = encrypted_id(dfsId)
                durl = u'http://p1.music.126.net/%s/%s.mp3' \
                    % (edfsId, dfsId)
                return durl, q[0]
        return None, None

    def get_cover(self, info):
        if info['album_name'] == self.cover_id:
            return self.cover_data
        else:
            self.cover_id = info['album_name']
            while True:
                url = info['album_pic_url']
                try:
                    self.cover_data = requests.get(url).content
                    if self.cover_data[:5] != '<?xml':
                        return self.cover_data
                except Exception as e:
                    print s % (1, 91, '   \\\n   \\-- Error, get_cover --'), e
                    time.sleep(5)

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
        #id3.add(TCON(encoding=3, text=u'genres'))
        #id3.add(TSST(encoding=3, text=info['sub_title']))
        #id3.add(TSRC(encoding=3, text=info['disc_code']))
        id3.add(COMM(encoding=3, desc=u'Comment', \
            text=info['song_url']))
        #id3.add(APIC(encoding=3, mime=u'image/jpg', type=3, \
            #desc=u'Front Cover', data=self.get_cover(info)))
        id3.save(file_name)

    def url_parser(self):
        if 'playlist' in self.url:
            self.playlist_id = re.search(
                r'playlist.+?(\d+)', self.url).group(1)
            print(s % (2, 92, u'\n  -- 正在分析歌单信息 ...'))
            self.download_playlist()
        elif 'toplist' in self.url:
            t = re.search(r'toplist.+?(\d+)', self.url)
            if t:
                self.playlist_id = t.group(1)
            else:
                self.playlist_id = '3779629'
            print(s % (2, 92, u'\n  -- 正在分析排行榜信息 ...'))
            self.download_playlist()
        elif 'album' in self.url:
            self.album_id = re.search(
                r'album.+?(\d+)', self.url).group(1)
            print(s % (2, 92, u'\n  -- 正在分析专辑信息 ...'))
            self.download_album()
        elif 'artist' in self.url:
            self.artist_id = re.search(
                r'artist.+?(\d+)', self.url).group(1)
            code = raw_input('\n  >> 输入 a 下载该艺术家所有专辑.\n' \
                '  >> 输入 t 下载该艺术家 Top 50 歌曲.\n  >> ')
            if code == 'a':
                print(s % (2, 92, u'\n  -- 正在分析艺术家专辑信息 ...'))
                self.download_artist_albums()
            elif code == 't':
                print(s % (2, 92, u'\n  -- 正在分析艺术家 Top 50 信息 ...'))
                self.download_artist_top_50_songs()
            else:
                print(s % (1, 92, u'  --> Over'))
        elif 'song' in self.url:
            self.song_id = re.search(
                r'song.+?(\d+)', self.url).group(1)
            print(s % (2, 92, u'\n  -- 正在分析歌曲信息 ...'))
            self.download_song()
        elif 'djradio' in self.url:
            self.djradio_id = re.search(
                r'id=(\d+)', self.url).group(1)
            print(s % (2, 92, u'\n  -- 正在分析DJ节目信息 ...'))
            self.download_djradio()
        elif 'program' in self.url:
            self.dj_id = re.search(
                r'id=(\d+)', self.url).group(1)
            print(s % (2, 92, u'\n  -- 正在分析DJ节目信息 ...'))
            self.download_dj()
        else:
            print(s % (2, 91, u'   请正确输入music.163.com网址.'))

    def get_song_info(self, i):
        z = z_index(i['album']['size']) \
            if i['album'].get('size') else 1
        song_info = {}
        song_info['song_id'] = i['id']
        song_info['song_url'] = u'http://music.163.com/song/%s' \
            % i['id']
        song_info['track'] = str(i['position'])
        song_info['durl'], song_info['mp3_quality'] = self.get_durl(i)
        #song_info['album_description'] = album_description
        #song_info['lyric_url'] = i['lyric']
        #song_info['sub_title'] = i['sub_title']
        #song_info['composer'] = i['composer']
        #song_info['disc_code'] = i['disc_code']
        #if not song_info['sub_title']: song_info['sub_title'] = u''
        #if not song_info['composer']: song_info['composer'] = u''
        #if not song_info['disc_code']: song_info['disc_code'] = u''
        t = time.gmtime(int(i['album']['publishTime'])*0.001)
        #song_info['year'] = unicode('-'.join([str(t.tm_year), \
            #str(t.tm_mon), str(t.tm_mday)]))
        song_info['year'] = unicode('-'.join(
            [str(t.tm_year), str(t.tm_mon), str(t.tm_mday)]
        ))
        song_info['song_name'] = modificate_text(i['name']).strip()
        song_info['artist_name'] = modificate_text(i['artists'][0]['name'])
        song_info['album_pic_url'] = i['album']['picUrl']
        song_info['cd_serial'] = u'1'
        song_info['album_name'] = modificate_text(i['album']['name'])
        file_name = song_info[ 'track'].zfill(z) \
            + '.' + song_info['song_name'] \
            + ' - ' + song_info['artist_name'] \
            + '.mp3'
        song_info['file_name'] = file_name
        # song_info['low_mp3'] = i['mp3Url']
        return song_info

    def get_song_infos(self, songs):
        for i in songs:
            song_info = self.get_song_info(i)
            self.song_infos.append(song_info)

    def download_song(self, noprint=False, n=1):
        j = ss.get(
            url_song % (
                self.song_id, urllib.quote('[%s]' % self.song_id)
            )
        ).json()
        songs = j['songs']
        if not noprint:
            print(s % (2, 97, u'\n  >> ' + u'1 首歌曲将要下载.')) \
                if not args.play else ''
        self.get_song_infos(songs)
        self.download(self.amount_songs, n)

    def download_album(self):
        j = ss.get(url_album % (self.album_id)).json()
        songs = j['album']['songs']
        d = modificate_text(
            j['album']['name'] \
            + ' - ' + j['album']['artist']['name'])
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        self.amount_songs = unicode(len(songs))
        print(s % (2, 97, \
                   u'\n  >> ' + self.amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        self.get_song_infos(songs)
        self.download(self.amount_songs)

    def download_playlist(self):
        j = ss.get(
            url_playlist % (
                self.playlist_id, urllib.quote('[%s]' % self.playlist_id)
            )
        ).json()
        songs = j['result']['tracks']
        d = modificate_text(
            j['result']['name'] + ' - ' \
            + j['result']['creator']['nickname'])
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        self.amount_songs = unicode(len(songs))
        print(s % (2, 97, u'\n  >> ' \
                   + self.amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        self.get_song_infos(songs)
        self.download(self.amount_songs)

    def download_djradio(self):
        html = ss.get(
            'http://music.163.com/djradio?id=%s' \
            % self.djradio_id).content
        dj_ids = re.findall(r'/program\?id=(\d+)', html)

        for dj_id in dj_ids:
            self.dj_id = dj_id
            self.download_dj()
            self.song_infos = []

    def download_dj(self):
        j = ss.get(
            url_dj % (
                self.dj_id, urllib.quote('[%s]' % self.dj_id)
            )
        ).json()
        songs = j['program']['songs']
        d = modificate_text(
            j['program']['name'] + ' - ' \
            + j['program']['dj']['nickname'])
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        self.amount_songs = unicode(len(songs))
        print(s % (2, 97, u'\n  >> \
                   ' + self.amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else None
        self.get_song_infos(songs)
        self.download(self.amount_songs)


    def download_artist_albums(self):
        ss.cookies.update({'appver': '1.5.2'})
        j = ss.get(
            url_artist_albums % self.artist_id).json()
        for albuminfo in j['hotAlbums']:
            self.album_id = albuminfo['id']
            self.download_album()

    def download_artist_top_50_songs(self):
        html = ss.get(
            url_artist_top_50_songs % self.artist_id).content
        text = re.search(
            r'<textarea style="display:none;">(.+?)</textarea>', html).group(1)
        j = json.loads(text)
        songids = [i['id'] for i in j]
        d = modificate_text(
            j[0]['artists'][0]['name'] + ' - ' + 'Top 50')
        dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.dir_ = modificate_file_name_for_wget(dir_)
        self.amount_songs = unicode(len(songids))
        print(s % (2, 97, u'\n  >> \
                   ' + self.amount_songs + u' 首歌曲将要下载.')) \
            if not args.play else ''
        n = 1
        for sid in songids:
            self.song_id = sid
            self.song_infos = []
            self.download_song(noprint=True, n=n)
            n += 1

    def display_infos(self, i):
        q = {'h': 'High', 'm': 'Middle', 'l': 'Low'}
        print '\n  ----------------'
        print '  >>', s % (2, 94, i['file_name'])
        print '  >>', s % (2, 95, i['album_name'])
        print '  >>', s % (2, 92, 'http://music.163.com/song/%s' \
                           % i['song_id'])
        print '  >>', s % (2, 97, 'MP3-Quality'), ':', \
            s % (1, 92, str(q.get(i['mp3_quality'])))
        print ''

    def play(self, amount_songs, n=None):
        for i in self.song_infos:
            self.display_infos(i)
            if not i['durl']:
                continue
            cmd = 'mpv --really-quiet --audio-display no %s' % i['durl']
            os.system(cmd)
            timeout = 1
            ii, _, _ = select.select([sys.stdin], [], [], timeout)
            if ii:
                sys.exit(0)
            else:
                pass

    def download(self, amount_songs, n=None):
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
            if os.path.exists(file_name):  # if file exists, no get_durl
                if args.undownload:
                    self.modified_id3(file_name, i)
                    ii += 1
                    continue
                else:
                    ii += 1
                    continue
            if not args.undownload:
                q = {'h': 'High', 'm': 'Middle', 'l': 'Low'}
                mp3_quality = str(q.get(i['mp3_quality']))
                if n == None:
                    print(u'\n  ++ 正在下载: #%s/%s# %s\n' \
                          u'  ++ mp3_quality: %s' \
                        % (ii, amount_songs, col,
                           s % (1, 91, mp3_quality)))
                else:
                    print(u'\n  ++ 正在下载: #%s/%s# %s\n' \
                          u'  ++ mp3_quality: %s' \
                        % (n, amount_songs, col,
                           s % (1, 91, mp3_quality)))
                if not i['durl']:
                    continue

                file_name_for_wget = file_name.replace('`', '\`')
                cmd = 'wget -c -nv -U "%s" -O "%s.tmp" %s' \
                    % (headers['User-Agent'], file_name_for_wget, i['durl'])
                cmd = cmd.encode('utf8')
                status = os.system(cmd)
                if status != 0:     # other http-errors, such as 302.
                    wget_exit_status_info = wget_es[status]
                    print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> \x1b[1;91m%d ' \
                        '(%s)\x1b[0m   ###--- \n\n' \
                          % (status, wget_exit_status_info))
                    print s % (1, 91, '  ===> '), cmd
                    sys.exit(1)
                else:
                    os.rename('%s.tmp' % file_name, file_name)

            self.modified_id3(file_name, i)
            ii += 1
            time.sleep(0)

def main(url):
    x = neteaseMusic(url)
    x.url_parser()

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='downloading any music.163.com')
    p.add_argument('url', help='any url of music.163.com')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-c', '--undownload', action='store_true', \
        help='no download, using to renew id3 tags')
    args = p.parse_args()
    main(args.url)
