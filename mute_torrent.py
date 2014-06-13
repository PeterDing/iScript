#!/usr/bin/env python2
# vim: set fileencoding=utf8

import bencode
import os
import sys

s = u'\x1b[%d;%dm%s\x1b[0m'       # terminual color template

new_torrents_dir = os.path.join(os.getcwd(), 'new_torrents')

class mute_torrent(object):
    def transfer(self, path, tpath):
        string = open(path).read()
        dstring = bencode.bdecode(string)
        dir_dict = {}
        files = []
        i = 0
        for fl in dstring['info']['files']:
            for y in xrange(len(fl['path'])):
                dir_, name = os.path.split(fl['path'][y])
                if not dir_dict.get(dir_): dir_dict[dir_] = i
                name = '%s%s' % (y, os.path.splitext(name)[-1])
                fl['path'][y] = os.path.join(str(dir_dict[dir_]), name)
            files.append(fl)
            i += 1
        dstring['info']['files'] = files
        c = bencode.bencode(dstring)

        with open(tpath, 'w') as g:
            g.write(c)

def main(xxx):
    if not os.path.exists(new_torrents_dir):
        os.mkdir(new_torrents_dir)

    x = mute_torrent()

    for path in xxx:
        if os.path.exists(path):
            if os.path.isdir(path):
                for a, b, c in os.walk(path):
                    for i in c:
                        if os.path.abspath(a) == new_torrents_dir: continue
                        ipath = os.path.join(a, i)
                        if ipath.lower().endswith('torrent'):
                            print s % (1, 97, '  ++ transfer:'), ipath
                            tpath = os.path.join(new_torrents_dir, i)
                            x.transfer(ipath, tpath)
            elif os.path.isfile(path):
                if path.lower().endswith('torrent'):
                    print s % (2, 97, '  ++ transfer:'), path
                    tpath = os.path.join(new_torrents_dir, os.path.basename(path))
                    x.transfer(path, tpath)
        else:
            print s % (1, 91, '  !! file doesn\'t existed'), s % (1, 93, '--'), path

if __name__ == '__main__':
    print s % (1, 92, '  new torrents are at'), new_torrents_dir
    xxx = sys.argv
    main(xxx)
