#!/usr/bin/env python2
# vim: set fileencoding=utf8

import sys
import urllib
import re
import argparse

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template

opener = urllib.urlopen

class ed2k_search(object):
    def __init__(self, keyword=''):
        self.url = "http://donkey4u.com/search/%s?page=%s&mode=list" \
            % (keyword, '%s')
        print ''

    def get_infos(self, url):
        r = opener(url)
        assert r
        self.html = r.read()
        html = re.search(r'<table class=\'search_table\'>.+?</table>',
                         self.html, re.DOTALL).group()

        sizes = re.findall(r'<td width=\'70\' align=\'right\'>(.+)', html)
        seeds = re.findall(r'<td width=\'100\' align=\'right\'>(.+)', html)
        links = re.findall(r'ed2k://.+?/', html)

        infos = zip(sizes, seeds, links)

        if infos:
            self.display(infos)
        else:
            print s % (1, 91, '  !! You are not Lucky, geting nothing.')
            sys.exit(1)

    def display(self, infos):
        template = '  size: ' + s % (1, 97, '%s') \
            + '  seed: ' + s % (1, 91, '%s') \
            + '\n  ----------------------------' \
            + '\n  ' + s % (2, 92, '%s') \
            + '\n  ----------------------------\n'

        for i in infos:
            t = template % i
            print t

    def do(self):
        page = 1
        while True:
            url = self.url % page
            self.get_infos(url)
            nx = raw_input(s % (1, 93, '  next page?') + ' (N/y): ')
            if nx in ('Y', 'y'):
                page += 1
                print ''
            else:
                sys.exit(1)


def main(xxx):
    keyword = ' '.join(xxx)
    x = ed2k_search(keyword)
    x.do()

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='searching ed2k at donkey4u.com')
    p.add_argument('xxx', type=str, nargs='*', help='keyword')
    args = p.parse_args()
    main(args.xxx)
