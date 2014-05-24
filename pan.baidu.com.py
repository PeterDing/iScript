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
import binascii
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

s = '\x1b[1;%dm%s\x1b[0m'       # terminual color template

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
                print s % (92, '  -- login success\n')
            else:
                print s % (91, '  !! login fail, maybe username or password is wrong.\n')
                print s % (91, '  !! maybe this app is down.')
                sys.exit(1)

        if os.path.exists(cookie_file):
            t = json.loads(open(cookie_file).read())
            if t.get('user') != None and t.get('user') == username:
                ss.cookies.update(t.get('cookies', t))
                if not self.check_login():
                    loginandcheck()
            else:
                print s % (91, '\n  ++  username changed, then relogin')
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
        print "  ++ 验证码已经保存至", s % (91, path)
        input_code = raw_input(s % (92, "  请输入看到的验证码: "))
        return input_code

    def check_login(self):
        print s % (97, '\n  -- check_login')
        url = 'http://www.baidu.com/home/msg/data/personalcontent'
        j = ss.get(url)
        if 'errNo":"0' in j.text:
            print s % (92, '  -- check_login success\n')
            #self.get_dsign()
            self.save_cookies()
            return True
        else:
            print s % (91, '  -- check_login fail\n')
            return False

    def login(self):
        print s % (97, '\n  -- login')

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

    def _get_file_list(self, dir_):
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
            #"desc": 1,   ## reversely
            "order": "name", ## sort by name, or size, time
            "_": int(time.time()*1000)
            #"bdstoken": token
        }
        url = 'http://pan.baidu.com/api/list'
        j = ss.get(url, params=p, headers=theaders).json()
        if j['errno'] != 0:
            print s % (91, '  error: get_infos'), '--', j
            sys.exit(1)
        else:
            return j

    def get_infos(self):
        dir_loop = [self.path]
        base_dir = '' if os.path.split(self.path)[0] == '/' \
            else os.path.split(self.path)[0]
        for d in dir_loop:
            j = self._get_file_list(d)
            if j['errno'] == 0 and j['list']:
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
                            i['dlink'] = self._get_dlink(i)
                        infos = {
                            'file': t,
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
                j = self._get_file_list(self.path)
                if j['errno'] == 0 and j['list']:
                    for i in j['list']:
                        if i['server_filename'].encode('utf8') == server_filename:
                            if i['isdir']: break
                            t =  os.path.join(os.getcwd(), server_filename)
                            if not i.has_key('dlink'):
                                i['dlink'] = self._get_dlink(i)
                            infos = {
                                'file': t,
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

    @staticmethod
    def download(infos):
        ## make dirs
        if not os.path.exists(infos['dir_']):
            os.makedirs(infos['dir_'])
        else:
            if os.path.exists(infos['file']):
                return 0

        num = random.randint(0, 7) % 7
        col = s % (num + 90, infos['file'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] if infos.get('total_file') else 1
        print '\n  ++ 正在下载: #', s % (97, infos['nn']), '/', s % (97, infos['total_file']), '#', col

        if args.aria2c:
            if args.limit:
                cmd = 'aria2c -c -x%s -s%s ' \
                    '--max-download-limit %s ' \
                    '-o "%s.tmp" -d "%s" \
                    --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (args.aria2c, args.aria2c, args.limit, infos['name'], \
                    infos['dir_'], headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'aria2c -c -x%s -s%s ' \
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
            print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> '\
                '\x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
                 % (status, wget_exit_status_info))
            print s % (91, '  ===> '), cmd
            sys.exit(1)
        else:
            os.rename('%s.tmp' % infos['file'], infos['file'])

    @staticmethod
    def play(infos):
        num = random.randint(0, 7) % 7
        col = s % (num + 90, infos['name'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] if infos.get('total_file') else 1
        print '\n  ++ play: #', s % (97, infos['nn']), '/', \
            s % (97, infos['total_file']), '#', col

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

    def meta(self, file_list):
        p = {
            "channel": "chunlei",
            "app_id": "250528",
            "method": "filemetas",
            "blocks": 1
        }
        data = {'target': json.dumps(file_list)}
        url = 'http://pan.baidu.com/api/filemetas'
        r = ss.post(url, params=p, data=data, verify=False)
        if r.ok:
            if r.json()['errno']:
                return False
        else:
            print s % (91, '  !! Error at exists')

    def _rapidupload_file(self, lpath, rpath):
        print '  |-- upload_function:', s % (97, '_rapidupload_file')
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
        print '  |-- upload_function:', s % (97, '_upload_one_file')
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
                print s % (91, '  !! file is too big, uploading is not supported.')
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
                    print s % (91, '  !! Error: size of file is too big.')
                    return 'None'
        else:
            return '_upload_one_file'

    def _upload_file(self, lpath, rpath):
        print s % (94, '  ++ uploading:'), lpath

        __current_file_size = os.path.getsize(lpath)
        self.__current_file_size = __current_file_size
        upload_function = self._get_upload_function()

        if self.upload_datas.has_key(lpath):
            if __current_file_size != self.upload_datas[lpath]['size']:
                self.upload_datas[lpath]['is_over'] = False
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
                    print '  |-- upload_function:', s % (97, '_upload_file_slices')
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
                                    print s % (91, '  |-- slice_md5 does\'n match, retry.')
                            self.upload_datas[lpath]['slice_md5s'].append(self.__slice_md5)
                            self.save_upload_datas()
                            percent = round(100*((piece + 1.0) / pieces), 2)
                            print s % (97, '  |-- upload: %s%s' % (percent, '%')), piece + 1, '/', pieces
                    result = self._combine_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        del self.upload_datas[lpath]['slice_md5s']
                        self.save_upload_datas()
                        print s % (92, '  |-- success.\n')
                        break
                    else:
                        print s % (91, '  !! Error at _combine_file')

                elif m == '_upload_one_file':
                    time.sleep(2)
                    result = self._upload_one_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        self.save_upload_datas()
                        print s % (92, '  |-- success.\n')
                        break
                    else:
                        print s % (91, '  !! Error: _upload_one_file is fall, retry.')

                elif m == '_rapidupload_file':
                    time.sleep(2)
                    result = self._rapidupload_file(lpath, rpath)
                    if result == ENoError:
                        self.upload_datas[lpath]['is_over'] = True
                        self.upload_datas[lpath]['remotepaths'].update([rpath])
                        self.save_upload_datas()
                        print s % (92, '  |-- RapidUpload: Success.\n')
                        break
                    else:
                        print s % (93, '  |-- can\'t be RapidUploaded, ' \
                            'now trying normal uploading.')
                        upload_function = self._get_upload_function(rapidupload_is_fall=True)
                        self.upload_datas[lpath]['upload_function'] = upload_function
                        if upload_function == '_upload_file_slices':
                            if not self.upload_datas[lpath].has_key('slice_md5s'):
                                self.upload_datas[lpath]['slice_md5s'] = []

                else:
                    print s % (91, '  !! Error: size of file is too big.')
                    break

            else:
                if args.uploadmode == 'c':
                    if rpath in self.upload_datas[lpath]['remotepaths']:
                        print s % (92, '  |-- file was uploaded.\n')
                        break
                    else:
                        self.upload_datas[lpath]['is_over'] = False
                elif args.uploadmode == 'o':
                    print s % (93, '  |-- reupload.')
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

    def upload(self, localpath, remotepath):
        lpath = localpath
        if localpath[0] == '~':
            lpath = os.path.expanduser(localpath)
        else:
            lpath = os.path.abspath(localpath)
        rpath = remotepath if remotepath[0] == '/' else '/' + remotepath

        if os.path.exists(lpath):
            pass
        else:
            print s % (91, '  !! Error: localpath doesn\'t exist')
            sys.exit(1)

        self.upload_datas_path = upload_datas_path
        self.upload_datas = {}
        if os.path.exists(self.upload_datas_path):
            f = open(self.upload_datas_path, 'rb')
            upload_datas = pk.load(f)
            if upload_datas:
                self.upload_datas = upload_datas

        if os.path.isdir(lpath):
            self._upload_dir(lpath, rpath)
        elif os.path.isfile(lpath):
            self._upload_file(lpath, rpath)
        else:
            print s % (91, '  !! Error: localpath ?')
            sys.exit(1)

    def save_upload_datas(self):
        f = open(self.upload_datas_path, 'wb')
        pk.dump(self.upload_datas, f)

    def do(self):
        self.get_infos()

class panbaiducom(object):
    def __init__(self, url):
        self.url = url
        self.secret = args.secret
        self.infos = {}

    def secret_or_not(self):
        r = ss.get(self.url)
        if 'init' in r.url:
            if not self.secret:
                self.secret = raw_input(s % (92, "  请输入提取密码: "))
            data = 'pwd=%s' % self.secret
            url = "%s&t=%d" % (r.url.replace('init', 'verify'), int(time.time()))
            r = ss.post(url, data=data)
            if r.json()['errno']:
                print s % (91, "  !! 提取密码错误\n")
                sys.exit(1)

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
                print s % ('  !! Error at get_infos2, can\'t get dlink')

    def do(self):
        self.secret_or_not()
        self.get_params()
        self.get_infos()

    def do2(self):
        self.get_infos2()

def sighandler(signum, frame):
    print s % (91, "  !! Signal %s received, Abort" % signum)
    print s % (91, "  !! Frame: %s" % frame)
    sys.exit(1)

def main(xxx):
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

    if xxx[0] == 'u' or xxx[0] == 'upload':
        if len(xxx) != 3:
            print s % (91, '  !! 参数错误\n  upload localpath remotepath\n' \
                '  u upload localpath remotepath')
            sys.exit(1)
        x = panbaiducom_HOME()
        x.init()
        x.upload(xxx[1], xxx[2])
        return

    elif xxx[0] == 'd' or xxx[0] == 'download':
        if len(xxx) < 2:
            print s % (91, '  !! 参数错误\n download url1 url2 ..\n' \
                '  d url1 url2 ..')
            sys.exit(1)
        urls = [url.replace('wap/link', 'share/link') for url in xxx[1:]]
        for url in urls:
            if '/disk/' in url or 'path' in url:
                x = panbaiducom_HOME(url)
                x.init()
                x.do()
            elif 'baidu.com/pcloud/album/file' in url:
                x = panbaiducom(url)
                x.do2()
            elif 'yun.baidu.com' in url or 'pan.baidu.com' in url:
                x = panbaiducom(url)
                x.do()
            else:
                print s % (91, '  !!! url 地址不正确.'), url
    else:
        print s % (91, '  !! 命令错误\n')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='download from pan.baidu.com')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令和参数.\nd, download\turl\nu, upload localpath remotepath')
    p.add_argument('-a', '--aria2c', action='store', default=None, \
        type=int, help='aria2c分段下载数量')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-s', '--secret', action='store', \
        default=None, help='提取密码')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    p.add_argument('-t', '--type_', action='store', \
        default=None, type=str, \
        help='要下载的文件的后缀，eg: -t mp3')
    p.add_argument('-l', '--limit', action='store', \
        default=None, type=str, help='下载速度限制，eg: -l 100k')
    # for upload
    p.add_argument('-m', '--uploadmode', action='store', \
        default='c', type=str, choices=['o', 'c'], \
        help='上传模式: o --> 重传. c --> 续传.')
    args = p.parse_args()
    main(args.xxx)
