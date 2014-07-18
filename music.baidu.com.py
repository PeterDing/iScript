#!/usr/bin/env python2
# vim: set fileencoding=utf8

import re
import sys
import os
import random
import time
import json
import urllib2
import argparse
import select

from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,APIC,TDRC,COMM,TCOM,TCON,TSST,WXXX,TSRC
from HTMLParser import HTMLParser
parser = HTMLParser()
s = u'\x1b[%d;%dm%s\x1b[0m'       # terminual color template

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; \
        q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://www.baidu.com/",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

############################################################
# wget exit status
wget_es = {
    0:"No problems occurred.",
    2:"User interference.",
    1<<8:"Generic error code.",
    2<<8:"Parse error - for instance, when parsing command-line \
        optio.wgetrc or .netrc...",
    3<<8:"File I/O error.",
    4<<8:"Network failure.",
    5<<8:"SSL verification failure.",
    6<<8:"Username/password authentication failure.",
    7<<8:"Protocol errors.",
    8<<8:"Server issued an error response."
}
############################################################

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

class baidu_music(object):
    def __init__(self, url):
        self.url = url
        self.song_infos = []
        self.json_url = ''
        self.dir_ = os.getcwd().decode('utf8')
        self.template_wgets = 'wget -nv -U "%s" -O "%s.tmp" %s' % (headers['User-Agent'], '%s', '%s')
        self.template_album = 'http://music.baidu.com/album/%s'
        if args.flac:
            self.template_api = 'http://music.baidu.com/data/music/fmlink?songIds=%s&type=flac'
        elif args.low:
            self.template_api = 'http://music.baidu.com/data/music/fmlink?songIds=%s&type=mp3'
        elif args.high:
            self.template_api = 'http://music.baidu.com/data/music/fmlink?songIds=%s&type=mp3&rate=320'
        else:
            self.template_api = 'http://music.baidu.com/data/music/fmlink?songIds=%s&type=mp3&rate=320'

        self.album_id = ''
        self.song_id = ''

        self.download = self.play if args.play else self.download

    def get_songidlist(self, id_):
        html = self.opener.open(self.template_album % id_).read()
        songidlist = re.findall(r'/song/(\d+)', html)
        api_json = self.opener.open(self.template_api % ','.join(songidlist)).read()
        api_json = json.loads(api_json)
        infos = api_json['data']['songList']
        return infos

    def get_cover(self, url):
        i = 1
        while True:
            cover_data = self.opener.open(url).read()
            if cover_data[:5] != '<?xml':
                return cover_data
            if i >= 10:
                print s % (1, 91, "  |--> Error: can't get cover image")
                sys.exit(0)
            i += 1

    def modified_id3(self, file_name, info):
        id3 = ID3()
        id3.add(TRCK(encoding=3, text=info['track']))
        id3.add(TIT2(encoding=3, text=info['song_name']))
        id3.add(TALB(encoding=3, text=info['album_name']))
        id3.add(TPE1(encoding=3, text=info['artist_name']))
        id3.add(COMM(encoding=3, desc=u'Comment', text=info['song_url']))
        id3.add(APIC(encoding=3, mime=u'image/jpg', type=3, desc=u'Cover', data=self.get_cover(info['album_pic_url'])))
        id3.save(file_name)

    def url_parser(self):
        if '/album/' in self.url:
            self.album_id = re.search(r'/album/(\d+)', self.url).group(1)
            #print(s % (2, 92, u'\n  -- 正在分析专辑信息 ...'))
            self.get_album_infos()
        elif '/song/' in self.url:
            self.song_id = re.search(r'/song/(\d+)', self.url).group(1)
            #print(s % (2, 92, u'\n  -- 正在分析歌曲信息 ...'))
            self.get_song_infos()
        else:
            print(s % (2, 91, u'   请正确输入baidu网址.'))

    def get_song_infos(self):
        api_json = self.opener.open(self.template_api % self.song_id).read()
        j = json.loads(api_json)
        song_info = {}
        song_info['song_id'] = unicode(j['data']['songList'][0]['songId'])
        song_info['track'] = u''
        song_info['song_url'] = u'http://music.baidu.com/song/' + song_info['song_id']
        song_info['song_name'] = modificate_text(j['data']['songList'][0]['songName']).strip()
        song_info['album_name'] = modificate_text(j['data']['songList'][0]['albumName']).strip()
        song_info['artist_name'] = modificate_text(j['data']['songList'][0]['artistName']).strip()
        song_info['album_pic_url'] = j['data']['songList'][0]['songPicRadio']
        if args.flac:
            song_info['file_name'] = song_info['song_name'] + ' - ' + song_info['artist_name'] + '.flac'
        else:
            song_info['file_name'] = song_info['song_name'] + ' - ' + song_info['artist_name'] + '.mp3'
        song_info['durl'] = j['data']['songList'][0]['songLink']
        self.song_infos.append(song_info)
        self.download()

    def get_album_infos(self):
        songidlist = self.get_songidlist(self.album_id)
        z = z_index(songidlist)
        ii = 1
        for i in songidlist:
            song_info = {}
            song_info['song_id'] = unicode(i['songId'])
            song_info['song_url'] = u'http://music.baidu.com/song/' + song_info['song_id']
            song_info['track'] = unicode(ii)
            song_info['song_name'] = modificate_text(i['songName']).strip()
            song_info['artist_name'] = modificate_text(i['artistName']).strip()
            song_info['album_pic_url'] = i['songPicRadio']
            if args.flac:
                song_info['file_name'] = song_info['track'].zfill(z) + '.' + song_info['song_name'] + ' - ' + song_info['artist_name'] + '.flac'
            else:
                song_info['file_name'] = song_info['track'].zfill(z) + '.' + song_info['song_name'] + ' - ' + song_info['artist_name'] + '.mp3'
            song_info['album_name'] = modificate_text(i['albumName']).strip() \
                if i['albumName'] else modificate_text(self.song_infos[0]['album_name'])
            song_info['durl'] = i['songLink']
            self.song_infos.append(song_info)
            ii += 1
        d = modificate_text(self.song_infos[0]['album_name'] + ' - ' + self.song_infos[0]['artist_name'])
        self.dir_ = os.path.join(os.getcwd().decode('utf8'), d)
        self.download()

    def display_infos(self, i):
        print '\n  ----------------'
        print '  >>', s % (2, 94, i['file_name'])
        print '  >>', s % (2, 95, i['album_name'])
        print '  >>', s % (2, 92, 'http://music.baidu.com/song/%s' % i['song_id'])
        print ''

    def play(self):
        for i in self.song_infos:
            durl = i['durl']
            self.display_infos(i)
            os.system('mpv --really-quiet %s' % durl)
            timeout = 1
            ii, _, _ = select.select([sys.stdin], [], [], timeout)
            if ii:
                sys.exit(0)
            else:
                pass

    def download(self):
        dir_ = modificate_file_name_for_wget(self.dir_)
        cwd = os.getcwd().decode('utf8')
        csongs = len(self.song_infos)
        if dir_ != cwd:
            if not os.path.exists(dir_):
                os.mkdir(dir_)
        print(s % (2, 97, u'\n  >> ' + str(csongs) + u' 首歌曲将要下载.'))
        ii = 1
        for i in self.song_infos:
            t = modificate_file_name_for_wget(i['file_name'])
            file_name = os.path.join(dir_, t)
            if os.path.exists(file_name):  ## if file exists, no get_durl
                ii += 1
                continue
            file_name_for_wget = file_name.replace('`', '\`')
            if 'zhangmenshiting.baidu.com' in i['durl'] or \
                'yinyueshiting.baidu.com' in i['durl']:
                num = random.randint(0,100) % 7
                col = s % (2, num + 90, i['file_name'])
                print(u'\n  ++ 正在下载: %s' % col)
                wget = self.template_wgets % (file_name_for_wget, i['durl'])
                wget = wget.encode('utf8')
                status = os.system(wget)
                if status != 0:     # other http-errors, such as 302.
                    wget_exit_status_info = wget_es[status]
                    print('\n\n ----### \x1b[1;91mERROR\x1b[0m ==> \x1b[1;91m%d (%s)\x1b[0m ###--- \n\n' % (status, wget_exit_status_info))
                    print('  ===> ' + wget)
                    break
                else:
                    os.rename('%s.tmp' % file_name, file_name)

                self.modified_id3(file_name, i)
                ii += 1
                #time.sleep(10)
            else:
                print s % (1, 91, '  !! Oops, you are unlucky, the song is not from zhangmenshiting.baidu.com')
                print i['durl']

def main(url):
    x = baidu_music(url)
    opener = urllib2.build_opener()
    opener.addheaders = headers.items()
    x.opener = opener
    x.url_parser()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='downloading any music.baidu.com')
    p.add_argument('url', help='any url of music.baidu.com')
    p.add_argument('-f', '--flac', action='store_true', help='download flac')
    p.add_argument('-i', '--high', action='store_true', help='download 320')
    p.add_argument('-l', '--low', action='store_true', help='download 128')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    args = p.parse_args()
    main(args.url)
