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
import sha
import select


account  = ''
password = ''   # 注意password不能超过48位


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

cookie_file = os.path.join(os.path.expanduser('~'), '.115.cookies')

headers = {
    "Accept":"Accept: application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    "Referer":"http://m.115.com/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

class pan115(object):
    def __init__(self, cid='0'):
        self.cid = cid
        self.download = self.play if args.play else self.download

    def init(self):
        if os.path.exists(cookie_file):
            t = json.loads(open(cookie_file).read())
            ss.cookies.update(t)
            if not self.check_login():
                self.login()
                if self.check_login():
                    print s % (92, '  -- login success\n')
                else:
                    print s % (91, '  !! login fail, maybe username or password is wrong.\n')
                    print s % (91, '  !! maybe this app is down.')
                    sys.exit(1)
        else:
            self.login()
            if self.check_login():
                print s % (92, '  -- login success\n')
            else:
                print s % (91, '  !! login fail, maybe username or password is wrong.\n')
                print s % (91, '  !! maybe this app is down.')
                sys.exit(1)

    def check_login(self):
        print s % (97, '\n  -- check_login')
        url = 'http://msg.115.com/?ac=unread'
        j = ss.get(url)
        if '"code"' not in j.text:
            print s % (92, '  -- check_login success\n')
            self.save_cookies()
            return True
        else:
            print s % (91, '  -- check_login fail\n')
            return False

    def login(self):
        print s % (97, '\n  -- login')

        def get_ssopw(ssoext):
            p = sha.new(password).hexdigest()
            a = sha.new(account).hexdigest()
            t = sha.new(p + a).hexdigest()
            ssopw = sha.new(t + ssoext.upper()).hexdigest()
            return ssopw

        ssoext = str(int(time.time()*1000))
        ssopw = get_ssopw(ssoext)

        quote = urllib.quote
        data = quote("login[ssoent]")+"=B1&" + \
            quote("login[version]")+"=2.0&" + \
            quote("login[ssoext]")+"=%s&" % ssoext + \
            quote("login[ssoln]")+"=%s&" % quote(account) + \
            quote("login[ssopw]")+"=%s&" % ssopw + \
            quote("login[ssovcode]")+"=%s&" % ssoext + \
            quote("login[safe]")+"=1&" + \
            quote("login[time]")+"=1&" + \
            quote("login[safe_login]")+"=1&" + \
            "goto=http://m.115.com/?ac=home"

        theaders = headers
        theaders["Referer"] = "http://passport.115.com/static/reg_login_130418/bridge.html?ajax_cb_key=bridge_%s" \
        % int(time.time()*1000)

        # Post!
        # XXX : do not handle errors
        params = {
            'ct': 'login',
            'ac': 'ajax',
            'is_ssl': 1
        }
        url = 'http://passport.115.com'
        ss.post(url, params=params, data=data, headers=theaders)
        self.save_cookies()
        sys.exit()

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            g.write(json.dumps(ss.cookies.get_dict(), indent=4, \
                sort_keys=True))

    def get_dlink(self, pc):
        params = {
            "ct": "app",
            "ac": "get",
            "pick_code": pc.encode('utf8')
        }
        url = 'http://115.com'
        r = ss.get(url, params=params)
        j = r.json()
        dlink = j['data']['url'].encode('utf8')
        return dlink

    def get_infos(self):
        params = {
            "cid": self.cid,
            "offset": 0,
            "type": "",
            "limit": 10000,
            "format": "json",
            "aid": 1,
            "o": "file_name",
            "asc": 0,
            "show_dir": 1
        }

        url = 'http://web.api.115.com/files'
        j = json.loads(ss.get(url, params=params).content[3:])

        dir_loop1 = [{'dir': j['path'][-1]['name'], 'cid': j['cid']}]
        dir_loop2 = []
        #base_dir = os.getcwd()
        while dir_loop1:
            for d in dir_loop1:
                params['cid'] = d['cid']
                j = json.loads(ss.get(url, params=params).content[3:])
                if j['errNo'] == 0 and j['data']:
                    if args.type_:
                        j['data'] = [x for x in j['data'] if x.get('ns') \
                            or x['ico'].lower() == unicode(args.type_.lower())]
                    total_file = len([i for i in j['data'] if not i.get('ns')])
                    if args.from_ - 1:
                        j['data'] = j['data'][args.from_-1:] if args.from_ else j['data']
                    nn = args.from_
                    for i in j['data']:
                        if i.get('ns'):
                            item = {
                                'dir': os.path.join(d['dir'], i['ns']),
                                'cid': i['cid']
                            }
                            dir_loop2.append(item)
                        else:
                            t = i['n']
                            t =  os.path.join(d['dir'], t).encode('utf8')
                            t =  os.path.join(os.getcwd(), t)
                            infos = {
                                'file': t,
                                'dir_': os.path.split(t)[0],
                                'dlink': self.get_dlink(i['pc']),
                                'name': i['n'].encode('utf8'),
                                'nn': nn,
                                'total_file': total_file
                            }
                            nn += 1
                            self.download(infos)
                else:
                    print s % (91, '  error: get_infos')
                    sys.exit(0)
            dir_loop1 = dir_loop2
            dir_loop2 = []


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
            # 115 普通用户只能有4下载通道。
            if args.limit:
                cmd = 'aria2c -c -x4 -s4 ' \
                    '--max-download-limit %s ' \
                    '-o "%s.tmp" -d "%s" ' \
                    '--user-agent "%s" ' \
                    '--header "Referer:http://m.115.com/" "%s"' \
                    % (args.limit, infos['name'], infos['dir_'],\
                        headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'aria2c -c -x4 -s4 ' \
                    '-o "%s.tmp" -d "%s" --user-agent "%s" ' \
                    '--header "Referer:http://m.115.com/" "%s"' \
                    % (infos['name'], infos['dir_'], headers['User-Agent'], \
                        infos['dlink'])
        else:
            if args.limit:
                cmd = 'wget -c --limit-rate %s ' \
                    '-O "%s.tmp" --user-agent "%s" ' \
                    '--header "Referer:http://m.115.com/" "%s"' \
                    % (args.limit, infos['file'], headers['User-Agent'], infos['dlink'])
            else:
                cmd = 'wget -c -O "%s.tmp" --user-agent "%s" ' \
                    '--header "Referer:http://m.115.com/" "%s"' \
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
        print '\n  ++ play: #', s % (97, infos['nn']), '/', s % (97, infos['total_file']), '#', col

        if os.path.splitext(infos['file'])[-1].lower() == '.wmv':
            cmd = 'mplayer -really-quiet -cache 8140 ' \
                '-http-header-fields "user-agent:%s" ' \
                '-http-header-fields "Referer:http://m.115.com/" "%s"' \
                % (headers['User-Agent'], infos['dlink'])
        else:
            cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
                '--http-header-fields "user-agent:%s" '\
                '--http-header-fields "Referer:http://m.115.com" "%s"' \
                % (headers['User-Agent'], infos['dlink'])

        status = os.system(cmd)
        timeout = 1
        ii, _, _ = select.select([sys.stdin], [], [], timeout)
        if ii:
            sys.exit(0)
        else:
            pass

    def exists(self, filepath):
        pass

    def upload(self, path, dir_):
        pass

    def do(self):
        self.get_infos()

    def do2(self, pc):
        dlink = self.get_dlink(pc)
        name = re.search(r'file=(.+?)(&|$)', dlink).group(1)
        name = urllib.unquote_plus(name)
        t = os.path.join(os.getcwd(), name)
        infos = {
            'file': t,
            'dir_': os.path.split(t)[0],
            'dlink': dlink,
            'name': name,
            'nn': 1,
            'total_file': 1
        }
        self.download(infos)

def main(url):
    if 'pickcode' in url:
        pc = re.search(r'pickcode=([\d\w]+)', url)
        if pc:
            pc = pc.group(1)
            x = pan115()
            x.init()
            x.do2(pc)
        else:
            print s % (91, '  can\'t find pickcode.')
    elif 'cid' in url:
        cid = re.search(r'cid=(\d+)', url)
        cid = cid.group(1) if cid else '0'
        x = pan115(cid)
        x.init()
        x.do()
    else:
        print s % (91, '  请正确输入自己的115地址。')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='download from 115.com reversely')
    p.add_argument('url', help='自己115文件夹url')
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
    args = p.parse_args()
    main(args.url)
