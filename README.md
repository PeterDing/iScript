## iScript

包含项目:

> *[L]* *[W]* *[LW]* 分别表示，在linux, windows, linux和windows 下通过测试。

- *[L]* xiami.py - 下载或播放高品质虾米音乐(xiami.com)

- *[L]* pan.baidu.com.py - 百度网盘的下载和播放

- *[L]* 115.py - 115网盘的下载和播放

- *[L]* yunpan.360.cn.py - 360网盘的下载

- *[L]* music.baidu.com.py - 下载或播放高品质百度音乐(music.baidu.com)

- *[L]* music.163.com.py - 下载或播放高品质网易音乐(music.163.com)

- *[L]* tumblr.py - 下载某个tumblr.com的所有图片

- *[L]* unzip.py - 解决linux下unzip乱码的问题

- *[L]* torrent2magnet.py - 种子转磁力

- *[L]* 91porn.py - 下载或播放91porn

- *[L]* ThunderLixianExporter.user.js - A fork of https://github.com/binux/ThunderLixianExporter - 增加了mpv和mplayer的导出。

- 待续

---

---

### xiami.py - 下载或播放高品质虾米音乐(xiami.com)

1. 依赖

        python2-requests (https://github.com/kennethreitz/requests)

        python2-mutagen (https://code.google.com/p/mutagen/)

        mpv (http://mpv.io)

2. 使用说明

    在源码中填入email和password后，可以将播放记录提交到虾米。

    !!! vip账户支持高品质音乐的下载和播放。

    默认执行下载，如要播放，加参数-p。

    下载的MP3默认添加id3 tags，保存在当前目录下。

    日志保存在 ~/.Xiami.log, cookies保存在 ~/.Xiami.cookies。
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

3. 用法

    \# xm 是xiami.py的马甲 (alias xm='python2 /path/to/xiami.py')

        # 下载专辑
        xm http://www.xiami.com/album/168709?spm=a1z1s.6928801.1561534521.114.ShN6mD

        # 下载单曲
        xm http://www.xiami.com/song/2082998?spm=a1z1s.6659513.0.0.DT2j7T

        # 下载精选集
        xm http://www.xiami.com/song/showcollect/id/30374035?spm=a1z1s.3061701.6856305.16.fvh75t

        # 下载该艺术家所有专辑或 Top 20 歌曲
        xm http://www.xiami.com/artist/23460?spm=a1z1s.6928801.1561534521.115.ShW08b

        # 下载用户的收藏
        xm http://www.xiami.com/u/141825?spm=a1z1s.3521917.0.0.zI0APP


    播放:

        # url 是上面的
        xm -p url

4. 参考:

> http://kanoha.org/2011/08/30/xiami-absolute-address/

> http://www.blackglory.me/xiami-vip-audition-with-no-quality-difference-between-downloading/

> https://gist.github.com/lepture/1014329

---

### pan.baidu.com.py - 百度网盘的下载和播放

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)

        mpv (http://mpv.io)

        mplayer # 我的linux上mpv播放wmv出错，换用mplayer

2. 使用说明

    在源码中填入百度账户username和password后，可以递归下载自己的网盘文件。

    分享的网盘连接中只支持单个文件的下载。

    下载工具默认为wget, 可用参数-a选用aria2

    对所有文件，默认执行下载，如要播放媒体文件，加参数-p。

    下载的文件，保存在当前目录下。

    cookies保存在 ~/.bp.cookies
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。
    
    参数:

        -a, --aria2c                   download with aria2c
        -p, --play                     play with mpv
        -s SECRET, --secret SECRET     提取密码
        -f number, --from_ number      从第几个开始下载，eg: -f 42
        -t ext, --type_ ext            要下载的文件的后缀，eg: -t mp3
        -l amount, --limit amount      下载速度限制，eg: -l 100k

3. 用法

    \# bp 是pan.baidu.com.py的马甲 (alias bp='python2 /path/to/pan.badiu.com.py')

        # 下载自己网盘中的*单个文件*
        bp http://pan.baidu.com/disk/home#dir/path=/path/to/filename
        bp http://pan.baidu.com/disk/home#dir/path%3D%2Fpath%2Fto%2Ffilename
        # or
        bp path=/path/to/filename
        bp path%3D%2Fpath%2Fto%2Ffilename

        # 递归下载自己网盘中的*文件夹*
        bp http://pan.baidu.com/disk/home#dir/path=/path/to/directory
        bp http://pan.baidu.com/disk/home#dir/path%3D%2Fpath%2Fto%2Fdirectory
        # or
        bp path=/path/to/directory
        bp path%3D%2Fpath%2Fto%2Fdirectory

        # 下载别人分享的*单个文件*
        bp http://pan.baidu.com/s/1o64pFnW
        bp http://pan.baidu.com/share/link?shareid=1622654699&uk=1026372002&fid=2112674284

        # 下载别人加密分享的*单个文件*，密码参数-s
        bp -s vuej http://pan.baidu.com/s/1i3FVlw5

        # 下载用aria2, url 是上面的
        bp -a url
        bp -a -s [secret] url

    播放

        # url 是上面的
        bp -p url
        bp -s [secret] -p url

4. 参考:

> https://gist.github.com/HououinRedflag/6191023

> https://github.com/banbanchs/pan-baidu-download/blob/master/bddown_core.py

---

### 115.py - 115网盘的下载和播放

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)

        mpv (http://mpv.io)

        mplayer # 我的linux上mpv播放wmv出错，换用mplayer

2. 使用说明

    !!! 脚本是用于下载自己的115网盘文件，不支持他人分享文件。
    
    !!! 非vip用户下载只能有4个通道，理论上，用aria2的下载速度最大为 4*300kb/s。

    在源码中填入115账户account和password后，可以*递归下载*自己的网盘文件。

    下载工具默认为wget, 可用参数-a选用aria2。

    对所有文件，默认执行下载(用wget)，如要播放媒体文件，加参数-p。

    下载的文件，保存在当前目录下。

    cookies保存在 ~/.115.cookies
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。
    
    参数:

        -a, --aria2c                   download with aria2c
        -p, --play                     play with mpv
        -f number, --from_ number      从第几个开始下载，eg: -f 42
        -t ext, --type_ ext            要下载的文件的后缀，eg: -t mp3
        -l amount, --limit amount      下载速度限制，eg: -l 100k

3. 用法

    \# pan115 是115.py的马甲 (alias pan115='python2 /path/to/pan.badiu.com.py')

        # 递归下载自己网盘中的*文件夹*
        pan115 http://115.com/?cid=xxxxxxxxxxxx&offset=0&mode=wangpan

        # 下载自己网盘中的*单个文件* -- 只能是115上可单独打开的文件，如pdf，视频
        pan115 http://wenku.115.com/preview/?pickcode=xxxxxxxxxxxx

        # 下载用aria2, url 是上面的
        pan115 -a url

    播放

        # url 是上面的
        pan115 -p url

4. 参考:

> http://passport.115.com/static/wap/js/common.js?v=1.6.39

---

### yunpan.360.cn.py - 360网盘的下载

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)


2. 使用说明

    在源码中填入yunpan.360.com账户username和password后，可以递归下载自己的网盘文件。
    
    !!!!!!  万恶的360不支持断点续传   !!!!!!
    
    由于上面的原因，不能播放媒体文件。

    只支持自己的\*文件夹\*的递归下载。

    下载工具默认为wget, 可用参数-a选用aria2

    下载的文件，保存在当前目录下。

    cookies保存在 ~/.360.cookies
    
    参数:

        -a, --aria2c                   download with aria2c
        -f number, --from_ number      从第几个开始下载，eg: -f 42
        -t ext, --type_ ext            要下载的文件的后缀，eg: -t mp3
        -l amount, --limit amount      下载速度限制，eg: -l 100k

3. 用法

    \# yp 是yunpan.360.cn.py的马甲 (alias yp='python2 /path/to/yunpan.360.cn.py')

        # 递归下载自己网盘中的*文件夹*
        yp http://c17.yunpan.360.cn/my/?sid=#/path/to/directory
        yp http://c17.yunpan.360.cn/my/?sid=#%2Fpath%3D%2Fpath%2Fto%2Fdirectory
        # or
        yp sid=/path/to/directory
        yp sid%3D%2Fpath%2Fto%2Fdirectory

        # 下载用aria2, url 是上面的
        bp -a url

4. 参考:

> https://github.com/Shu-Ji/gorthon/blob/master/_3rdapp/CloudDisk360/main.py

---

### music.baidu.com.py - 下载或播放高品质百度音乐(music.baidu.com)

1. 依赖

        python2-mutagen (https://code.google.com/p/mutagen/)

        mpv (http://mpv.io)

2. 使用说明

    默认执行下载，如要播放，加参数-p。
    
    参数：
        
        -f, --flac  download flac
        -i, --high  download 320, default
        -l, --low   download 128
        -p, --play  play with mpv

    下载的MP3默认添加id3 tags，保存在当前目录下。
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

3. 用法

    \# bm 是music.baidu.com.py的马甲 (alias xm='python2 /path/to/music.baidu.com.py')

        # 下载专辑
        bm http://music.baidu.com/album/115032005

        # 下载单曲
        bm http://music.baidu.com/song/117948039

    播放:

        # url 是上面的
        bm -p url

4. 参考:

> http://v2ex.com/t/77685 # 第9楼

---

### music.163.com.py - 下载或播放高品质网易音乐(music.163.com)

1. 依赖

        python2-requests (https://github.com/kennethreitz/requests)

        python2-mutagen (https://code.google.com/p/mutagen/)

        mpv (http://mpv.io)

2. 使用说明

    !!! 默认下载和播放高品质音乐，如果服务器没有高品质音乐则转到低品质音乐。

    默认执行下载，如要播放，加参数-p。

    下载的MP3默认添加id3 tags，保存在当前目录下。

    日志保存在 ~/.163music.log。
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

3. 用法

    \# nm 是music.163.com.py的马甲 (alias nm='python2 /path/to/music.163.com.py')

        # 下载专辑
        nm http://music.163.com/#/album?id=18915

        # 下载单曲
        nm http://music.163.com/#/song?id=186114

        # 下载歌单
        nm http://music.163.com/#/playlist?id=12214308

        # 下载该艺术家所有专辑或 Top 50 歌曲
        nm http://music.163.com/#/artist?id=6452

        # 下载DJ节目
        nm http://music.163.com/#/dj?id=675051


    播放:

        # url 是上面的
        nm -p url

4. 参考:

> https://github.com/yanunon/NeteaseCloudMusic/wiki/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90API%E5%88%86%E6%9E%90

> http://s3.music.126.net/s/2/core.js

---

### tumblr.py - 下载某个tumblr.com的所有图片

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

2. 使用说明

    使用前需用在 http://www.tumblr.com/oauth/apps 加入一个app，证实后得到api_key，再在源码中填入，完成后则可使用。

    默认开5个进程，如需改变用参数-p [num]。

    下载的文件，保存在当前目录下。
    
    默认下载原图。
    
    支持连续下载，下载进度储存在下载文件夹内的 json.json。

3. 用法

    \# tm是tumblr.py的马甲 (alias vx='python2 /path/to/tumblr.py')

        tm http://sosuperawesome.tumblr.com/

---

### unzip.py - 解决linux下unzip乱码的问题

用法

        unzip.py azipfile.zip

代码来自以下连接，我改了一点。

> http://wangqige.com/the-solution-of-unzip-files-which-zip-under-windows/解决在Linux环境下解压zip的乱码问题

---

### torrent2magnet.py - 种子转磁力

1. 依赖
        python3

2. 使用说明

    将一个目录下的所有torrent转换成magnet，并保存于当前目录的magnet_link文件中。

2. 用法

    \# ttm是torrent2magnet.py的马甲 (alias vx='python2 /path/to/torrent2magnet.py')

        ttm /path/to/directory

3. 参考

代码来自以下连接，我改了一点。

> https://github.com/repolho/torrent2magnet

---

### 91porn.py - 下载或播放91porn

> 警告: 18岁以下者，请自觉远离。

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)

        mpv (http://mpv.io)

2. 使用说明

    > 没有解决 *7个/day* 限制

    下载工具默认为wget, 可用参数-a选用aria2

    默认执行下载，如要播放媒体文件，加参数-p。

    下载的文件，保存在当前目录下。
    
    关于播放操作:
    
    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

3. 用法

    \# pn 是91porn.py的马甲 (alias pn='python2 /path/to/91porn.py')

        pn url # 91porn.com(或其镜像) 视频的url

    播放

        pn -p url

4. 参考

> http://v2ex.com/t/110196 # 第16楼

---

### ThunderLixianExporter.user.js - A fork of https://github.com/binux/ThunderLixianExporter

一个github.com/binux的迅雷离线导出脚本的fork。

增加了mpv和mplayer的导出。

用法见: https://github.com/binux/ThunderLixianExporter

