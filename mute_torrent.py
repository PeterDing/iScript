#!/usr/bin/env python2
# vim: set fileencoding=utf8

import bencode
import os
import sys
import re
import requests

############################################################
headers = {
    "Connection": "keep-alive",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"gzip,deflate,sdch",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

s = u'\x1b[%d;%dm%s\x1b[0m'       # terminual color template
new_torrents_dir = os.path.join(os.getcwd(), 'new_torrents')

class mute_torrent(object):
    def transfer(self, string, tpath):
        self.dir_dict = {}
        self.sub_dir_index = 0

        dstring = bencode.bdecode(string)
        files = []
        file_index = 0

        ## change files' name
        for fl in dstring['info']['files']:
            filename = fl['path'][-1]
            ext = os.path.splitext(filename)[-1]
            path = [self._get_sub_dir_index(i) for i in fl['path'][:-1]] \
                + ['%s%s' % (file_index, ext)]
            file_index += 1
            #print path
            fl['path'] = path
            files.append(fl)

        ## change top directory
        for i in dstring['info']:
            if 'name' in i:
                dstring['info'][i] = 'tasks'

        ## delete comment and creator
        for i in dstring.keys():
            if 'comment' in i:
                del dstring[i]

            elif 'created by' in i:
                del dstring[i]

        dstring['info']['files'] = files
        c = bencode.bencode(dstring)

        with open(tpath, 'w') as g:
            g.write(c)

    def _get_sub_dir_index(self, dir_):
        if not self.dir_dict.get(dir_):
            self.dir_dict[dir_] = str(self.sub_dir_index)
            self.sub_dir_index += 1
            return self.dir_dict[dir_]
        else:
            return self.dir_dict[dir_]

    def get_torrent(self, hh):
        print s % (1, 93, '  ++ get torrent from web')

        ## first with https://zoink.it
        print s % (1, 94, '  --> try:'), 'https://zoink.it'
        url = 'https://torcache.net/torrent/%s.torrent' % hh
        r = ss.get(url, verify=False)
        if r.ok:
            return r.content
        else:
            print s % (1, 91, '  -- not get.')

        ## 2nd, with https://zoink.it
        print s % (1, 94, '  --> try:'), 'https://torcache.net'
        url = 'https://torcache.net/torrent/%s.torrent' % hh
        r = ss.get(url, verify=False)
        if r.ok:
            return r.content
        else:
            print s % (1, 91, '  -- not get.')

        ## 3rd, with http://www.btspread.com
        print s % (1, 94, '  --> try:'), 'http://www.btspread.com'
        #ss.get('http://www.btspread.com/')
        url = 'http://www.btspread.com/torrent/detail/hash/%s' % hh
        r = ss.get(url)
        if r.ok:
            html = r.content
            durl = re.search(r'"(http://www.btspread.com/torrent/download/key/.+?)"', html).group(1)
            r = ss.get(durl)
            if r.ok and r.content:
                print s % (1, 92, '  ++ get torrent.')
                return r.content
            else:
                print s % (1, 91, '  -- not get.')

        return False

def main(xxx):
    if not os.path.exists(new_torrents_dir):
        os.mkdir(new_torrents_dir)

    x = mute_torrent()

    for path in xxx:
        if path.startswith('magnet:'):
            hh = re.search(r'urn:btih:(\w+)', path)
            if hh:
                hh = hh.group(1).upper()
            else:
                print s % (1, 91, '  !! magnet is wrong.'), path
            string = x.get_torrent(hh)
            if string:
                tpath = os.path.join(new_torrents_dir, hh + '.torrent')
                print s % (1, 97, '  ++ transfer:'), 'magnet:?xt=urn:btih:%s' % hh
                x.transfer(string, tpath)
            else:
                print s % (1, 91, 'Can\'t get torrent from web.'), path

        elif os.path.exists(path):
            if os.path.isdir(path):
                for a, b, c in os.walk(path):
                    for i in c:
                        if os.path.abspath(a) == new_torrents_dir: continue
                        ipath = os.path.join(a, i)
                        if ipath.lower().endswith('torrent'):
                            print s % (1, 97, '  ++ transfer:'), ipath
                            string = open(ipath).read()
                            tpath = os.path.join(new_torrents_dir, i)
                            x.transfer(string, tpath)
            elif os.path.isfile(path):
                if path.lower().endswith('torrent'):
                    print s % (2, 97, '  ++ transfer:'), path
                    string = open(path).read()
                    tpath = os.path.join(new_torrents_dir, os.path.basename(path))
                    x.transfer(string, tpath)
        else:
            print s % (1, 91, '  !! file doesn\'t existed'), s % (1, 93, '--'), path

if __name__ == '__main__':
    print s % (1, 92, '  new torrents are at'), new_torrents_dir
    xxx = sys.argv
    main(xxx)
