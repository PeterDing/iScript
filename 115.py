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
import sha
import select

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

# file extensions
mediatype = [
    ".wma", ".wav", ".mp3", ".aac", ".ra", ".ram", ".mp2", ".ogg", ".aif",
    ".mpega", ".amr", ".mid", ".midi", ".m4a", ".m4v", ".wmv", ".rmvb",
    ".mpeg4", ".mpeg2", ".flv", ".avi", ".3gp", ".mpga", ".qt", ".rm",
    ".wmz", ".wmd", ".wvx", ".wmx", ".wm", ".swf", ".mpg", ".mp4", ".mkv",
    ".mpeg", ".mov", ".mdf", ".iso", ".asf"
]

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template

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
    def __init__(self):
        self.download = self.play if args.play else self.download

    def init(self):
        if os.path.exists(cookie_file):
            try:
                t = json.loads(open(cookie_file).read())
                ss.cookies.update(t.get('cookies', t))
                if not self.check_login():
                    print s % (1, 91, '  !! cookie is invalid, please login\n')
                    sys.exit(1)
                self.check_vip()
            except:
                g = open(cookie_file, 'w')
                g.close()
                print s % (1, 97, '  please login')
                sys.exit(1)
        else:
            print s % (1, 91, '  !! cookie_file is missing, please login')
            sys.exit(1)

    def check_vip(self):
        url = 'http://vip.115.com/?ac=mycouponcount'
        r = ss.get(url).content

        if '"vip":0' in r:
            self.is_vip = False
        else:
            self.is_vip = True

    def check_login(self):
        #print s % (1, 97, '\n  -- check_login')
        url = 'http://msg.115.com/?ac=unread'
        j = ss.get(url)
        if '"code"' not in j.text:
            #print s % (1, 92, '  -- check_login success\n')
            self.save_cookies()
            return True
        else:
            print s % (1, 91, '  -- check_login fail\n')
            return False

    def login(self, account, password):
        print s % (1, 97, '\n  -- login')

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
        theaders["Referer"] = "http://passport.115.com\
            /static/reg_login_130418/bridge.html?ajax_cb_key=bridge_%s" \
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

    def save_cookies(self):
        with open(cookie_file, 'w') as g:
            c = {'cookies': ss.cookies.get_dict()}
            g.write(json.dumps(c, indent=4, sort_keys=True))

    def get_dlink(self, pc):
        params = {
            "pickcode": pc.encode('utf8'),
            "_": int(time.time()*1000),
        }
        url = 'http://web.api.115.com/files/download'
        r = ss.get(url, params=params)
        j = r.json()
        dlink = j['file_url'].encode('utf8')
        return dlink

    def _get_play_purl(self, pickcode):
        url = 'http://115.com/api/video/m3u8/%s.m3u8' % pickcode
        r = ss.get(url)
        c = r.content.strip()

        if c:
            purl = c.split()[-1]
            if 'http' not in purl:
                return None
            else:
                return purl
        else:
            return None

    def get_infos(self, cid):
        params = {
            "cid": cid,
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
        j = ss.get(url, params=params).json()

        dir_loop1 = [{'dir': j['path'][-1]['name'], 'cid': j['cid']}]
        dir_loop2 = []
        #base_dir = os.getcwd()
        while dir_loop1:
            for d in dir_loop1:
                params['cid'] = d['cid']
                j = ss.get(url, params=params).json()
                if j['errNo'] == 0 and j['data']:
                    if args.type_:
                        j['data'] = [
                            x for x in j['data'] \
                            if x.get('ns') \
                                or x['ico'].lower() == unicode(args.type_.lower())
                        ]

                    for i in j['data']:
                        if i.get('ns'):
                            item = {
                                'dir': os.path.join(d['dir'], i['ns']),
                                'cid': i['cid']
                            }
                            dir_loop2.append(item)

                    if args.play:
                        j['data'] = [
                            i for i in j['data'] \
                            if i.get('sha') \
                                and os.path.splitext(i['n'])[-1].lower() \
                                in mediatype
                        ]

                    total_file = len([i for i in j['data'] if not i.get('ns')])
                    if args.from_ - 1:
                        j['data'] = j['data'][args.from_-1:] if args.from_ \
                                                                else j['data']
                    nn = args.from_
                    for i in j['data']:
                        if not i.get('ns'):
                            t = i['n']
                            t =  os.path.join(d['dir'], t).encode('utf8')
                            t =  os.path.join(os.getcwd(), t)
                            infos = {
                                'file': t,
                                'dir_': os.path.split(t)[0],
                                'dlink': self.get_dlink(i['pc']),
                                'name': i['n'].encode('utf8'),
                                #'purl': self._get_play_purl(
                                #   i['pc'].encode('utf8')) \
                                #       if args.play and self.is_vip else None,
                                'purl': self._get_play_purl(
                                    i['pc'].encode('utf8')) \
                                        if args.play else None,
                                'nn': nn,
                                'total_file': total_file
                            }
                            nn += 1
                            self.download(infos)
                else:
                    print s % (1, 91, '  error: get_infos')
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

        num = random.randint(0, 7) % 8
        col = s % (2, num + 90, infos['file'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] \
            if infos.get('total_file') else 1
        print '\n  ++ 正在下载: #', \
            s % (1, 97, infos['nn']), \
            '/', s % (1, 97, infos['total_file']), \
            '#', col

        if args.aria2c:
            # 115 普通用户只能有4下载通道。
            quiet = ' --quiet=true' if args.quiet else ''
            taria2c = ' -x %s -s %s' % (args.aria2c, args.aria2c)
            tlimit = ' --max-download-limit %s' \
                % args.limit if args.limit else ''
            cmd = 'aria2c -c%s%s%s ' \
                '-m 0 ' \
                '-o "%s.tmp" -d "%s" ' \
                '--user-agent "%s" ' \
                '--header "Referer:http://m.115.com/" "%s"' \
                % (quiet, taria2c, tlimit, infos['name'], infos['dir_'],\
                    headers['User-Agent'], infos['dlink'])
        else:
            tlimit = ' --limit-rate %s' % args.limit if args.limit else ''
            cmd = 'wget -c%s ' \
                '-O "%s.tmp" --user-agent "%s" ' \
                '--header "Referer:http://m.115.com/" "%s"' \
                % (tlimit, infos['file'], headers['User-Agent'],
                   infos['dlink'])

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
        num = random.randint(0, 7) % 8
        col = s % (2, num + 90, infos['name'])
        infos['nn'] = infos['nn'] if infos.get('nn') else 1
        infos['total_file'] = infos['total_file'] \
            if infos.get('total_file') else 1
        print '\n  ++ play: #', \
            s % (1, 97, infos['nn']), '/', \
            s % (1, 97, infos['total_file']), \
            '#', col

        if not infos['purl']:
            print s % (1, 91, '  |-- m3u8 is not ready, using dlink')
            infos['purl'] = infos['dlink']

        cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
            '--http-header-fields "user-agent:%s" '\
            '--http-header-fields "Referer:http://m.115.com" "%s"' \
            % (headers['User-Agent'], infos['purl'])

        status = os.system(cmd)
        timeout = 1
        ii, _, _ = select.select([sys.stdin], [], [], timeout)
        if ii:
            sys.exit(0)
        else:
            pass

    # TODO
    def exists(self, filepath):
        pass

    # TODO
    def upload(self, path, dir_):
        pass

    def addtask(self, u):
        # get uid
        url = 'http://my.115.com/?ct=ajax&ac=get_user_aq'
        r = ss.get(url)
        j = r.json()
        uid = j['data']['uid']

        # get sign, time
        url = 'http://115.com/?ct=offline&ac=space'
        r = ss.get(url)
        j = r.json()
        sign = j['sign']
        tm = j['time']

        # now, add task
        data = {
            'url': urllib.quote_plus(u),
            'uid': uid,
            'sign': sign,
            'time': str(tm)
        }
        url = 'http://115.com/lixian/?ct=lixian&ac=add_task_url'
        r = ss.post(url, data=data)
        if not r.ok:
            print s % (1, 91, '  !! Error at addtask')
            print r.content
            sys.exit(1)

        j = r.json()
        if j['info_hash']:
            print s % (1, 92, '  ++ add task success.')
        else:
            print s % (2, 91, '  !! Error: %s' % j['error_msg'])
            sys.exit()

        data = {
            'page': 1,
            'uid': uid,
            'sign': sign,
            'time': str(tm)
        }
        url = 'http://115.com/lixian/?ct=lixian&ac=task_lists'
        r = ss.post(url, data=data)
        j = r.json()
        percentDone = j['tasks'][0]['percentDone']
        print s % (1, 97, '  ++ %s' % j['tasks'][0]['name'])
        print s % (1, 92, '  %s%s Done' % (percentDone, '%'))

    def do(self, pc):
        dlink = self.get_dlink(pc)
        name = re.search(r'/([^/]+?)\?', dlink).group(1)
        name = urllib.unquote_plus(name)
        t = os.path.join(os.getcwd(), name)
        infos = {
            'file': t,
            'dir_': os.path.split(t)[0],
            'dlink': dlink,
            #'purl': self._get_play_purl(pc) \
            #   if args.play and self.is_vip else None,
            'purl': self._get_play_purl(pc) if args.play else None,
            'name': name,
            'nn': 1,
            'total_file': 1
        }
        self.download(infos)

def main(argv):
    if len(argv) <= 1:
        sys.exit()

    ######################################################
    # for argparse
    p = argparse.ArgumentParser(
        description='download from 115.com reversely')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-a', '--aria2c', action='store', default=None, \
        type=int, help='aria2c分段下载数量')
    p.add_argument('-p', '--play', action='store_true', \
        help='play with mpv')
    p.add_argument('-q', '--quiet', action='store_true', \
                   help='quiet for download and play')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    p.add_argument('-t', '--type_', action='store', \
        default=None, type=str, \
        help='要下载的文件的后缀，eg: -t mp3')
    p.add_argument('-l', '--limit', action='store', \
        default=None, type=str, help='下载速度限制，eg: -l 100k')
    p.add_argument('-d', '--addtask', action='store_true', \
        help='加离线下载任务')
    global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    if xxx[0] == 'login' or xxx[0] == 'g':
        if len(xxx[1:]) < 1:
            account = raw_input(s % (1, 97, ' account: '))
            password = getpass(s % (1, 97, 'password: '))
        elif len(xxx[1:]) == 1:
            account = xxx[1]
            password = getpass(s % (1, 97, '  password: '))
        elif len(xxx[1:]) == 2:
            account = xxx[1]
            password = xxx[2]
        else:
            print s % (1, 91, '  login\n  login account\n  \
                                 login account password')

        x = pan115()
        x.login(account, password)
        is_signin = x.check_login()
        if is_signin:
            print s % (1, 92, '  ++ login succeeds.')
        else:
            print s % (1, 91, '  login failes')

    elif xxx[0] == 'signout':
        g = open(cookie_file, 'w')
        g.close()

    else:
        x = pan115()
        x.init()
        for url in xxx:
            if 'pickcode' in url:
                pc = re.search(r'pickcode=([\d\w]+)', url)
                if pc:
                    pc = pc.group(1)
                    x.do(pc)
                else:
                    print s % (1, 91, '  can\'t find pickcode.')
            elif 'cid=' in url:
                cid = re.search(r'cid=(\d+)', url)
                cid = cid.group(1) if cid else '0'
                x.get_infos(cid)
            elif args.addtask:
                x.addtask(url)
            else:
                print s % (2, 91, '  请正确输入自己的115地址。')

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
