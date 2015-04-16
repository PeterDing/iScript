#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
from getpass import getpass
import requests
import urllib
import json
import re
import time
import argparse
import random
import md5

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

cookie_file = os.path.join(os.path.expanduser('~'), '.360.cookies')

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "Referer":"http://yunpan.360.cn/",
    "X-Requested-With":"XMLHttpRequest",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

class yunpan360(object):
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

    def get_path(self, url):
        url = urllib.unquote_plus(url)
        f = re.search(r'#(.+?)(&|$)', url)
        if f:
            return f.group(1)
        else:
            return '/'

    def check_login(self):
        #print s % (1, 97, '\n  -- check_login')
        url = 'http://yunpan.360.cn/user/login?st=774'
        r = ss.get(url)
        self.save_cookies()

        if r.ok:
            #print s % (1, 92, '  -- check_login success\n')

            # get apihost
            self.apihost = re.search(r'http://(.+?)/', r.url).group(1).encode('utf8')
            self.save_cookies()
            return True
        else:
            print s % (1, 91, '  -- check_login fail\n')
            return False

    def login(self, username, password):
        print s % (1, 97, '\n  -- login')

        # get token
        params = {
            "o": "sso",
            "m": "getToken",
            "func": "QHPass.loginUtils.tokenCallback",
            "userName": username,
            "rand": random.random()
        }
        url = 'https://login.360.cn'
        r = ss.get(url, params=params)
        token = re.search(r'token":"(.+?)"', r.content).group(1)

        # now loin
        params = {
            "o": "sso",
            "m": "login",
            "requestScema": "http",
            "from": "pcw_cloud",
            "rtype": "data",
            "func": "QHPass.loginUtils.loginCallback",
            "userName": username,
            "pwdmethod": 1,
            "isKeepAlive": 0,
            "token": token,
            "captFlag": 1,
            "captId": "i360",
            "captCode": "",
            "lm": 0,
            "validatelm": 0,
            "password": md5.new(password).hexdigest(),
            "r": int(time.time()*1000)
        }
        url = 'https://login.360.cn'
        ss.get(url, params=params)
        self.save_cookies()

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            c = {'cookies': ss.cookies.get_dict()}
            g.write(json.dumps(c, indent=4, sort_keys=True))

    def get_dlink(self, i):
        data = 'nid=%s&fname=%s&' % (i['nid'].encode('utf8'), \
            urllib.quote_plus(i['path'].encode('utf8')))
        apiurl = 'http://%s/file/download' % self.apihost
        r = ss.post(apiurl, data=data)
        j = r.json()
        if j['errno'] == 0:
            dlink = j['data']['download_url'].encode('utf8')
            return dlink

    def fix_json(self, ori):
        # 万恶的 360，返回的json尽然不合法。
        jdata = re.search(r'data:\s*\[.+?\]', ori).group()
        jlist = re.split(r'\}\s*,\s*\{', jdata)
        jlist = [l for l in jlist if l.strip()]
        j = []
        for item in jlist:
            nid = re.search(r',nid: \'(\d+)\'', item)
            path = re.search(r',path: \'(.+?)\',nid', item)
            name = re.search(r'oriName: \'(.+?)\',path', item)
            isdir = 'isDir: ' in item
            if nid:
                t = {
                    'nid': nid.group(1),
                    'path': path.group(1).replace("\\'", "'"),
                    'name': name.group(1).replace("\\'", "'"),
                    'isdir': 1 if isdir else 0
                }
                j.append(t)
        return j

    def get_infos(self):
        apiurl = 'http://%s/file/list' % self.apihost
        data = "type" + "=2" + "&" \
            "t" + "=%s" % random.random() + "&" \
            "order" + "=asc" + "&" \
            "field" + "=file_name" + "&" \
            "path" + "=%s" + "&" \
            "page" + "=0" + "&" \
            "page_size" + "=10000" + "&" \
            "ajax" + "=1"

        dir_loop = [self.path]
        base_dir = os.path.split(self.path[:-1])[0] if self.path[-1] == '/' \
            and self.path != '/' else os.path.split(self.path)[0]
        for d in dir_loop:
            data = data % urllib.quote_plus(d)
            r = ss.post(apiurl, data=data)
            j = self.fix_json(r.text.strip())
            if j:
                if args.type_:
                    j = [x for x in j if x['isdir'] \
                        or x['name'][-len(args.type_):] \
                        == unicode(args.type_)]
                total_file = len([i for i in j if not i['isdir']])
                if args.from_ - 1:
                    j = j[args.from_-1:] if args.from_ else j
                nn = args.from_
                for i in j:
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
                            'dlink': self.get_dlink(i),
                            'name': i['name'].encode('utf8'),
                            'apihost': self.apihost,
                            'nn': nn,
                            'total_file': total_file
                        }
                        nn += 1
                        self.download(infos)
            else:
                print s % (1, 91, '  error: get_infos')
                sys.exit(0)

    @staticmethod
    def download(infos):
        #### !!!! 注意：360不支持断点续传

        ## make dirs
        if not os.path.exists(infos['dir_']):
            os.makedirs(infos['dir_'])
        else:
            if os.path.exists(infos['file']):
                return 0

        num = random.randint(0, 7) % 8
        col = s % (2, num + 90, infos['file'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] if infos.get('total_file') else 1
        print '\n  ++ 正在下载: #', s % (1, 97, infos['nn']), '/', s % (1, 97, infos['total_file']), '#', col

        cookie = '; '.join(['%s=%s' % (x, y) for x, y in ss.cookies.items()]).encode('utf8')
        if args.aria2c:
            if args.limit:
                cmd = 'aria2c -c -s10 -x10 ' \
                    '--max-download-limit %s ' \
                    '-o "%s.tmp" -d "%s" ' \
                    '--user-agent "%s" ' \
                    '--header "Cookie:%s" ' \
                    '--header "Referer:http://%s/" "%s"' \
                    % (args.limit, infos['name'], infos['dir_'],\
                        headers['User-Agent'], cookie, infos['apihost'], infos['dlink'])
            else:
                cmd = 'aria2c -c -s10 -x10 ' \
                    '-o "%s.tmp" -d "%s" --user-agent "%s" ' \
                    '--header "Cookie:%s" ' \
                    '--header "Referer:http://%s/" "%s"' \
                    % (infos['name'], infos['dir_'], headers['User-Agent'], \
                        cookie, infos['apihost'], infos['dlink'])
        else:
            if args.limit:
                cmd = 'wget -c --limit-rate %s ' \
                    '-O "%s.tmp" --user-agent "%s" ' \
                    '--header "Cookie:%s" ' \
                    '--header "Referer:http://%s/" "%s"' \
                    % (args.limit, infos['file'], headers['User-Agent'], \
                        cookie, infos['apihost'], infos['dlink'])
            else:
                cmd = 'wget -c -O "%s.tmp" --user-agent "%s" ' \
                    '--header "Cookie:%s" ' \
                    '--header "Referer:http://%s/" "%s"' \
                    % (infos['file'], headers['User-Agent'], \
                       cookie, infos['apihost'], infos['dlink'])

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

    def exists(self, filepath):
        pass

    def upload(self, path, dir_):
        pass

    def addtask(self):
        pass

    def do(self):
        self.get_infos()

def main(argv):
    if len(argv) <= 1:
        sys.exit()

    ######################################################
    # for argparse
    p = argparse.ArgumentParser(description='download from yunpan.360.com')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-a', '--aria2c', action='store_true', \
        help='download with aria2c')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    p.add_argument('-t', '--type_', action='store', \
        default=None, type=str, \
        help='要下载的文件的后缀，eg: -t mp3')
    p.add_argument('-l', '--limit', action='store', \
        default=None, type=str, help='下载速度限制，eg: -l 100k')
    global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    if xxx[0] == 'login' or xxx[0] == 'g':
        if len(xxx[1:]) < 1:
            username = raw_input(s % (1, 97, '  username: '))
            password = getpass(s % (1, 97, '  password: '))
        elif len(xxx[1:]) == 1:
            username = xxx[1]
            password = getpass(s % (1, 97, '  password: '))
        elif len(xxx[1:]) == 2:
            username = xxx[1]
            password = xxx[2]
        else:
            print s % (1, 91, '  login\n  login username\n  login username password')

        x = yunpan360()
        x.login(username, password)
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
        x = yunpan360()
        x.init()
        for url in urls:
            x.path = x.get_path(url)
            x.do()

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
