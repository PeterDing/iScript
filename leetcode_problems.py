#!/usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import re
import os
import argparse
import requests
from lxml import html as lxml_html

try:
    import html
except ImportError:
    import HTMLParser
    html = HTMLParser.HTMLParser()

try:
    import cPickle as pk
except ImportError:
    import pickle as pk

class LeetcodeProblems(object):
    def get_problems_info(self):
        leetcode_url = 'https://leetcode.com/problemset/algorithms'
        res = requests.get(leetcode_url)
        if not res.ok:
            print('request error')
            sys.exit()
        cm = res.text
        cmt = cm.split('tbody>')[-2]
        indexs = re.findall(r'<td>(\d+)</td>', cmt)
        problem_urls = ['https://leetcode.com' + url \
                        for url in re.findall(
                            r'<a href="(/problems/.+?)"', cmt)]
        levels = re.findall(r"<td value='\d*'>(.+?)</td>", cmt)
        tinfos = zip(indexs, levels, problem_urls)
        assert (len(indexs) == len(problem_urls) == len(levels))
        infos = []
        for info in tinfos:
            res = requests.get(info[-1])
            if not res.ok:
                print('request error')
                sys.exit()
            tree = lxml_html.fromstring(res.text)
            title = tree.xpath('//meta[@property="og:title"]/@content')[0]
            description = tree.xpath('//meta[@property="description"]/@content')
            if not description:
                description = tree.xpath('//meta[@property="og:description"]/@content')[0]
            else:
                description = description[0]
            description = html.unescape(description.strip())
            tags = tree.xpath('//div[@id="tags"]/following::a[@class="btn btn-xs btn-primary"]/text()')
            infos.append(
                {
                    'title': title,
                    'level': info[1],
                    'index': int(info[0]),
                    'description': description,
                    'tags': tags
                }
            )

        with open('leecode_problems.pk', 'wb') as g:
            pk.dump(infos, g)
        return infos

    def to_text(self, pm_infos):
        if self.args.index:
            key = 'index'
        elif self.args.title:
            key = 'title'
        elif self.args.tag:
            key = 'tags'
        elif self.args.level:
            key = 'level'
        else:
            key = 'index'

        infos = sorted(pm_infos, key=lambda i: i[key])

        text_template = '## {index} - {title}\n' \
            '~{level}~  {tags}\n' \
            '{description}\n' + '\n' * self.args.line
        text = ''
        for info in infos:
            if self.args.rm_blank:
                info['description'] = re.sub(r'[\n\r]+', r'\n', info['description'])
            text += text_template.format(**info)

        with open('leecode problems.txt', 'w') as g:
            g.write(text)

    def run(self):
        if os.path.exists('leecode_problems.pk') and not self.args.redownload:
            with open('leecode_problems.pk', 'rb') as f:
                pm_infos = pk.load(f)
        else:
            pm_infos = self.get_problems_info()

        print('find %s problems.' % len(pm_infos))
        self.to_text(pm_infos)

def handle_args(argv):
    p = argparse.ArgumentParser(description='extract all leecode problems to location')
    p.add_argument('--index', action='store_true', help='sort by index')
    p.add_argument('--level', action='store_true', help='sort by level')
    p.add_argument('--tag', action='store_true', help='sort by tag')
    p.add_argument('--title', action='store_true', help='sort by title')
    p.add_argument('--rm_blank', action='store_true', help='remove blank')
    p.add_argument('--line', action='store', type=int, default=10, help='blank of two problems')
    p.add_argument('-r', '--redownload', action='store_true', help='redownload data')
    args = p.parse_args(argv[1:])
    return args

def main(argv):
    args = handle_args(argv)
    x = LeetcodeProblems()
    x.args = args
    x.run()

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
