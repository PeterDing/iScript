#!/usr/bin/env python2
# vim: set fileencoding=utf8

import bencode
import os
import sys
import re
from hashlib import sha1
import base64
import requests
import urlparse
import argparse

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template
letters = [i for i in '.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' \
           + '0123456789']

############################################################
headers = {
    "Connection": "keep-alive",
    "Accept":"text/html,application/xhtml+xml,\
        application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"gzip,deflate,sdch",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;\
        q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/40.0.2214.91 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

def save_img(url, ext):
    path = os.path.join(os.path.expanduser('~'), 'vcode.%s' % ext)
    with open(path, 'w') as g:
        data = requests.get(url).content
        g.write(data)
    print "  ++ 验证码已保存至", s % (1, 97, path)
    input_code = raw_input(s % (2, 92, "  输入验证码: "))
    return input_code

class Bt(object):
    def transfer(self, string, tpath, foo=None, bar=None):
        self.dir_dict = {}
        self.sub_dir_index = 0

        dstring = bencode.bdecode(string)
        files = []
        file_index = 0

        ## change files' name
        if dstring['info'].get('files'):
            for fl in dstring['info']['files']:
                filename = fl['path'][-1]
                if args.type_ == 'n':
                    newfilename = re.sub(foo, bar, filename, re.I) \
                        if foo and bar else filename
                    if filename != newfilename:
                        print filename, s % (1, 92, '==>'), newfilename
                        path = [self._get_sub_dir_index(i) \
                                for i in fl['path'][:-1]]  + [newfilename]
                    else:
                        ext = os.path.splitext(filename)[-1]
                        ext = self._check_ext(ext)
                        path = [self._get_sub_dir_index(i) \
                                for i in fl['path'][:-1]] \
                                + ['%s%s' % (file_index, ext)]
                    file_index += 1
                    fl['path'] = path

                elif args.type_ == 'be64':
                    fn, ext = os.path.splitext(filename)
                    ext = self._check_ext(ext)
                    tfn = '/'.join(fl['path'][:-1] + [fn])
                    e_fn = base64.urlsafe_b64encode(tfn)
                    fl['path'] = [e_fn + '.base64' + ext]

                for item in fl.keys():
                    #if item not in ['path', 'length', 'filehash', 'ed2k']:
                    if item not in ['path', 'length', 'filehash']:
                        del fl[item]

                files.append(fl)
            dstring['info']['files'] = files

        ## change top directory
        for i in dstring['info'].keys():
            if i not in ['files', 'piece length', 'pieces', 'name', 'length']:
                del dstring['info'][i]
            elif 'name' in i:
                if args.name:
                    dstring['info'][i] = args.name

        ## delete comment and creator
        for i in dstring.keys():
            if i not in ['creation date', 'announce', 'info', 'encoding']:
                del dstring[i]

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

    def _check_ext(self, ext):
        if len(ext) > 4:
            return ''

        for e in ext:
            if e not in letters:
                return ''

        return ext

    def get_torrent(self, hh):
        print s % (1, 93, '\n  ++ get torrent from web')

        def do(url, data=None, timeout=None):
            try:
                proxies = {'http': args.proxy} if args.proxy else None
                r = ss.get(url, proxies=proxies, timeout=timeout)
                cnt = r.content
                if r.ok and cnt and '<head>' not in cnt \
                    and '4:name' in cnt:
                    print s % (1, 92, '  √ get torrent.')
                    return cnt
                else:
                    print s % (1, 91, '  × not get.')
                    return None
            except:
                return None

        ## xunlei
        print s % (1, 94, '  >> try:'), 'bt.box.n0808.com'
        url = 'http://bt.box.n0808.com/%s/%s/%s.torrent' \
            % (hh[:2], hh[-2:], hh)
        ss.headers['Referer'] = 'http://bt.box.n0808.com'
        result = do(url)
        if result: return result

        ## https://torrage.com
        if ss.headers.get('Referer'): del ss.headers['Referer']
        print s % (1, 94, '  >> try:'), 'torrage.com'
        url = 'http://torrage.com/torrent/%s.torrent' % hh
        try:
            result = do(url)
            if result: return result
        except:
            pass

        ## http://btcache.me
        if ss.headers.get('Referer'): del ss.headers['Referer']
        print s % (1, 94, '  >> try:'), 'btcache.me'
        url = 'http://btcache.me/torrent/%s' % hh
        r = ss.get(url)
        key = re.search(r'name="key" value="(.+?)"', r.content)
        if key:
            url = 'http://btcache.me/captcha'
            vcode = save_img(url, 'png')
            data = {
                "key": key.group(1),
                "captcha": vcode
            }
            ss.headers['Referer'] = url
            url = 'http://btcache.me/download'
            result = do(url, data=data)
            if result: return result
        else:
            print s % (1, 91, '  × not get.')

        ## torrent stores
        if ss.headers.get('Referer'): del ss.headers['Referer']
        urls = [
                #'http://www.sobt.org/Tool/downbt?info=%s',
                'http://www.win8down.com/url.php?hash=%s&name=name',
                #'http://www.31bt.com/Torrent/%s',
                'http://178.73.198.210/torrent/%s',
                'http://zoink.it/torrent/%s.torrent',
                'http://torcache.net/torrent/%s.torrent',
                'http://torrentproject.se/torrent/%s.torrent',
                'http://istoretor.com/fdown.php?hash=%s',
                'http://torrentbox.sx/torrent/%s',
                'http://www.torrenthound.com/torrent/%s',
                'http://www.silvertorrent.org/download.php?id=%s',
        ]
        for url in urls:
            print s % (1, 94, '  >> try:'), urlparse.urlparse(url).hostname
            url = url % hh
            try:
                result = do(url)
                if result: return result
            except:
                print s % (1, 91, '  !! Error at connection')

        ## with Vuze
        #print s % (1, 94, '  >> try:'), 'magnet.vuze.com'
        #if ss.headers.get('Referer'): del ss.headers['Referer']
        #chh = base64.b32encode(binascii.unhexlify(hh))
        #url = 'http://magnet.vuze.com/magnetLookup?hash=%s' % chh
        #result = do(url)
        #if result: return result

        return False

    def magnet2torrent(self, urls, dir_):
        for url in urls:
            hh = re.search(r'urn:btih:(\w+)', url)
            if hh:
                hh = hh.group(1).upper()
            else:
                print s % (1, 91, '  !! magnet is wrong.'), url
                continue
            string = self.get_torrent(hh)
            if string:
                tpath = os.path.join(dir_, hh + '.torrent')
                print s % (1, 97, '  ++ magnet to torrent:'), \
                    'magnet:?xt=urn:btih:%s' % hh
                with open(tpath, 'w') as g:
                    g.write(string)
            else:
                print s % (1, 91, '  !! Can\'t get torrent from web.'), url

    def torrent2magnet(self, paths):
        def trans(tpath):
            if tpath.lower().endswith('torrent'):
                string = open(tpath).read()
                try:
                    dd = bencode.bdecode(string)
                except Exception as e:
                    print s % (1, 91, '  !! torrent is wrong:'), e
                    return None
                info = bencode.bencode(dd['info'])
                hh = sha1(info).hexdigest()
                print '# %s' % tpath
                print 'magnet:?xt=urn:btih:%s' % hh, '\n'

        for path in paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    for a, b, c in os.walk(path):
                        for i in c:
                            tpath = os.path.join(a, i)
                            trans(tpath)
                elif os.path.isfile(path):
                    tpath = path
                    trans(tpath)
            else:
                print s % (1, 91, '  !! file doesn\'t existed'), \
                    s % (1, 93, '--'), path

    def change(self, ups, dir_, foo=None, bar=None):
        for up in ups:
            path = up
            if path.startswith('magnet:'):
                hh = re.search(r'urn:btih:(\w+)', path)
                if hh:
                    hh = hh.group(1).upper()
                else:
                    print s % (1, 91, '  !! magnet is wrong.'), path
                string = self.get_torrent(hh)
                if string:
                    tpath = os.path.join(dir_, hh + '.torrent')
                    print s % (1, 97, '  ++ transfer:'), \
                        'magnet:?xt=urn:btih:%s' % hh
                    self.transfer(string, tpath, foo=foo, bar=bar)
                else:
                    print s % (1, 91, '  !! Can\'t get torrent from web.'), path

            elif os.path.exists(path):
                if os.path.isdir(path):
                    for a, b, c in os.walk(path):
                        for i in c:
                            ipath = os.path.join(a, i)
                            if i.lower().endswith('torrent'):
                                def do():
                                    print s % (1, 97, '  ++ transfer:'), ipath
                                    string = open(ipath).read()
                                    tpath = os.path.join(dir_, 'change_' + i)
                                    self.transfer(string, tpath, foo=foo,
                                                  bar=bar)
                                    # ??? paths.update(ipath)
                                if os.getcwd() == os.path.abspath(dir_):
                                    do()
                                elif os.getcwd() != os.path.abspath(dir_) and \
                                    os.path.abspath(a) != os.path.abspath(dir_):
                                    do()
                elif os.path.isfile(path):
                    if path.lower().endswith('torrent'):
                        print s % (1, 97, '  ++ transfer:'), path
                        string = open(path).read()
                        tpath = os.path.join(dir_,
                                             'change_' + os.path.basename(path))
                        self.transfer(string, tpath, foo=foo, bar=bar)
            else:
                print s % (1, 91, '  !! file doesn\'t existed'), \
                    s % (1, 93, '--'), path

def import_magnet(froms):
    ml = []
    m_re = re.compile(r'btih:([a-zA-Z0-9]{40})')

    def get_magnet(cm):
        ls = m_re.findall(cm)
        ls = ['magnet:?xt=urn:btih:' + i for i in ls]
        return ls

    for path in froms:
        if path[0] == '~':
            path = os.path.expanduser(path)
        else:
            path = os.path.abspath(path)

        if os.path.isfile(path):
            cm = open(path).read()
            ls = get_magnet(cm)
            ml += ls
        elif os.path.isdir(path):
            for a, b, c in os.walk(path):
                for i in c:
                    p = os.path.join(a, i)
                    cm = open(p).read()
                    ls = get_magnet(cm)
                    ml += ls
        else:
            print s % (1, 91, '  !! path is wrong:'), path

    t = set(ml)
    return list(t)

def main(argv):
    ######################################################
    # for argparse
    p = argparse.ArgumentParser(
        description='magnet torrent 互转，数字命名bt内容文件名' \
        ' 用法见 https://github.com/PeterDing/iScript')
    p.add_argument('xxx', type=str, nargs='*',
        help='命令对象.')
    p.add_argument('-i', '--import_from', type=str, nargs='*',
        help='import magnet from local.')
    p.add_argument('-p', '--proxy', action='store',
                   type=str, help='proxy for torrage.com, \
                                eg: -p "sooks5://127.0.0.1:8883"')
    p.add_argument('-d', '--directory', action='store', default=None,
        type=str, help='torrents保存的路径, eg: -d /path/to/save')
    p.add_argument('-n', '--name', action='store', default=None,
        type=str, help='顶级文件夹名称, eg: -n thistopdirectory')
    p.add_argument('-t', '--type_', action='store',
        default='n', type=str,
        help='类型参数，eg: ')
    global args
    args = p.parse_args(argv[2:])
    comd = argv[1]
    xxx = args.xxx

    dir_ = os.getcwd() if not args.directory \
                        else args.directory
    if not os.path.exists(dir_):
        os.mkdir(dir_)
    if comd == 'm' or comd == 'mt':   # magnet to torrent
        urls = xxx if not args.import_from \
                    else import_magnet(args.import_from)
        x = Bt()
        x.magnet2torrent(urls, dir_)

    elif comd == 't' or comd == 'tm':   # torrent ot magnet
        paths = xxx
        x = Bt()
        x.torrent2magnet(paths)

    elif comd == 'c' or comd == 'ct':   # change
        ups = xxx if not args.import_from \
                    else import_magnet(args.import_from)
        x = Bt()
        x.change(ups, dir_, foo=None, bar=None)

    elif comd == 'cr' or comd == 'ctre':   # change
        foo = xxx[0]
        bar = xxx[1]
        ups = xxx[2:] if not args.import_from \
                        else import_magnet(args.import_from)
        x = Bt()
        x.change(ups, dir_, foo=foo, bar=bar)

    else:
        print s % (2, 91, '  !! 命令错误\n')

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
