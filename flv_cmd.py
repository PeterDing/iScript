#!/usr/bin/env python2
# vim: set fileencoding=utf8

import re
import requests
import os
import sys
import argparse
import random
from HTMLParser import HTMLParser
import urllib
import select

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template
parser = HTMLParser()

############################################################
# wget exit status
wget_es = {
    0: "No problems occurred.",
    2: "User interference.",
    1<<8: "Generic error code.",
    2<<8: "Parse error - for instance, \
        when parsing command-line optio.wgetrc or .netrc...",
    3<<8: "File I/O error.",
    4<<8: "Network failure.",
    5<<8: "SSL verification failure.",
    6<<8: "Username/password authentication failure.",
    7<<8: "Protocol errors.",
    8<<8: "Server issued an error response."
}
############################################################

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) " \
        "AppleWebKit/537.36 (KHTML, like Gecko) " \
        "Chrome/40.0.2214.91 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;" \
        "q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch",
    "Accept-Language": "en-US,en;q=0.8",
    "Referer": "http://flvgo.com/download"
}

ss = requests.session()
ss.headers.update(headers)

def download(info):
    if not os.path.exists(info['dir_']):
        os.mkdir(info['dir_'])

    #else:
        #if os.path.exists(info['filename']):
            #return 0

    num = random.randint(0, 7) % 8
    col = s % (2, num + 90, os.path.basename(info['filename']))
    print '\n  ++ 正在下载:', '#', \
        s % (1, 97, info['n']), '/', \
        s % (1, 97, info['amount']), \
        '#', col

    print info['durl']
    cmd = 'wget -c -nv --user-agent "%s" -O "%s" "%s"' \
        % (headers['User-Agent'], info['filename'], info['durl'])
    status = os.system(cmd)

    if status != 0:     # other http-errors, such as 302.
        wget_exit_status_info = wget_es[status]
        print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> \
              \x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
              % (status, wget_exit_status_info))
        print s % (1, 91, '  ===> '), cmd
        sys.exit(1)

def play(info):
    num = random.randint(0, 7) % 8
    col = s % (2, num + 90, os.path.basename(info['filename']))
    print '\n  ++ play:', '#', \
        s % (1, 97, info['n']), '/', \
        s % (1, 97, info['amount']), \
        '#', col

    cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
        '--http-header-fields "User-Agent:%s" ' \
        '"%s"' % (headers['User-Agent'], info['durl'])
        #'"%s"' % parser.unescape(info['durl'])

    os.system(cmd)
    timeout = 1
    ii, _, _ = select.select([sys.stdin], [], [], timeout)
    if ii:
        sys.exit(0)
    else:
        pass

def flvxz_parser(cn):
    blocks = cn.split('playerContainer')[1:]
    infos = {}
    title = re.search(r'class="name">(.+?)<', cn).group(1)
    infos['title'] = title
    infos['data'] = {}
    for bc in blocks:
        quality = re.search(r'视频格式：(\w+)', bc).group(1)
        size = sum([float(s) for s in re.findall(r'>([\d.]+) MB<', bc)])
        durls = re.findall(r'<td><a href="(.+?)">', bc)
        infos['data'][quality] = {
            'size': size,
            'durls': durls
        }
    return infos

def pickup(infos):
    print s % (1, 97, infos['title'])
    print s % (1, 97, '  ++ pick a quality:')
    sizes = [(infos['data'][q]['size'], q) for q in infos['data']]
    sizes.sort()
    sizes.reverse()
    for i in xrange(len(sizes)):
        print s % (1, 91, '  %s' % (i+1)), \
            str(sizes[i][0]) + 'MB\t', sizes[i][1]

    p = raw_input(s % (1, 92, '  Enter') + ' (1): ')
    if p == '':
        return sizes[0][1]
    if not p.isdigit():
        print s % (1, 91, '  !! enter error')
        sys.exit()
    p = int(p)
    if p <= len(infos['data']):
        print s % (2, 92, '  -- %s' % sizes[p-1][1])
        return sizes[p-1][1]
    else:
        print s % (1, 91, '  !! enter error')
        sys.exit()

def getext(durl):
    if durl.find('flv'):
        return '.flv'
    elif durl.find('mp4'):
        return '.mp4'
    elif durl.find('m3u8'):
        return '.m3u8'
    else:
        return '.flv'

def main(purl):
    apiurl = 'http://flvgo.com/download?url=%s' % urllib.quote(purl)
    ss.get('http://flvgo.com')
    cn = ss.get(apiurl).content
    infos = flvxz_parser(cn)
    title = infos['title']
    quality = pickup(infos)
    durls = infos['data'][quality]['durls']

    yes = True if len(durls) > 1 else False
    dir_ = os.path.join(os.getcwd(), infos['title']) if yes else os.getcwd()

    n = args.from_ - 1
    amount = len(durls)

    for i in xrange(n, amount):
        info = {
            'title': title,
            'filename': os.path.join(dir_, str(i+1) + getext(durls[i])),
            'durl': durls[i],
            'dir_': dir_,
            'amount': amount,
            'n': n
        }
        if args.play:
            play(info)
        else:
            download(info)
        n += 1

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='flvxz')
    p.add_argument('url', help='site url')
    p.add_argument('-p', '--play', action='store_true', \
                help='play with mpv')
    p.add_argument('-f', '--from_', action='store', \
        default=1, type=int, \
        help='从第几个开始下载，eg: -f 42')
    args = p.parse_args()
    main(args.url)
