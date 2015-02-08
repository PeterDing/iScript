#!/usr/bin/env python2
# vim: set fileencoding=utf8

import re
import base64
import requests
import os
import sys
import argparse
import random
import json
from HTMLParser import HTMLParser
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
    "Host": "www.flvxz.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) \
        AppleWebKit/537.36 (KHTML, like Gecko) \
        Chrome/40.0.2214.91 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "http://flvxz.com",
    "Connection": "keep-alive"
}

ss = requests.session()
ss.headers.update(headers)

api = 'https://www.flvxz.com/getFlv.php?url=%s'

def download(infos):
    if not os.path.exists(infos['dir_']):
        os.mkdir(infos['dir_'])

    #else:
        #if os.path.exists(infos['filename']):
            #return 0

    num = random.randint(0, 7) % 7
    col = s % (2, num + 90, os.path.basename(infos['filename']))
    print '\n  ++ 正在下载:', '#', \
        s % (1, 97, infos['n']), '/', \
        s % (1, 97, infos['amount']), \
        '#', col

    cmd = 'wget -c -nv --user-agent "%s" -O "%s" "%s"' \
        % (headers['User-Agent'], infos['filename'],
           parser.unescape(infos['durl']))
    status = os.system(cmd)

    if status != 0:     # other http-errors, such as 302.
        wget_exit_status_info = wget_es[status]
        print('\n\n ----###   \x1b[1;91mERROR\x1b[0m ==> \
              \x1b[1;91m%d (%s)\x1b[0m   ###--- \n\n' \
              % (status, wget_exit_status_info))
        print s % (1, 91, '  ===> '), cmd
        sys.exit(1)

def play(infos):
    num = random.randint(0, 7) % 7
    col = s % (2, num + 90, os.path.basename(infos['filename']))
    print '\n  ++ play:', '#', \
        s % (1, 97, infos['n']), '/', \
        s % (1, 97, infos['amount']), \
        '#', col

    cmd = 'mpv --really-quiet --cache 8140 --cache-default 8140 ' \
        '--http-header-fields "User-Agent:%s" ' \
        '"%s"' % (headers['User-Agent'], infos['durl'])
        #'"%s"' % parser.unescape(infos['durl'])

    os.system(cmd)
    timeout = 1
    ii, _, _ = select.select([sys.stdin], [], [], timeout)
    if ii:
        sys.exit(0)
    else:
        pass

def decrypt(encrypted_cn):
    c = encrypted_cn.split('}(')
    x = re.search(r'(\[.+\])\)\);', c[1]).group(1)
    y = re.search(r'(\[.+\])..\)\);if', c[2]).group(1)

    a, b = json.loads('[' + x + ']')
    for i in xrange(len(b)):
        b[i] = a[b[i]]
    t = ''.join(b[::-1])[8:-1]
    b = json.loads(t)

    a = json.loads(y)
    for i in xrange(len(b)):
        b[i] = a[b[i]]
    decrypted_cn = ''.join(b[::-1])

    return decrypted_cn

def flvxz_parser(cn):
    cn = decrypt(cn)
    qualities = re.findall(r'"quality">\[(.+?)\]<', cn)
    if not qualities: return {}

    j = {}
    chucks = re.split(r'"quality">\[.+?\]<', cn)[1:]

    for i in xrange(len(qualities)):
        parts = re.findall(r'data-clipboard-text="(.+?)"', chucks[i])
        t = re.findall(r'rel="noreferrer" href="(.+?)"', chucks[i])
        urls = [ii for ii in t if 'flvxz' not in ii]

        j[qualities[i]] = zip(parts, urls)

    return j

def pickup(j):
    print s % (1, 97, '  ++ pick a quality:')
    qualities = j.keys()
    qualities.sort()
    for i in xrange(len(qualities)):
        print s % (1, 91, '  %s' % (i+1)), qualities[i]

    p = raw_input(s % (1, 92, '  Enter: '))
    if p.isdigit():
        p = int(p)
        if p <= len(j):
            print s % (2, 92, '  -- %s' % qualities[p-1])
            return j[qualities[p-1]]
        else:
            print s % (1, 91, '  !! enter error')
            sys.exit()
    else:
        print s % (1, 91, '  !! enter error')
        sys.exit()

def main(url):
    encode_url = base64.urlsafe_b64encode(url.replace('://', ':##'))
    url = api % encode_url

    cn = ss.get(url).content
    j = flvxz_parser(cn)
    if j:
        j = pickup(j)
    else:
        print s % (1, 91, '  !! Can\'t get videos')
        sys.exit()

    title = re.search(r'media-heading">(.+?)</', cn)
    title = title.group(1) if title else ''
    yes = True if len(j) > 1 else False
    dir_ = os.path.join(os.getcwd(), title) if yes else os.getcwd()

    n = args.from_
    amount = len(j)
    j = j[args.from_ - 1:]
    for i in j:
        infos = {
            'filename': os.path.join(dir_, i[0]),
            'durl': i[1],
            'dir_': dir_,
            'amount': amount,
            'n': n
        }
        if args.play:
            play(infos)
        else:
            download(infos)
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
