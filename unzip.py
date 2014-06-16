#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import zipfile
import argparse

s = '\x1b[%d;%dm%s\x1b[0m'       # terminual color template

def unzip(path):

    file = zipfile.ZipFile(path,"r")
    if args.secret:
        file.setpassword(args.secret)

    for name in file.namelist():
        try:
            utf8name=name.decode('gbk')
            pathname = os.path.dirname(utf8name)
        except:
            utf8name=name
            pathname = os.path.dirname(utf8name)

        #print s % (1, 92, '  >> extracting:'), utf8name
        #pathname = os.path.dirname(utf8name)
        if not os.path.exists(pathname) and pathname != "":
            os.makedirs(pathname)
        data = file.read(name)
        if not os.path.exists(utf8name):
            try:
                fo = open(utf8name, "w")
                fo.write(data)
                fo.close
            except:
                pass
    file.close()

def main(argv):
    ######################################################
    # for argparse
    p = argparse.ArgumentParser(description='解决unzip乱码')
    p.add_argument('xxx', type=str, nargs='*', \
        help='命令对象.')
    p.add_argument('-s', '--secret', action='store', \
        default=None, help='密码')
    global args
    args = p.parse_args(argv[1:])
    xxx = args.xxx

    for path in xxx:
        if path.endswith('.zip'):
            if os.path.exists(path):
                print s % (1, 97, '  ++ unzip:'), path
                unzip(path)
            else:
                print s % (1, 91, '  !! file doesn\'t exist.'), path
        else:
            print s % (1, 91, '  !! file isn\'t a zip file.'), path

if __name__ == '__main__':
    argv = sys.argv
    main(argv)
