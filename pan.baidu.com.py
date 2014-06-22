#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
import requests
from requests_toolbelt import MultipartEncoder
import urllib
import json
import cPickle as pk
import re
import time
import argparse
import random
import select
import base64
import md5
from zlib import crc32
import StringIO
import signal


username = ''
password = ''


############################################################
# Defines that should never be changed
OneK = 1024
OneM = OneK * OneK
OneG = OneM * OneK
OneT = OneG * OneK
OneP = OneT * OneK
OneE = OneP * OneK

############################################################
# Default values
MinRapidUploadFileSize = 256 * OneK
DefaultSliceSize = 10 * OneM
MaxSliceSize = 2 * OneG
MaxSlicePieces = 1024
ENoError = 0

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

cookie_file = os.path.join(os.path.expanduser('~'), '.bp.cookies')
upload_datas_path = os.path.join(os.path.expanduser('~'), '.bp.pickle')

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://www.baidu.com/",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

class panbaiducom_HOME(object):
    def __init__(self, url=''):
        self.path = self.get_path(url)
        self.download = self.play if args.play else self.download
        self.ondup = 'overwrite'

    def init(self):
        def loginandcheck():
            self.login()
            if self.check_login():
                print s % (1, 92, '  -- login success\n')
            else:
                print s % (1, 91, '  !! login fail, maybe username or password is wrong.\n')
                print s % (1, 91, '  !! maybe this app is down.')
                sys.exit(1)

        if os.path.exists(cookie_file):
            t = json.loads(open(cookie_file).read())
            if t.get('user') != None and t.get('user') == username:
                ss.cookies.update(t.get('cookies', t))
                if not self.check_login():
                    loginandcheck()
            else:
                print s % (1, 91, '\n  ++  username changed, then relogin')
                loginandcheck()
        else:
            loginandcheck()

    def get_path(self, url):
        t = re.search(r'path=(.+?)(&|$)', url)
        if t:
            t = t.group(1)
        else:
            t = '/'
        t = urllib.unquote_plus(t)
        return t

    @staticmethod
    def save_img(url, ext):
        path = os.path.join(os.path.expanduser('~'), 'vcode.%s' % ext)
        with open(path, 'w') as g:
            data = urllib.urlopen(url).read()
            g.write(data)
        print "  ++ 验证码已保存至", s % (1, 97, path)
        input_code = raw_input(s % (2, 92, "  输入验证码: "))
        return input_code

    def check_login(self):
        #print s % (1, 97, '\n  -- check_login')
        url = 'http://www.baidu.com/home/msg/data/personalcontent'
        r = ss.get(url)
        if 'errNo":"0' in r.content:
            #print s % (1, 92, '  -- check_login success\n')
            #self.get_dsign()
            self.save_cookies()
            return True
        else:
            print s % (1, 91, '  -- check_login fail\n')
            return False

    def login(self):
        print s % (1, 97, '\n  -- login')

        # Check if we have to deal with verify codes
        params = {
            'tpl': 'pp',
            'callback': 'bdPass.api.login._needCodestringCheckCallback',
            'index': 0,
            'logincheck': '',
            'time': 0,
            'username': username
        }

        # Ask server
        url = 'https://passport.baidu.com/v2/api/?logincheck'
        r = ss.get(url, params=params)
        # Callback for verify code if we need
        #codestring = r.content[r.content.index('(')+1:r.content.index(')')]
        codestring = re.search(r'\((.+?)\)', r.content).group(1)
        codestring = json.loads(codestring)['codestring']
        codestring = codestring if codestring else ""
        url = 'https://passport.baidu.com/cgi-bin/genimage?'+codestring
        verifycode = self.save_img(url, 'gif') if codestring != "" else ""

        # Now we'll do login
        # Get token
        ss.get('http://www.baidu.com')
        t = ss.get('https://passport.baidu.com/v2/api/?getapi&class=login' \
                   '&tpl=pp&tangram=false').text
        token = re.search(r'login_token=\'(.+?)\'', t).group(1)

        # Construct post body
        data = {
            'token': token,
            'ppui_logintime': '1600000',
            'charset':'utf-8',
            'codestring': codestring,
            'isPhone': 'false',
            'index': 0,
            'u': '',
            'safeflg': 0,
            'staticpage': 'http://www.baidu.com/cache/user/html/jump.html',
            'loginType': 1,
            'tpl': 'pp',
            'callback': 'parent.bd__pcbs__qvljue',
            'username': username,
            'password': password,
            'verifycode': verifycode,
            'mem_pass': 'on',
            'apiver': 'v3'
        }

        # Post!
        # XXX : do not handle errors
        url = 'https://passport.baidu.com/v2/api/?login'
        ss.post(url, data=data)

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            c = {'user': username, 'cookies': ss.cookies.get_dict()}
            g.write(json.dumps(c, indent=4, sort_keys=True))

    def _get_bdstoken(self):
        if hasattr(self, 'bdstoken'):
            return self.bdstoken

        url = 'http://pan.baidu.com/wap/share/home'
        r = ss.get(url)
        html = r.content

        t = re.search(r'bdstoken="(.+?)"', html)
        if t:
            bdstoken = t.group(1)
            return bdstoken
        else:
            print s % (1, 91, '  !! Error at _get_bdstoken')
            sys.exit(1)

    #def _sift(self, fileslist, name=None, size=None, time=None, head=None, tail=None, include=None, exclude=None):
    def _sift(self, fileslist, **arguments):
        """
        a filter for time, size, name, head, tail, include, exclude
        support regular expression
        """

        def sort(reverse, arg, fileslist=fileslist):
            tdict = {fileslist[i][arg] : i for i in xrange(len(fileslist))}
            keys = tdict.keys()
            keys.sort(reverse=reverse)
            indexs = [tdict[i] for i in keys]
            fileslist = [fileslist[i] for i in indexs]
            return fileslist

        # for time
        if arguments.get('name'):
            reverse = None
            if arguments['name'] == 'reverse':
                reverse = True
            elif arguments['name'] == 'no_reverse':
                reverse = False
            fileslist = sort(reverse, 'server_filename')

        # for size
        if arguments.get('size'):
            reverse = None
            if arguments['size'] == 'reverse':
                reverse = True
            elif arguments['size'] == 'no_reverse':
                reverse = False
            fileslist = sort(reverse, 'size')

        # for size
        if arguments.get('time'):
            reverse = None
            if arguments['time'] == 'reverse':
                reverse = True
            elif arguments['time'] == 'no_reverse':
                reverse = False
            fileslist = sort(reverse, 'local_mtime')

        # for head, tail, include, exclude
        head = args.head
        tail = args.tail
        include = args.include
        exclude = args.exclude
        if head or tail or include or exclude:
            tdict = {fileslist[i]['server_filename'] : i for i in xrange(len(fileslist))}
            keys1 = [i for i in tdict.keys() if i.lower().startswith(head.encode('utf8').lower())] \
                if head else []
            keys2 = [i for i in tdict.keys() if i.lower().endswith(tail.decode('utf8').lower())] \
                if tail else []
            keys3 = [i for i in tdict.keys() if re.search(include, i.encode('utf8'), flags=re.I)] \
                if include else []
            keys4 = [i for i in tdict.keys() if not re.search(exclude, i.encode('utf8'), flags=re.I)] \
                if exclude else []

            # intersection
            keys = [i for i in [keys1, keys2, keys3, keys4] if i]
            if len(keys) > 1:
                tkeys = keys[0]
                for i in keys:
                    tkeys &= i
                keys = tkeys
            elif len(keys) == 1:
                keys = keys[0]
            elif len(keys) == 0:
                keys = []

            indexs = [tdict[i] for i in keys]
            fileslist = [fileslist[i] for i in indexs]

        dirs = [i for i in fileslist if i['isdir']]
        files = [i for i in fileslist if not i['isdir']]
        if arguments.get('desc') == 1:
            dirs.reverse()
            files.reverse()
        fileslist = dirs + files

        return fileslist

    def _get_file_list(self, order, desc, dir_):
        t = {'Referer':'http://pan.baidu.com/disk/home'}
        theaders = headers
        theaders.update(t)

        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "num": 10000,   ## max amount of listed file at one page
            "t": int(time.time()*1000),
            "dir": dir_,
            "page": 1,
            "desc": 1,   ## reversely
            "order": order, ## sort by name, or size, time
            "_": int(time.time()*1000)
            #"bdstoken": token
        }
        if not desc: del p['desc']
        url = 'http://pan.baidu.com/api/list'
        r = ss.get(url, params=p, headers=theaders)
        j = r.json()
        if j['errno'] != 0:
            print s % (1, 91, '  error: _get_file_list'), '--', j
            sys.exit(1)
        else:
            return j

    def get_infos(self):
        dir_loop = [self.path]
        base_dir = '' if os.path.split(self.path)[0] == '/' \
            else os.path.split(self.path)[0]
        for d in dir_loop:
            j = self._get_file_list('name', None, d)
            if j['list']:
                if args.head or args.tail or args.include or args.exclude:
                    j['list'] = self._sift(j['list'])
                if args.type_:
                    j['list'] = [x for x in j['list'] if x['isdir'] \
                        or x['server_filename'][-len(args.type_):] \
                        == unicode(args.type_)]
                total_file = len([i for i in j['list'] if not i['isdir']])
                if args.from_ - 1:
                    j['list'] = j['list'][args.from_-1:] if args.from_ else j['list']
                nn = args.from_
                for i in j['list']:
                    if i['isdir']:
                        dir_loop.append(i['path'].encode('utf8'))
                    else:
                        t = i['path'].encode('utf8')
                        t = t.replace(base_dir, '')
                        t = t[1:] if t[0] == '/' else t
                        t =  os.path.join(os.getcwd(), t)
                        if not i.has_key('dlink'):
                            i['dlink'] = self._get_dlink2(i)
                        infos = {
                            'file': t,
                            'path': i['path'].encode('utf8'),
                            'dir_': os.path.split(t)[0],
                            'dlink': i['dlink'].encode('utf8'),
                            'name': i['server_filename'].encode('utf8'),
                            'nn': nn,
                            'total_file': total_file
                        }
                        nn += 1
                        self.download(infos)
            elif not j['list']:
                self.path, server_filename = os.path.split(self.path)
                j = self._get_file_list('name', None, self.path)
                if j['errno'] == 0 and j['list']:
                    for i in j['list']:
                        if i['server_filename'].encode('utf8') == server_filename:
                            if i['isdir']: break
                            t =  os.path.join(os.getcwd(), server_filename)
                            if not i.has_key('dlink'):
                                i['dlink'] = self._get_dlink2(i)
                            infos = {
                                'file': t,
                                'path': i['path'].encode('utf8'),
                                'dir_': os.path.split(t)[0],
                                #'dlink': self.get_dlink(i),
                                'dlink': i['dlink'].encode('utf8'),
                                'name': i['server_filename'].encode('utf8')
                            }
                            self.download(infos)
                            break

    def _get_dsign(self):
        url = 'http://pan.baidu.com/disk/home'
        r = ss.get(url)
        html = r.content
        sign1 = re.search(r'sign1="(.+?)";', html).group(1)
        sign3 = re.search(r'sign3="(.+?)";', html).group(1)
        timestamp = re.search(r'timestamp="(.+?)";', html).group(1)

        def sign2(j, r):
            a = []
            p = []
            o = ''
            v = len(j)

            for q in xrange(256):
                a.append(ord(j[q % v]))
                p.append(q)

            u = 0
            for q in xrange(256):
                u = (u + p[q] + a[q]) % 256
                t = p[q]
                p[q] = p[u]
                p[u] = t

            i = 0
            u = 0
            for q in xrange(len(r)):
                i = (i + 1) % 256
                u = (u + p[i]) % 256
                t = p[i]
                p[i] = p[u]
                p[u] = t
                k = p[((p[i] + p[u]) % 256)]
                o += chr(ord(r[q]) ^ k)

            return base64.b64encode(o)

        self.dsign = sign2(sign3, sign1)
        self.timestamp = timestamp

    def _get_dlink(self, i):
        if not hasattr(self, 'dsign'):
            self._get_dsign()

        while True:
            params = {
                "channel": "chunlei",
                "clienttype": 0,
                "web": 1,
                #"bdstoken": token
            }

            data = {
                "sign": self.dsign,
                "timestamp": self.timestamp,
                "fidlist": "[%s]" % i['fs_id'],
                "type": "dlink"
            }

            url = 'http://pan.baidu.com/api/download'
            r = ss.post(url, params=params, data=data)
            j = r.json()
            if j['errno'] == 0:
                dlink = j['dlink'][0]['dlink'].encode('utf8')
                return dlink
            else:
                self._get_dsign()

    def _get_dlink2(self, i):
        j = self._meta([i['path'].encode('utf8')])
        if j:
            return j['info'][0]['dlink'].encode('utf8')
        else:
            print s % (1, 91, '  !! Error at _get_dlink2')
            sys.exit(1)

    @staticmethod
    def download(infos):
        ## make dirs
        if not os.path.exists(infos['dir_']):
            os.makedirs(infos['dir_'])
        else:
            if os.path.exists(infos['file']):
                return 0

        num = random.randint(0, 7) % 7
        col = s % (2, num + 90, infos['file'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] if infos.get('total_file') else 1
        print '\n  ++ 正在下载: #', s % (1, 97, infos['nn']), '/', s % (1, 97, infos['total_file']), '#', col

        if args.aria2c:
            if args.limit:
                cmd = 'aria2c -c -x %s -s %s ' \
                    '--max-download-limit %s ' \
                    '-o "%s.tmp" -d "%s" \
                    --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (args.aria2c, args.aria2c, args.limit, infos['name'], \
                    infos['dir_'], headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'aria2c -c -x %s -s %s ' \
                    '-o "%s.tmp" -d "%s" --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (args.aria2c, args.aria2c, infos['name'], infos['dir_'], headers['User-Agent'], \
                        infos['dlink'])
        else:
            if args.limit:
                cmd = 'wget -c --limit-rate %s ' \
                    '-O "%s.tmp" --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (args.limit, infos['file'], headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'wget -c -O "%s.tmp" --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (infos['file'], headers['User-Agent'], infos['dlink'])

        status = os.system(cmd)
        if status != 0:     # other http-errors, such as 302.
            wget_exit_status_info = wget_es[status]
            print('\n\n ---###   \x1b[1;91mERROR\x1b[0m ==> '\
                '\x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
                 % (status, wget_exit_status_info))
            print s % (1, 91, '  ===> '), cmd
            sys.exit(1)
        else:
            os.rename('%s.tmp' % infos['file'], infos['file'])

    @staticmethod
    def play(infos):
        num = random.randint(0, 7) % 7
        col = s % (2, num + 90, infos['path']) if args.view \
            else s % (2, num + 90, infos['name'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] if infos.get('total_file') else 1
        print '\n  ++ play: #', s % (1, 97, infos['nn']), '/', \
            s % (1, 97, infos['total_file']), '#', col

        if os.path.splitext(infos['file'])[-1].lower() == '.wmv':
            cmd = 'mplayer -really-quiet -cache 8140 ' \
                '-http-header-fields "user-agent:%s" ' \
                '-http-header-fields "Referer:http://pan.baidu.com/disk/home" "%s"' \
                % (headers['User-Agent'], infos['dlink'])
        else:
            cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
                '--http-header-fields "user-agent:%s" '\
                '--http-header-fields "Referer:http://pan.baidu.com/disk/home" "%s"' \
                % (headers['User-Agent'], infos['dlink'])

        status = os.system(cmd)
        timeout = 1
        ii, _, _ = select.select([sys.stdin], [], [], timeout)
        if ii:
            sys.exit(0)
        else:
            pass

    def _make_dir(self, dir_):
        p = {
            "a": "commit",
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "bdstoken": self._get_bdstoken()
        }
        data = {
            "path": dir_,
            "isdir": 1,
            "size": "",
            "block_list": [],
            "method": "post"
        }
        url = 'http://pan.baidu.com/api/create'
        r = ss.post(url, params=p, data=data)
        j = r.json()
        if j['errno'] != 0:
            print s % (1, 91, '  !! Error at _make_dir')
            sys.exit(1)

    def _meta(self, file_list):
        p = {
            "channel": "chunlei",
            "app_id": "250528",
            "method": "filemetas",
            "dlink": 1,
            "blocks": 0,  # 0 or 1
            #"bdstoken": self._get_bdstoken()
        }
        data = {'target': json.dumps(file_list)}
        url = 'http://pan.baidu.com/api/filemetas'
        r = ss.post(url, params=p, data=data, verify=False)
        j = r.json()
        if j['errno'] == 0:
            return j
        else:
            return False

    def _rapidupload_file(self, lpath, rpath):
        print '  |-- upload_function:', s % (1, 97, '_rapidupload_file')
        slice_md5 = md5.new(open(lpath, 'rb').read(256 * OneK)).hexdigest()
        with open(lpath, "rb") as f:
            buf = f.read(OneM)
            content_md5 = md5.new()
            content_md5.update(buf)
            crc = crc32(buf).conjugate()
            while True:
                buf = f.read(OneM)
                if buf:
                    crc = crc32(buf, crc).conjugate()
                    content_md5.update(buf)
                else:
                    break
            content_md5 = content_md5.hexdigest()
            content_crc32 = crc.conjugate() & 0xffffffff

        p = {
            "method" : "rapidupload",
            "app_id": "250528",
            "BDUSS": ss.cookies['BDUSS']
        }
        data = {
            "path": os.path.join(rpath, os.path.basename(lpath)),
            "content-length" : self.__current_file_size,
            "content-md5" : content_md5,
            "slice-md5" : slice_md5,
            "content-crc32" : content_crc32,
            "ondup" : self.ondup
        }
        url = 'https://c.pcs.baidu.com/rest/2.0/pcs/file'
        r = ss.post(url, params=p, data=data, verify=False)
        if r.ok:
            return ENoError
        else:
            return r.json()

    def _upload_one_file(self, lpath, rpath):
        print '  |-- upload_function:', s % (1, 97, '_upload_one_file')
        p = {
            "method": "upload",
            "app_id": "250528",
            "ondup": self.ondup,
            "dir": rpath,
            "filename": os.path.basename(lpath),
            "BDUSS": ss.cookies['BDUSS'],
        }
        files = {'file': ('file', open(lpath, 'rb'), '')}
        data = MultipartEncoder(files)
        theaders = headers
        theaders['Content-Type'] = data.content_type
        url = 'https://c.pcs.baidu.com/rest/2.0/pcs/file'
        r = ss.post(url, params=p, data=data, verify=False, headers=theaders)
        if r.ok:
            return ENoError
        else:
            sys.exit(1)

    def _combine_file(self, lpath, rpath):
        p = {
            "method": "createsuperfile",
            "app_id": "250528",
            "ondup": self.ondup,
            "path": os.path.join(rpath, os.path.basename(lpath)),
            "BDUSS": ss.cookies['BDUSS'],
        }
        data = {'param': json.dumps({'block_list': self.upload_datas[lpath]['slice_md5s']})}
        url = 'https://c.pcs.baidu.com/rest/2.0/pcs/file'
        r = ss.post(url, params=p, data=data, verify=False)
        if r.ok:
            return ENoError
        else:
            sys.exit(1)

    def _upload_slice(self):
        p = {
            "method": "upload",
            "app_id": "250528",
            "type": "tmpfile",
            "BDUSS": ss.cookies['BDUSS'],
        }

        file = StringIO.StringIO(self.__slice_block)
        files = {'file': ('file', file, '')}
        data = MultipartEncoder(files)
        theaders = headers
        theaders['Content-Type'] = data.content_type
        url = 'https://c.pcs.baidu.com/rest/2.0/pcs/file'
        r = ss.post(url, params=p, data=data, verify=False, headers=theaders)
        j = r.json()
        if self.__slice_md5 == j['md5']:
            return ENoError
        else:
            return 'MD5Mismatch'

    def _get_pieces_slice(self):
        pieces = MaxSlicePieces
        slice = DefaultSliceSize
        n = 1
        while True:
            t = n * DefaultSliceSize * MaxSlicePieces
            if self.__current_file_size <= t:
                if self.__current_file_size % (n * DefaultSliceSize) == 0:
                    pieces = self.__current_file_size / (n * DefaultSliceSize)
                    slice = n * DefaultSliceSize
                else:
                    pieces = (self.__current_file_size / (n * DefaultSliceSize)) + 1
                    slice = n * DefaultSliceSize
                break
            elif t > MaxSliceSize * MaxSlicePieces:
                n += 1
            else:
                print s % (1, 91, '  !! file is too big, uploading is not supported.')
                sys.exit(1)

        return pieces, slice

    def _get_upload_function(self, rapidupload_is_fall=False):
        if self.__current_file_size > MinRapidUploadFileSize:
            if not rapidupload_is_fall:
                return '_rapidupload_file'
            else:
                if self.__current_file_size <= DefaultSliceSize:
                    return '_upload_one_file'

                elif self.__current_file_size <= MaxSliceSize * MaxSlicePieces:
                    return '_upload_file_slices'
                else:
                    print s % (1, 91, '  !! Error: size of file is too big.')
                    return 'None'
        else:
            return '_upload_one_file'

    def _upload_file(self, lpath, rpath):
        print s % (1, 94, '  ++ uploading:'), lpath

        __current_file_size = os.path.getsize(lpath)
        self.__current_file_size = __current_file_size
        upload_function = self._get_upload_function()

        if self.upload_datas.has_key(lpath):
            if __current_file_size != self.upload_datas[lpath]['size']:
                self.upload_datas[lpath]['is_over'] = False
                self.upload_datas[lpath]['size'] = __current_file_size
            self.upload_datas[lpath]['upload_function'] = upload_function
        else:
            self.upload_datas[lpath] = {
                'is_over': False,
                'upload_function': upload_function,
                'size': __current_file_size,
                'remotepaths': set()
            }

        while True:
            if not self.upload_datas[lpath]['is_over']:
                m = self.upload_datas[lpath]['upload_function']
                if m == '_upload_file_slices':
                    time.sleep(2)
                    print '  |-- upload_function:', s % (1, 97, '_upload_file_slices')
                    pieces, slice = self._get_pieces_slice()
                    f = open(lpath, 'rb')
                    current_piece_point = len(self.upload_datas[lpath]['slice_md5s'])
                    f.seek(current_piece_point * slice)
                    for piece in xrange(current_piece_point, pieces):
                        self.__slice_block = f.read(slice)
                        if self.__slice_block:
                            self.__slice_md5 = md5.new(self.__slice_block).hexdigest()
                            while True:
                                result = self._upload_slice()
                                if result == ENoError:
                                    break
                                else:
                                    print s % (1, 91, '  |-- slice_md5 does\'n match, retry.')
                            self.upload_datas[lpath]['slice_md5s'].append(self.__slice_md5)
                            self.save_upload_datas()
                            percent = round(100*((piece + 1.0) / pieces), 2)
                            print s % (1, 97, '  |-- upload: %s%s' % (percent, '%')), piece + 1, '/', pieces
                    result = self._combine_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        del self.upload_datas[lpath]['slice_md5s']
                        self.save_upload_datas()
                        print s % (1, 92, '  |-- success.\n')
                        break
                    else:
                        print s % (1, 91, '  !! Error at _combine_file')

                elif m == '_upload_one_file':
                    time.sleep(2)
                    result = self._upload_one_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        self.save_upload_datas()
                        print s % (1, 92, '  |-- success.\n')
                        break
                    else:
                        print s % (1, 91, '  !! Error: _upload_one_file is fall, retry.')

                elif m == '_rapidupload_file':
                    time.sleep(2)
                    result = self._rapidupload_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        self.save_upload_datas()
                        print s % (1, 92, '  |-- RapidUpload: Success.\n')
                        break
                    else:
                        if args.type_ == 'r':   # only rapidupload
                            print s % (1, 92, '  |-- can\'t be RapidUploaded\n')
                            break
                        print s % (1, 93, '  |-- can\'t be RapidUploaded, ' \
                            'now trying normal uploading.')
                        upload_function = self._get_upload_function(rapidupload_is_fall=True)
                        self.upload_datas[lpath]['upload_function'] = upload_function
                        if upload_function == '_upload_file_slices':
                            if not self.upload_datas[lpath].has_key('slice_md5s'):
                                self.upload_datas[lpath]['slice_md5s'] = []

                else:
                    print s % (1, 91, '  !! Error: size of file is too big.')
                    break

            else:
                if args.uploadmode == 'c':
                    if rpath in self.upload_datas[lpath]['remotepaths']:
                        print s % (1, 92, '  |-- file was uploaded.\n')
                        break
                    else:
                        self.upload_datas[lpath]['is_over'] = False
                elif args.uploadmode == 'o':
                    print s % (1, 93, '  |-- reupload.')
                    self.upload_datas[lpath]['is_over'] = False

    def _upload_dir(self, lpath, rpath):
        base_dir = os.path.split(lpath)[0]
        for a, b, c in os.walk(lpath):
            for path in c:
                localpath = os.path.join(a, path)
                t = localpath.replace(base_dir + '/', '')
                t = os.path.split(t)[0]
                remotepath = os.path.join(rpath, t)
                self._upload_file(localpath, remotepath)

    def upload(self, localpaths, remotepath):
        self.upload_datas_path = upload_datas_path
        self.upload_datas = {}
        if os.path.exists(self.upload_datas_path):
            f = open(self.upload_datas_path, 'rb')
            upload_datas = pk.load(f)
            if upload_datas:
                self.upload_datas = upload_datas

        for localpath in localpaths:
            lpath = localpath
            if localpath[0] == '~':
                lpath = os.path.expanduser(localpath)
            else:
                lpath = os.path.abspath(localpath)
            rpath = remotepath if remotepath[0] == '/' else '/' + remotepath

            if os.path.exists(lpath):
                pass
            else:
                print s % (1, 91, '  !! Error: localpath doesn\'t exist')
                print s % (1, 91, '  ==>'), lpath
                continue

            if os.path.isdir(lpath):
                self._upload_dir(lpath, rpath)
            elif os.path.isfile(lpath):
                self._upload_file(lpath, rpath)
            else:
                print s % (1, 91, '  !! Error: localpath ?')
                sys.exit(1)

    def save_upload_datas(self):
        f = open(self.upload_datas_path, 'wb')
        pk.dump(self.upload_datas, f)

    ##################################################################
    # for saving shares

    def _share_transfer(self, info):
        meta = self._meta([info['remotepath'].encode('utf8')])
        if not meta:
            self._make_dir(info['remotepath'].encode('utf8'))

        theaders = headers
        theaders.update({'Referer': 'http://pan.baidu.com/share/link?shareid=%s&uk=%s' \
            % (self.shareid, self.uk)})

        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "ondup": "overwrite",
            "async": 1,
            "from": self.uk,
            "shareid": self.shareid,
            "bdstoken": self._get_bdstoken()
        }
        data = "path=" + urllib.quote_plus(info['remotepath'].encode('utf8')) + \
            '&' + "filelist=" + urllib.quote_plus('["%s"]' % info['path'].encode('utf8'))

        url = 'http://pan.baidu.com/share/transfer'
        r = ss.post(url, params=p, data=data, headers=theaders, verify=False)
        j = r.json()
        if j['errno'] == 0:
            return ENoError
        else:
            return j['errno']

    def _get_share_list(self, info):
        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "num": 10000,
            "dir": info['path'].encode('utf8'),
            "t": int(time.time()*1000),
            "uk": self.uk,
            "shareid": self.shareid,
            #"desc": 1,   ## reversely
            "order": "name", ## sort by name, or size, time
            "_": int(time.time()*1000),
            "bdstoken": self._get_bdstoken()
        }
        url = 'http://pan.baidu.com/share/list'
        r = ss.get(url, params=p)
        j = r.json()
        if j['errno'] != 0:
            print s % (1, 91, '  !! Error at _get_share_list')
            sys.exit(1)
        rpath = '/'.join([info['remotepath'], os.path.split(info['path'])[-1]])
        for x in xrange(len(j['list'])):
            j['list'][x]['remotepath'] = rpath

        return j['list']

    def _get_share_infos(self, url, remotepath, infos):
        r = ss.get(url)
        html = r.content

        self.uk = re.search(r'FileUtils.share_uk="(.+?)"', html).group(1)
        self.shareid = re.search(r'FileUtils.share_id="(.+?)"', html).group(1)
        self.bdstoken = re.search(r'bdstoken="(.+?)"', html).group(1)

        isdirs = [int(x) for x in re.findall(r'\\"isdir\\":\\"(\d)\\"', html)]
        paths = [json.loads('"%s"' % x.replace('\\\\', '\\')) \
            for x in re.findall(r'\\"path\\":\\"(.+?)\\",\\"', html)]
        z = zip(isdirs, paths)
        if not infos:
            infos = [{
                'isdir': x,
                'path': y,
                'remotepath': remotepath if remotepath[-1] != '/' else remotepath[:-1]
            } for x, y in z]

        return infos

    def save_share(self, url, remotepath, infos=None):
        infos = self._get_share_infos(url, remotepath, infos)
        for info in infos:
            print s % (1, 97, '  ++ transfer:'), info['path']
            result = self._share_transfer(info)
            if result == ENoError:
                pass
            elif result == 12:
                print s % (1, 91, '  |-- file had existed.')
                sys.exit()
            elif result == -33:
                if info['isdir']:
                    print s % (1, 93, '  |-- over transferring limit.')
                    infos += self._get_share_list(info)
                else:
                    print s % (1, 91, '  !! Error: can\'t transfer file')
            else:
                print s % (1, 91, '  !! Error at save_share, errno:'), result
                sys.exit(1)

    @staticmethod
    def _secret_or_not(url):
        ss.headers['Referer'] = 'http://pan.baidu.com'
        r = ss.get(url)
        if 'init' in r.url:
            if not args.secret:
                secret = raw_input(s % (2, 92, "  请输入提取密码: "))
            else:
                secret = args.secret
            data = 'pwd=%s' % secret
            url = "%s&t=%d" % (r.url.replace('init', 'verify'), int(time.time()))
            r = ss.post(url, data=data)
            if r.json()['errno']:
                print s % (2, 91, "  !! 提取密码错误\n")
                sys.exit(1)

    #######################################################################
    # for saveing inbox shares

    def _share_inbox_transfer(self, info, burl):
        meta = self._meta([info['remotepath'].encode('utf8')])
        if not meta:
            self._make_dir(info['remotepath'].encode('utf8'))

        p = "channel=chunlei&" + "clienttype=0&" + "web=1&" + \
            "path=%s&" % urllib.quote_plus(info['remotepath'].encode('utf8')) + \
            "object_array=%s&" % urllib.quote_plus('["%s"]' % info['object_id'].encode('utf8')) + \
            "fsid_array=%s&" % urllib.quote_plus('[%s]' % info['fs_id']) + \
            "session_id=%s&" % self.session_id + \
            "founder_uk=%s&" % self.founder_uk + \
            "bdstoken=%s" % self._get_bdstoken()

        url = 'http://pan.baidu.com/inbox/object/transfer?' + p
        r = ss.get(url)
        j = r.json()
        if j['errno'] == 0:
            return ENoError
        else:
            return j['errno']

    def _get_share_inbox_list(self, info):
        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "object_id": info['object_id'],
            "object_status": info['object_status'],
            "fs_id": info['fs_id'],
            "path": info['path'],
            "server_filename": info['server_filename'],
            "size": info['size'],
            "server_mtime": info['server_mtime'],
            "server_ctime": info['server_ctime'],
            "local_mtime": info['local_mtime'],
            "local_ctime": info['local_ctime'],
            "isdir": info['isdir'],
            "category": info['category'],
            "founder_uk": self.founder_uk,
            "session_id": self.session_id,
            "bdstoken": self._get_bdstoken(),
        }
        if info.get('ori_path'): p.update({"ori_path": info['ori_path']})
        if info.get('dir_ref'): p.update({"dir_ref": info['dir_ref']})
        if info.get('md5'): p.update({"md5": ""})
        if info.get('create_time'): p.update({"create_time": "1402299935"})
        if info.get('update_time'): p.update({"update_time": "1402299935"})
        if info.get('last_time'): p.update({"last_time": ""})

        url = 'http://pan.baidu.com/inbox/object/unpanfileinfo'
        r = ss.get(url, params=p)
        j = r.json()
        if j['errno'] != 0:
            print s % (1, 91, '  !! Error at _get_share_inbox_list')
            sys.exit(1)
        rpath = '/'.join([info['remotepath'], os.path.split(info['path'])[-1]])
        for x in xrange(len(j['list'])):
            j['list'][x]['remotepath'] = rpath
        return j['list']

    def _get_share_inbox_infos(self, url, remotepath, infos):
        r = ss.get(url)
        html = r.content

        self.founder_uk = re.search(r'FileUtils.founder_uk=(\d+)', html).group(1)
        self.session_id = re.search(r'FileUtils.session_id="(.+?)"', html).group(1)
        self.bdstoken = re.search(r'bdstoken="(.+?)"', html).group(1)

        p = {
            "session_id": self.session_id,
            "founder_uk": self.founder_uk,
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "bdstoken": self._get_bdstoken(),
        }
        url = 'http://pan.baidu.com/inbox/object/unpanfileinfo'
        r = ss.get(url, params=p)
        j = r.json()
        if j['errno'] == 0:
            for x in xrange(len(j['list'])):
                rpath = '/'.join([remotepath, os.path.split(j['list'][x]['path'])[-1]])
                j['list'][x]['remotepath'] = rpath
            return j['list']
        else:
            print s % (1, 91, '  !! Error at _get_share_inbox_infos')
            sys.exit()


    def save_inbox_share(self, url, remotepath, infos=None):
        ss.headers['Referer'] = 'http://pan.baidu.com'
        remotepath = remotepath if remotepath[-1] != '/' else remotepath[:-1]
        infos = self._get_share_inbox_infos(url, remotepath, infos)
        for info in infos:
            print s % (1, 97, '  ++ transfer:'), info['path']
            result = self._share_inbox_transfer(info, url)
            if result == ENoError:
                pass
            elif result == 12:
                print s % (1, 91, '  |-- file had existed.')
                sys.exit()
            #elif result == -33:
            elif result == 1:
                if info['isdir']:
                    print s % (1, 93, '  |-- over transferring limit.')
                    infos += self._get_share_inbox_list(info)
                else:
                    print s % (1, 91, '  !! Error: can\'t transfer file')
            else:
                print s % (1, 91, '  !! Error at save_inbox_share, errno:'), result
                sys.exit(1)

    #######################################################################
    # for finding files

    def _search(self, keyword, directory):
        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "dir": directory if directory else "",
            "key": keyword,
            #"timeStamp": "0.15937364846467972",
            #"bdstoken": self._get_bdstoken(),
        }
        if args.recursive: p['recursion'] = 1
        url = 'http://pan.baidu.com/api/search'
        r = ss.get(url, params=p)
        j = r.json()
        if j['errno'] == 0:
            return j['list']
        else:
            print s % (1, 91, '  !! Error at _search'), j
            sys.exit(1)

    def _find_display(self, info):
        # https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
        def sizeof_fmt(num):
            for x in ['','KB','MB','GB']:
                if num < 1024.0:
                    return "%3.1f%s" % (num, x)
                num /= 1024.0
            return "%3.1f%s" % (num, 'TB')

        if args.type_ == 'f':
            if info['isdir']:
                return
        elif args.type_ == 'd':
            if not info['isdir']:
                return
        else:
            pass

        if args.ls_color == 'on':
            isdir = s % (1, 93, 'd') if info['isdir'] else s % (1, 97, '-')
            size = s % (1, 91, sizeof_fmt(info['size']).rjust(7))
            base_dir, filename = os.path.split(info['path'])
            path = os.path.join(s % (2, 95, base_dir.encode('utf8'))
                if base_dir != '/' else '/', \
                filename.encode('utf8') \
                if not info['isdir'] else s % (2, 92, filename.encode('utf8')))
            template = '  %s %s %s' % (isdir, size, path)
            print template
        elif args.ls_color == 'off':
            isdir = 'd' if info['isdir'] else '-'
            size = sizeof_fmt(info['size']).rjust(7)
            path = info['path'].encode('utf8')
            template = '  %s %s %s' % (isdir, size, path)
            print template

    def find(self, keyword, **arguments):
        infos = self._search(keyword, arguments.get('directory'))
        infos = self._sift(infos, name=arguments.get('name'), \
            size=arguments.get('size'), time=arguments.get('time'), \
            desc=arguments.get('desc'))
        for info in infos:
            self._find_display(info)

    ##############################################################
    # for ls

    def _ls_display(self, infos, dir_=None):
        if dir_:
            print dir_ + ':'
            for info in infos:
                self._find_display(info)
        else:
            self._find_display(infos)

    def _ls_directory(self, order, desc, path):
        directorys = [path.decode('utf8')]
        y = 1
        for dir_ in directorys:
            infos = self._get_file_list(order, desc, dir_.encode('utf8'))['list']
            if args.head or args.tail or args.include or args.exclude:
                infos = self._sift(infos)
            self._ls_display(infos, dir_)
            if args.recursive:
                subdirs = [i['path'] for i in infos if i['isdir']]
                directorys[y:y] = subdirs
                y += 1
            print ''

    def ls(self, order, desc, paths):
        for path in paths:
            meta = self._meta([path])
            if meta:
                if meta['info'][0]['isdir']:
                    self._ls_directory(order, desc, path)
                else:
                    self._ls_display(meta['info'][0])
            else:
                print s % (1, 91, '  !! path is not existed.\n'), \
                    ' --------------\n ', path

    ###############################################################
    # for file operate

    def _exist(self, list_):
        meta = self._meta(list_)
        if not meta:
            print s % (1, 91, '  !! Error at _exist, some paths are not existed.')
            sys.exit(1)

    def _filemanager(self, opera, data):
        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "opera": opera,
            "bdstoken": self._get_bdstoken(),
        }
        url = 'http://pan.baidu.com/api/filemanager'
        r = ss.post(url, params=p, data=data)
        j = r.json()
        if j['errno'] == 0:
            print s % (1, 92, '  ++ success.')
        else:
            print s % (1, 91, '  !! Error at filemanager')

    def move(self, paths, remotepath):
        self._exist(paths)

        meta = self._meta([remotepath])
        if not meta:
            self._make_dir(remotepath)
        elif not meta['info'][0]['isdir']:
            print s % (1, 91, '  !! Error at move:'), remotepath, s % (1, 91, 'is a file.')
            sys.exit(1)

        t = [{
                'path': i,
                'dest': remotepath,
                'newname': os.path.basename(i)
        } for i in paths]
        data = 'filelist=' + urllib.quote_plus(json.dumps(t))
        self._filemanager('move', data)

    def copy(self, paths, remotepath):
        self._exist(paths)

        t = None
        if len(paths) != 1:
            meta = self._meta([remotepath])
            if not meta:
                self._make_dir(remotepath)
            elif not meta['info'][0]['isdir']:
                print s % (1, 91, '  !! Error at move:'), remotepath, s % (1, 91, 'is a file.')
                sys.exit(1)

            t = [{
                    'path': i,
                    'dest': remotepath,
                    'newname': os.path.basename(i)
            } for i in paths]
        else:
            meta = self._meta([remotepath])
            if not meta:
                base_dir = os.path.split(remotepath)[0]
                meta = self._meta([base_dir])
                if not meta:
                    self._make_dir(base_dir)
                elif not meta['info'][0]['isdir']:
                    print s % (1, 91, '  !! Error at move:'), remotepath, s % (1, 91, 'is a file.')
                    sys.exit(1)
                t = [{
                        'path': i,
                        'dest':base_dir,
                        'newname': os.path.basename(remotepath)
                } for i in paths]
            elif not meta['info'][0]['isdir']:
                print s % (1, 91, '  !! Error at move:'), remotepath, s % (1, 91, 'is a file.')
                sys.exit(1)
            else:
                t = [{
                        'path': i,
                        'dest': remotepath,
                        'newname': os.path.basename(i)
                } for i in paths]

        data = 'filelist=' + urllib.quote_plus(json.dumps(t))
        self._filemanager('copy', data)

    def remove(self, paths):
        self._exist(paths)

        data = 'filelist=' + urllib.quote_plus(json.dumps(paths))
        self._filemanager('delete', data)

    def rename(self, path, remotepath):
        self._exist([path])

        meta = self._meta([remotepath])
        if meta:
            print s % (1, 91, '  !! Error at rename:'), remotepath, s % (1, 91, 'is existed.')
            sys.exit(1)

        base_dir = os.path.split(remotepath)[0]
        meta = self._meta([base_dir])
        if not meta:
            self._make_dir(base_dir)
        elif not meta['info'][0]['isdir']:
            print s % (1, 91, '  !! Error at rename:'), base_dir, s % (1, 91, 'is a file.')
            sys.exit(1)

        t = [{
                'path': path,
                'dest': base_dir,
                'newname': os.path.basename(remotepath)
        }]
        data = 'filelist=' + urllib.quote_plus(json.dumps(t))
        self._filemanager('move', data)

    ##############################################################
    # for add_task

    def _get_magnet_info(self, url):
        p = {
            "bdstoken": self._get_bdstoken(),
            "bdstoken": self._get_bdstoken(),
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "app_id": 250528,
        }
        data = {
            "method": "query_magnetinfo",
            "app_id": 250528,
            "source_url": url,
            "save_path": "/",
            "type": 4,
        }
        url = 'http://pan.baidu.com/rest/2.0/services/cloud_dl'
        r = ss.post(url, params=p, data=data)
        j = r.json()
        if j.get('error_code'):
            print s % (1, 91, '  !! Error at _get_magnet_info:'), j['error_msg']
            return None
        else:
            return j['magnet_info']

    def _get_selected_idx(self, magnet_info):
        mediatype = {".wma", ".wav", ".mp3", ".aac", ".ra", ".ram", ".mp2", ".ogg", ".aif", ".mpega", ".amr", ".mid", ".midi", ".m4a", ".wmv", ".rmvb", ".mpeg4", ".mpeg2", ".flv", ".avi", ".3gp", ".mpga", ".qt", ".rm", ".wmz", ".wmd", ".wvx", ".wmx", ".wm", ".swf", ".mpg", ".mp4", ".mkv", ".mpeg", ".mov"}
        imagetype = {".jpg", ".jpeg", ".gif", ".bmp", ".png", ".jpe", ".cur", ".svg", ".svgz", ".tif", ".tiff", ".ico"}
        doctype = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".vsd", ".txt", ".pdf", ".ods", ".ots", ".odt", ".rtf", ".dot", ".dotx", ".odm", ".pps", ".pot", ".xlt", ".xltx", ".csv", ".ppsx", ".potx", ".epub", ".apk", ".exe", ".msi", ".ipa", ".torrent", ".mobi"}
        archivetype = {".7z", ".a", ".ace", ".afa", ".alz", ".android", ".apk", ".ar", ".arc", ".arj", ".b1", ".b1", ".ba", ".bh", ".bz2", ".cab", ".cab", ".cfs", ".chm", ".cpio", ".cpt", ".cqm", ".dar", ".dd", ".dgc", ".dmg", ".ear", ".ecc", ".eqe", ".exe", ".f", ".gca", ".gz", ".ha", ".hki", ".html", ".ice", ".id", ".infl", ".iso", ".jar", ".kgb", ".lbr", ".lha", ".lqr", ".lz", ".lzh", ".lzma", ".lzo", ".lzx", ".mar", ".ms", ".net", ".package", ".pak", ".paq6", ".paq7", ".paq8", ".par", ".par2", ".partimg", ".pea", ".pim", ".pit", ".qda", ".rar", ".rk", ".rz", ".s7z", ".sda", ".sea", ".sen", ".sfark", ".sfx", ".shar", ".sit", ".sitx", ".sqx", ".tar", ".tbz2", ".tgz", ".tlz", ".tqt", ".uc", ".uc0", ".uc2", ".uca", ".ucn", ".ue2", ".uha", ".ur2", ".war", ".web", ".wim", ".x", ".xar", ".xp3", ".xz", ".yz1", ".z", ".zip", ".zipx", ".zoo", ".zpaq", ".zz"}

        if not args.type_:
            return []
        types = args.type_.split(',')
        idx = []
        if 'a' in types:
            return []
        if 'm' in types:
            for i in xrange(len(magnet_info)):
                idx.append(i+1) if os.path.splitext(magnet_info[i]['file_name'])[-1].lower() in mediatype else None
        if 'i' in types:
            for i in xrange(len(magnet_info)):
                idx.append(i+1) if os.path.splitext(magnet_info[i]['file_name'])[-1].lower() in imagetype else None
        if 'd' in types:
            for i in xrange(len(magnet_info)):
                idx.append(i+1) if os.path.splitext(magnet_info[i]['file_name'])[-1].lower() in doctype else None
        if 'p' in types:
            for i in xrange(len(magnet_info)):
                idx.append(i+1) if os.path.splitext(magnet_info[i]['file_name'])[-1].lower() in archivetype else None
        idx = list(set(idx))
        idx.sort()
        idx = [str(i) for i in idx]
        return idx

    def _add_magnet(self, url, remotepath):
        magnet_info = self._get_magnet_info(url)
        if not magnet_info:
            return
        selected_idx = self._get_selected_idx(magnet_info)

        p = {
            "bdstoken": self._get_bdstoken(),
            "bdstoken": self._get_bdstoken(),
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "app_id": 250528,
        }
        data = {
            "method": "add_task",
            "app_id": 250528,
            "file_sha1": "",
            "save_path": remotepath,
            "selected_idx": ",".join(selected_idx),
            "task_from": 1,
            "t": str(int(time.time())*1000),
            "source_url": url,
            "type": 4,
        }
        apiurl = 'http://pan.baidu.com/rest/2.0/services/cloud_dl'
        while True:
            r = ss.post(apiurl, params=p, data=data)
            j = r.json()
            if j.get('error_code') == -19:
                if data.get('vcode'):
                    print s % (2, 91, '  × 错误验证码')
                vcode = j['vcode']
                input_code = panbaiducom_HOME.save_img(j['img'], 'jpg')
                data.update({'input': input_code, 'vcode': vcode})
            elif j.get('error_code') != -19 and j.get('error_code'):
                print s % (1, 91, '  !! Error at _add_magnet:'), j['error_msg']
                return
            else:
                print s % (1 ,97, '  ++ rapid_download:'), s % (1, 91, j['rapid_download'])
                if args.view:
                    print ''
                    files = [os.path.join(remotepath, magnet_info[int(i) - 1]['file_name']) \
                        for i in selected_idx]
                    for i in files:
                        print i
                return

    def _add_task(self, url, remotepath):
        p = {
            "bdstoken": self._get_bdstoken(),
            "bdstoken": self._get_bdstoken(),
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "app_id": 250528,
        }
        data = {
            "method": "add_task",
            "app_id": 250528,
            "save_path": remotepath,
            "source_url": url,
            "type": 3,
        }
        apiurl = 'http://pan.baidu.com/rest/2.0/services/cloud_dl'
        while True:
            r = ss.post(apiurl, params=p, data=data)
            j = r.json()
            if j.get('error_code') == -19:
                if data.get('vcode'):
                    print s % (2, 91, '  × 错误验证码')
                vcode = j['vcode']
                input_code = panbaiducom_HOME.save_img(j['img'], 'jpg')
                data.update({'input': input_code, 'vcode': vcode})
            elif j.get('error_code'):
                print s % (1, 91, '  !! Error at _add_task:'), j['error_msg']
                return
            else:
                print s % (1 ,97, '  ++ rapid_download:'), s % (1, 91, j['rapid_download'])
                return

    def add_tasks(self, urls, remotepath):
        for url in urls:
            if url.startswith('magnet:'):
                args.type_ = 'm' if not args.type_ else args.type_  # default args.type_
                self._add_magnet(url, remotepath)
            elif url.startswith('http'):
                self._add_task(url, remotepath)
            elif url.startswith('ftp:'):
                self._add_task(url, remotepath)
            elif url.startswith('ed2k:'):
                self._add_task(url, remotepath)
            else:
                print s % (1, 91, '  !! url is wrong:'), url

    def do(self):
        self.get_infos()

class panbaiducom(object):
    def __init__(self, url):
        self.url = url
        self.infos = {}

    def get_params(self):
        r = ss.get(self.url)
        pattern = re.compile('server_filename="(.+?)";disk.util.ViewShareUtils.bdstoken="(\w+)";'
                             'disk.util.ViewShareUtils.fsId="(\d+)".+?FileUtils.share_uk="(\d+)";'
                             'FileUtils.share_id="(\d+)";.+?FileUtils.share_timestamp="(\d+)";'
                             'FileUtils.share_sign="(\w+)";')
        p = re.search(pattern, r.text)

        self.params = {
            "bdstoken": p.group(2),
            "uk": p.group(4),
            "shareid": p.group(5),
            "timestamp": p.group(6),
            "sign": p.group(7),
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1
        }

        self.infos.update({
            'name': p.group(1).encode('utf8'),
            'file': os.path.join(os.getcwd(), p.group(1)).encode('utf8'),
            'dir_': os.getcwd(),
            'fs_id': p.group(3).encode('utf8')
            })

    def get_infos(self):
        url = 'http://pan.baidu.com/share/download'
        data = 'fid_list=["%s"]' % self.infos['fs_id']

        while True:
            r = ss.post(url, data=data, params=self.params)
            j = r.json()
            if not j['errno']:
                self.infos['dlink'] = j['dlink'].encode('utf8')
                if args.play:
                    panbaiducom_HOME.play(self.infos)
                else:
                    panbaiducom_HOME.download(self.infos)
                break
            else:
                vcode = j['vcode']
                input_code = panbaiducom_HOME.save_img(j['img'], 'jpg')
                self.params.update({'input': input_code, 'vcode': vcode})

    def get_infos2(self):
        url = self.url

        while True:
            r = ss.get(url)
            j = r.content.replace('\\', '')
            name = re.search(r'server_filename":"(.+?)"', j).group(1)
            dlink = re.search(r'dlink":"(.+?)"', j)
            if dlink:
                self.infos = {
                    'name': name,
                    'file': os.path.join(os.getcwd(), name),
                    'dir_': os.getcwd(),
                    'dlink': dlink.group(1)
                }
                if args.play:
                    panbaiducom_HOME.play(self.infos)
                else:
                    panbaiducom_HOME.download(self.infos)
                break
            else:
                print s % (1, '  !! Error at get_infos2, can\'t get dlink')

    def do(self):
        panbaiducom_HOME._secret_or_not(self.url)
        self.get_params()
        self.get_infos()

    def do2(self):
        self.get_infos2()

def sighandler(signum, frame):
    print s % (1, 91, "  !! Signal %s received, Abort" % signum)
    print s % (1, 91, "  !! Frame: %s" % frame)
    sys.exit(1)

def main(argv):
    signal.signal(signal.SIGBUS, sighandler)
    signal.signal(signal.SIGHUP, sighandler)
    # https://stackoverflow.com/questions/108183/how-to-prevent-sigpipes-or-handle-them-properly
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    signal.signal(signal.SIGQUIT, sighandler)
    signal.signal(signal.SIGSYS, sighandler)

    signal.signal(signal.SIGABRT, sighandler)
    signal.signal(signal.SIGFPE, sighandler)
    signal.signal(signal.SIGILL, sighandler)
    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGSEGV, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    usage = """
 usage: https://github.com/PeterDing/iScript#pan.baidu.com.py

 命令:
 d  或 download url1 url2 ..                          下载
 u  或 upload localpath remotepath                    上传
 s  或 save url remotepath [-s secret]                转存
 rn 或 rename path new_path                           重命名
 rm 或 remove path1 path2 ..                          删除
 mv 或 move path1 path2 .. /path/to/directory         移动
 cp 或 copy path /path/to/directory_or_file           复制
 cp 或 copy path1 path2 .. /path/to/directory         复制
 a  或 add url1 url2 .. [remotepath] [-t {m,d,p,a}]   离线下载

 f   或 find keyword .. [directory]             非递归搜索
 ff  keyword .. [directory]                     非递归搜索 反序
 ft  keyword .. [directory]                     非递归搜索 by time
 ftt keyword .. [directory]                     非递归搜索 by time 反序
 fs  keyword .. [directory]                     非递归搜索 by size
 fss keyword .. [directory]                     非递归搜索 by size 反序
 fn  keyword .. [directory]                     非递归搜索 by name
 fnn keyword .. [directory]                     非递归搜索 by name 反序
 # 递归搜索加 -R
 # 关于-H, -T, -I, -E
 f -H head -T tail -I "re(gul.*) ex(p|g)ress$" keyword ... [directory]
 f -H head -T tail -E "re(gul.*) ex(p|g)ress$" keyword ... [directory]

 l path1 path2 ..                               ls by name
 ll path1 path2 ..                              ls by name 反序
 ln path1 path2 ..                              ls by name
 lnn path1 path2 ..                             ls by name 反序
 lt path1 path2 ..                              ls by time
 ltt path1 path2 ..                             ls by time 反序
 ls path1 path2 ..                              ls by size
 lss path1 path2 ..                             ls by size 反序

 # sl 是以上ls命令中的一个.
 # 以下是只ls文件或文件夹
 sl -t f path1 path2 ..                            ls files
 sl -t d path1 path2 ..                            ls directorys
 # 关于-H, -T, -I, -E
 sl -H head -T tail -I "^re(gul.*) ex(p|g)ress$" path1 path2 ..
 sl -H head -T tail -E "^re(gul.*) ex(p|g)ress$" path1 path2 ..

 # magnet离线下载 -- 文件选择
 # -t m    # 媒体文件, 如: mkv, avi ..etc
 # -t i    # 图像文件, 如: jpg, png ..etc
 # -t d    # 文档文件, 如: pdf, doc, docx, epub, mobi ..etc
 # -t p    # 压缩文件, 如: rar, zip ..etc
 # -t a    # 所有文件 (默认)
 # m, i, d, p, a 可以任意组合(用,分隔), 如: -t m,i,d   -t m,p   -t m,d,p
 # remotepath 默认为 /
 a magnet1 magnet2 .. [remotepath] -t m,i,d,p,a
        """
    if len(argv) <= 1:
        print usage
        sys.exit()

    ######################################################
    # for argparse
    p = argparse.ArgumentParser(description='about pan.baidu.com.' \
        ' 用法见 https://github.com/PeterDing/iScript')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-a', '--aria2c', action='store', default=None, \
        type=int, help='aria2c分段下载数量')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-v', '--view', action='store_true', \
        help='view details')
    p.add_argument('-s', '--secret', action='store', \
        default=None, help='提取密码')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    p.add_argument('-t', '--type_', action='store', \
        default=None, type=str, \
        help='类型参数，eg: -t mp3. 或者ls 文件(f)、文件夹(d)的参数')
    p.add_argument('-l', '--limit', action='store', \
        default=None, type=str, help='下载速度限制，eg: -l 100k')
    # for upload
    p.add_argument('-m', '--uploadmode', action='store', \
        default='c', type=str, choices=['o', 'c'], \
        help='上传模式: o --> 重传. c --> 续传 .')
    # for recurse, head, tail, include, exclude
    p.add_argument('-R', '--recursive', action='store_true', \
        help='递归 ls')
    p.add_argument('-H', '--head', action='store', \
        default=None, type=str, help='匹配开头的字符，eg: -H Headishere')
    p.add_argument('-T', '--tail', action='store', \
        default=None, type=str, help='匹配结尾的字符，eg: -T Tailishere')
    p.add_argument('-I', '--include', action='store', \
        default=None, type=str, help='不排除匹配到表达的文件名, 可以是正则表达式，eg: -I "*.mp3"')
    p.add_argument('-E', '--exclude', action='store', \
        default=None, type=str, help='排除匹配到表达的文件名, 可以是正则表达式，eg: -E "*.html"')
    p.add_argument('-c', '--ls_color', action='store', default='on', \
        choices=['on', 'off'], type=str, help='递归 ls')
    global args
    args = p.parse_args(argv[2:])
    comd = argv[1]
    xxx = args.xxx
    #######################################################

    if comd == 'u' or comd == 'upload':
        if len(xxx) < 2:
            print s % (1, 91, '  !! 参数错误\n  upload localpath1 localpath2 .. remotepath\n' \
                '  u localpath1 localpath2 .. remotepath')
            sys.exit(1)
        x = panbaiducom_HOME()
        x.init()
        x.upload(xxx[:-1], xxx[-1])

    elif comd == 'd' or comd == 'download':
        if len(xxx) < 1:
            print s % (1, 91, '  !! 参数错误\n download url1 url2 ..\n' \
                '  d url1 url2 ..')
            sys.exit(1)
        urls = xxx
        for url in urls:
            if url[0] == '/':
                url = 'path=%s' % url
            if '/disk/home' in url or 'path' in url:
                x = panbaiducom_HOME(url)
                x.init()
                x.do()
            elif 'baidu.com/pcloud/album/file' in url:
                x = panbaiducom(url)
                x.do2()
            elif 'yun.baidu.com' in url or 'pan.baidu.com' in url:
                url = url.replace('wap/link', 'share/link')
                x = panbaiducom(url)
                x.do()
            else:
                print s % (2, 91, '  !!! url 地址不正确.'), url

    elif comd == 's' or comd == 'save':
        if len(xxx) != 2:
            print s % (1, 91, '  !! 参数错误\n save url remotepath\n' \
                ' s url remotepath')
            sys.exit(1)
        x = panbaiducom_HOME(xxx[0])
        x.init()
        remotepath = xxx[1].decode('utf8')
        infos = []
        if x.path != '/':
            infos.append({'isdir': 1, 'path': x.path.decode('utf8'), \
            'remotepath': remotepath if remotepath[-1] != '/' else remotepath[:-1]})
        else:
            infos = None
        if '/inbox/' in xxx[0]:
            url = xxx[0]
            x.save_inbox_share(url, remotepath, infos=infos)
        else:
            url = re.search(r'(http://.+?.baidu.com/.+?)(#|$)', xxx[0]).group(1)
            x._secret_or_not(url)
            x.save_share(url, remotepath, infos=infos)

    elif comd == 'f' or comd == 'find' or comd == 'ff' \
        or comd == 'ft' or comd == 'ftt' \
        or comd == 'fs' or comd == 'fss' \
        or comd == 'fn' or comd == 'fnn':
        if len(xxx) < 1:
            print s % (1, 91, '  !! 参数错误\n find keyword [directory]\n' \
                ' f keyword [directory]')
            sys.exit(1)
        x = panbaiducom_HOME()
        x.init()
        keyword = ''
        directory = None
        if xxx[-1][0] == '/':
            keyword = ' '.join(xxx[:-1])
            directory = xxx[-1]
        else:
            keyword = ' '.join(xxx)

        if comd == 'f' or comd == 'find':
            x.find(keyword, desc=None, directory=directory)
        elif comd == 'ff':
            x.find(keyword, desc=1, directory=directory)
        elif comd == 'ft':
            x.find(keyword, desc=None, time='no_reverse', directory=directory)
        elif comd == 'ftt':
            x.find(keyword, desc=1, time='reverse', directory=directory)
        elif comd == 'fs':
            x.find(keyword, desc=None, size='no_reverse', directory=directory)
        elif comd == 'fss':
            x.find(keyword, desc=1, size='reverse', directory=directory)
        elif comd == 'fn':
            x.find(keyword, desc=None, name='no_reverse', directory=directory)
        elif comd == 'fnn':
            x.find(keyword, desc=1, name='reverse', directory=directory)

    elif comd == 'mv' or comd == 'move' \
        or comd == 'rm' or comd == 'remove' \
        or comd == 'cp' or comd == 'copy' \
        or comd == 'rn' or comd == 'rename' \
        or comd == 'l' or comd == 'll' \
        or comd == 'ln' or comd == 'lnn'\
        or comd == 'ls' or comd == 'lss' \
        or comd == 'lt' or comd == 'ltt':
        if len(xxx) < 1:
            print s % (1, 91, '  !! 参数错误\n move path1 path2 .. /path/to/directory\n' \
                ' mv path1 path2 .. /path/to/directory\n' \
                ' remove path1 path2 ..\n' \
                ' rm path1 path2 ..\n' \
                ' rename path new_path\n' \
                ' rn path new_path\n' \
                ' rename path new_path\n' \
                ' cp path1 path2 /copy/to/directory\n' \
                ' cp path /copy/to/existed_directory/newname\n' \
                ' l path1 path2 ..\n' \
                ' ls path1 path2 ..\n')
            sys.exit(1)
        e = True if 'f' in ['f' for i in xxx if i[0] != '/'] else False
        if e:
            print s % (1, 91, '  !! path is incorrect.')
            sys.exit(1)
        x = panbaiducom_HOME()
        x.init()
        if comd == 'mv' or comd == 'move':
            x.move(xxx[:-1], xxx[-1])
        elif comd == 'rm' or comd == 'remove':
            x.remove(xxx)
        elif comd == 'cp' or comd == 'copy':
            x.copy(xxx[:-1], xxx[-1])
        elif comd == 'rn' or comd == 'rename':
            x.rename(xxx[0], xxx[1])
        elif comd == 'l' or comd == 'ln':
            x.ls('name', None, xxx)
        elif comd == 'll' or comd == 'lnn':
            x.ls('name', 1, xxx)
        elif comd == 'lt':
            x.ls('time', None, xxx)
        elif comd == 'ltt':
            x.ls('time', 1, xxx)
        elif comd == 'ls':
            x.ls('size', None, xxx)
        elif comd == 'lss':
            x.ls('size', 1, xxx)

    elif comd == 'a' or comd == 'add':
        if len(xxx) < 1:
            print s % (1, 91, '  !! 参数错误\n add url1 url2 .. [directory]\n' \
                ' a url1 url2 .. [directory]\n' \
                ' a url1 url2 .. [directory] [-t {m,d,p,a}]')
            sys.exit(1)
        if xxx[-1].startswith('/'):
            remotepath = xxx[-1] if xxx[-1][-1] == '/' else xxx[-1] + '/'
            urls = xxx[:-1]
        else:
            remotepath = '/'
            urls = xxx
        x = panbaiducom_HOME()
        x.init()
        x.add_tasks(urls, remotepath)

    else:
        print s % (2, 91, '  !! 命令错误\n')

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
