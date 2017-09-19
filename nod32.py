#!/usr/bin/env python3
# encoding: utf-8
# author: Vincent
# refer: https://github.com/vc5
import requests,re
from bs4 import BeautifulSoup

url = "http://nod32jihuoma.com/"

headers = {
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.91 Safari/537.36",
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'dnt': "1",
    'referer': "https://www.google.com/",
    'accept-encoding': "gzip, deflate",
    'accept-language': "zh-CN,zh;q=0.8",
    'cache-control': "no-cache"
    }

response = requests.request("GET", url, headers=headers)

soup = BeautifulSoup(response.content,'lxml')
url1 = soup.select('#zq_ser > div.col-left.box-base > div.box1  a')[0]['href']
response = requests.request("GET",url1,headers=headers)
soup = BeautifulSoup(response.content,'lxml')
pp = soup.select('#Artcontent p')
pp = pp[1:-1]
def esetconvert(id,passwd):
    url = "https://my.eset.com/Convert"
    payload = {'EmailConfirmation':'false','Password':passwd,'UserName':id}
    r= requests.post(url,headers=headers,data=payload)
    soup =BeautifulSoup(r.content,'lxml')
    LicenseKey = soup.select('#body_lblLicenseKey')[0].text
    return LicenseKey
pat_id=re.compile('TRIAL-\d{10}')
pat_pass=re.compile('[a-z0-9]{10}')
for p in pp:
    id=re.findall(pat_id,p.text)[0]
    passwd = re.findall(pat_pass, p.text)[-1]
    print(esetconvert(id,passwd))

