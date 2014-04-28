#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
import requests
import urllib
import json
import re
import time
import argparse
import random
import select


username = ''
password = ''


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

cookie_file = os.path.join(os.path.expanduser('~'), '.bpp.cookie')

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

    def init(self):
        if os.path.exists(cookie_file):
            t = json.loads(open(cookie_file).read())
            ss.cookies.update(t)
            if not self.check_login():
                self.login()
        else:
            self.login()

    def get_path(self, url):
        url = urllib.unquote(url)
        #print repr(url)
        f = re.search(r'path=(.+?)(&|$)', url)
        #print f.group(1)
        #sys.exit()
        if f:
            return f.group(1)
        else:
            return '/'

    def getvcode(self, codestring):
        url = 'https://passport.baidu.com/cgi-bin/genimage?'+codestring
        r = requests.get(url).content
        with open('vcode.gif','wb') as f:
            f.write(r)
        p = os.popen('feh vcode.gif')
        ret = input('vcode?')
        p.terminate()
        return ret

    def check_login(self):
        print s % (97, '\n  -- check_login')
        url = 'http://www.baidu.com/home/msg/data/personalcontent'
        j = ss.get(url)
        if 'errNo":"0' in j.text:
            print s % (92, '  -- check_login success\n')
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
        codestring = r.text[r.text.index('(')+1:r.text.index(')')]
        codestring = json.loads(codestring)['codestring']
        codestring = codestring if codestring != "null" else None
        verifycode = (self.getvcode(codestring)) if codestring != None else ""

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
        r = ss.post(url, data=data)
        self.save_cookies()
        print s % (92, '  -- login success\n')

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            g.write(json.dumps(ss.cookies.get_dict(), indent=4, \
                sort_keys=True))

    def get_infos(self):
        t = {'Referer':'http://pan.baidu.com/disk/home'}
        ss.headers.update(t)

        params = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "num": 10000,   ## max amount of listed file at one page
            "t": int(time.time()*1000),
            "page": 1,
            #"desc": 1,   ## reversely
            "order": "name", ## sort by name, or size, time
            "_": int(time.time()*1000)
            #"bdstoken": token
        }
        url = 'http://pan.baidu.com/api/list'

        dir_loop = [self.path]
        base_dir = os.path.split(self.path)[0]
        for d in dir_loop:
            params['dir'] = d
            j = ss.get(url, params=params).json()
            if j['errno'] == 0 and j['list']:
                if args.type_:
                    j['list'] = [x for x in j['list'] if x['isdir'] \
                        or x['server_filename'][-len(args.type_):] \
                        == unicode(args.type_)]
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
                        infos = {
                            'file': t,
                            'dir_': os.path.split(t)[0],
                            'dlink': i['dlink'].encode('utf8'),
                            'name': i['server_filename'].encode('utf8'),
                            'nn': nn
                        }
                        nn += 1
                        self.download(infos)
            elif j['errno'] != 0:
                print s % (91, '  error: get_infos')
                sys.exit(0)
            elif not j['list']:
                self.path, server_filename = os.path.split(self.path)
                params['dir'] = self.path
                j = ss.get(url, params=params).json()
                if j['errno'] == 0 and j['list']:
                    for i in j['list']:
                        if i['server_filename'].encode('utf8') == server_filename:
                            t =  os.path.join(os.getcwd(), server_filename)
                            infos = {
                                'file': t,
                                'dir_': os.path.split(t)[0],
                                'dlink': i['dlink'].encode('utf8'),
                                'name': i['server_filename'].encode('utf8'),
                                'nn': 1
                            }
                            self.download(infos)
                            break

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
        print '\n  ++ 正在下载: #', s % (97, infos['nn']), '#', col

        if args.aria2c:
            if args.limit:
                cmd = 'aria2c -c -x10 -s10 ' \
                    '--max-download-limit %s ' \
                    '-o "%s.tmp" -d "%s" \
                    --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (args.limit, infos['name'], infos['dir_'],\
                        headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'aria2c -c -x10 -s10 ' \
                    '-o "%s.tmp" -d "%s" --user-agent "%s" ' \
                    '--header "Referer:http://pan.baidu.com/disk/home" "%s"' \
                    % (infos['name'], infos['dir_'], headers['User-Agent'], \
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
        print '\n  ++ play: #', s % (97, infos['nn']), '#', col

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

    def exists(self, filepath):
        url = 'http://pan.baidu.com/api/filemanager'

        p = {
            "channel": "chunlei",
            "clienttype": 0,
            "web": 1,
            "opera": "rename"
        }

        data = '[{"path": "%s", "newname": "%s"}]' % (filepath, os.path.split(filepath)[-1])
        data = 'filelist=' + urllib.quote_plus(data)

        r = ss.post(url, params=p, data=data, verify=False)
        if r.ok:
            if r.json()['errno']:
                return False
        else:
            print s % (91, '  !! Error at exists')

    def upload(self, path, dir_):
        url = 'https://c.pcs.baidu.com/rest/2.0/pcs/file'
        path = os.path.expanduser(path)

        p = {
            "method": "upload",
            "app_id": "250528",
            "ondup": "overwrite",
            "dir": dir_,
            "filename": os.path.split(path)[-1],
            "BDUSS": ss.cookies['BDUSS'],
        }

        files = {'file': ('file', open(path, 'rb'), '')}

        data = MultipartEncoder(files)

        theaders = headers
        theaders['Content-Type'] = data.content_type

        r = ss.post(url, params=p, data=data, verify=False, headers=theaders)
        if r.ok:
            print s % (92, '  ++ upload success,'), "path:", s % (97, r.json()['path'].encode('utf8'))
        else:
            print s % (91, '  !! Error at upload')

    def do(self):
        self.get_infos()
        #self.exists('/aa/a')

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
                self.save_img(j['img'])
                input_code = raw_input(s % (92, "  请输入看到的验证码: "))
                self.params.update({'input': input_code, 'vcode': vcode})

    def save_img(self, url):
        path = os.path.join(os.path.expanduser('~'), 'vcode.jpg')
        with open(path, 'w') as g:
            data = urllib.urlopen(url).read()
            g.write(data)
        print "  ++ 验证码已经保存至", s % (91, path)

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

def main(url):
    url = url.replace('wap/link', 'share/link')
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
        print s % (91, '  !!! url 地址不正确.')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='download from pan.baidu.com')
    p.add_argument('url', help='eg: http://pan.baidu.com/s/1gdutU3S, '\
        'http://pan.baidu.com/disk/home# '\
        'dir/path=/tmp/\xe5\x90\x8d\xe4\xbe\xa6\xe6\x8e\xa2\xe6\x9f\xaf\xe5\x8d\x97')
    p.add_argument('-a', '--aria2c', action='store_true', \
        help='download with aria2c')
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
    args = p.parse_args()
    main(args.url)
