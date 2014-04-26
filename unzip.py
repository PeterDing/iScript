#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import sys
import zipfile

print "Processing File " + sys.argv[1]

file = ''
if len(sys.argv) == 3:
    file=zipfile.ZipFile(sys.argv[1],"r")
    file.setpassword(sys.argv[2])
else:
    file=zipfile.ZipFile(sys.argv[1],"r")

for name in file.namelist():
    try:
        utf8name=name.decode('gbk')
        pathname = os.path.dirname(utf8name)
    except:
        utf8name=name
        pathname = os.path.dirname(utf8name)

    print "Extracting " + utf8name
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
