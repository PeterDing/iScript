#!/usr/bin/env python2
# vim: set fileencoding=utf8

import os
import sys
import requests
import urlparse
import re
import argparse
import random
import select
import urllib2

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

headers = {
    "Accept":"text/html,application/xhtml+xml,application/xml; " \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding":"text/html",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2",
    "Content-Type":"application/x-www-form-urlencoded",
    "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 " \
        "(KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
}

ss = requests.session()
ss.headers.update(headers)

class nrop19(object):
    def __init__(self, url=None):
        self.url = url
        self.download = self.play if args.play else self.download

    def get_infos(self):
        r = ss.get(self.url)
        if r.ok:
            n1 = re.search(r'so.addVariable\(\'file\',\'(\d+)\'', r.content)
            n2 = re.search(r'so.addVariable\(\'seccode\',\'(.+?)\'', r.content)
            n3 = re.search(r'so.addVariable\(\'max_vid\',\'(\d+)\'', r.content)

            if n1 and n2 and n3:
                apiurl = 'http://%s/getfile.php' \
                    % urlparse.urlparse(self.url).hostname

                params = {
                    'VID': n1.group(1),
                    'mp4': '1',
                    'seccode': n2.group(1),
                    'max_vid': n3.group(1),
                }

                #tapiurl = apiurl + '?' + \
                    #'&'.join(['='.join(item) for item in params.items()])
                #print tapiurl

                r = requests.get(apiurl, params=params)
                if r.ok:
                    dlink = re.search(
                        r'file=(http.+?)&', r.content).group(1)
                    dlink = urllib2.unquote(dlink)
                    name = re.search(
                        r'viewkey=([\d\w]+)', self.url).group(1)
                    infos = {
                        'name': '%s.mp4' % name,
                        'file': os.path.join(os.getcwd(), '%s.mp4' % name),
                        'dir_': os.getcwd(),
                        'dlink': dlink,
                    }
                    if not args.get_url:
                        self.download(infos)
                    else:
                        print dlink
                else:
                    print s % (1, 91, '  Error at get(apiurl)')
            else:
                print s % (1, 91, '  You are blocked')

    def download(self, infos):
        num = random.randint(0, 7) % 7
        col = s % (2, num + 90, infos['file'])
        print '\n  ++ 正在下载: %s' % col

        cookies = '; '.join(
            ['%s=%s' % (i, ii) for i, ii in ss.cookies.items()])
        if args.aria2c:
            cmd = 'aria2c -c -x10 -s10 ' \
                '-o "%s.tmp" -d "%s" --header "User-Agent: %s" ' \
                '--header "Cookie: %s" "%s"' \
                % (infos['name'], infos['dir_'], \
                headers['User-Agent'], cookies, infos['dlink'])
        else:
            cmd = 'wget -c -O "%s.tmp" --header "User-Agent: %s" ' \
                '--header "Cookie: %s" "%s"' \
                % (infos['file'], headers['User-Agent'], cookies, infos['dlink'])

        status = os.system(cmd)
        if status != 0:     # other http-errors, such as 302.
            wget_exit_status_info = wget_es[status]
            print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> '\
                '\x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
                % (status, wget_exit_status_info))
            print s % (1, 91, '  ===> '), cmd
            sys.exit(1)
        else:
            os.rename('%s.tmp' % infos['file'], infos['file'])

    def play(self, infos):
        num = random.randint(0, 7) % 7
        col = s % (2, num + 90, infos['name'])
        print '\n  ++ play: %s' % col

        cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
            '--http-header-fields "user-agent:%s" "%s"' \
            % (headers['User-Agent'], infos['dlink'])

        os.system(cmd)
        timeout = 1
        ii, _, _ = select.select([sys.stdin], [], [], timeout)
        if ii:
            sys.exit(0)
        else:
            pass

    def do(self):
        self.get_infos()

def main(url):
    if args.proxy:
        ss.proxies = {
            'http': args.proxy,
            'https': args.proxy
        }
    x = nrop19(url)
    x.do()

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='download from 91porn.com')
    p.add_argument('url', help='url of 91porn.com')
    p.add_argument('-a', '--aria2c', action='store_true', \
                help='download with aria2c')
    p.add_argument('-p', '--play', action='store_true', \
                help='play with mpv')
    p.add_argument('-u', '--get_url', action='store_true', \
                help='print download_url without download')
    p.add_argument('--proxy', action='store', type=str, default=None, \
                help='print download_url without download')
    args = p.parse_args()
    main(args.url)
