## iscript

包含项目:

- xiami.py - 下载或播放高品质虾米音乐(xiami.com)

- pan.baidu.com.py - 百度网盘的下载和播放

- music.baidu.com.py - 下载或播放高品质百度音乐(music.baidu.com)

- tumblr.py - 下载某个tumblr.com的所有图片

- unzip.py - 解决linux下unzip乱码的问题

- torrent2magnet.py - 种子转磁力

- 91porn.py - 下载或播放91porn

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
    
    登录时需要输入验证码。

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

        # 下载该艺术家所有专辑或top 20歌曲
        xm http://www.xiami.com/artist/23460?spm=a1z1s.6928801.1561534521.115.ShW08b

        # 下载用户的收藏
        xm http://www.xiami.com/u/141825?spm=a1z1s.3521917.0.0.zI0APP


    播放:

        # url 是上面的
        xm -p url

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

---

### tumblr.py - 下载某个tumblr.com的所有图片

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

2. 使用说明

    使用前需用在 http://www.tumblr.com/oauth/apps 加入一个app，证实后得到api_key，再在源码中填入，完成后则可使用。

    默认开5个进程，如需改变用参数-p [num]。

    下载的文件，保存在当前目录下。

3. 用法

    \# tm是tumblr.py的马甲 (alias vx='python2 /path/to/tumblr.py')

        tm http://sosuperawesome.tumblr.com/

---

### unzip.py - 解决linux下unzip乱码的问题

用法

        unzip.py azipfile.zip

---

### torrent2magnet.py - 种子转磁力

1. 依赖
        python3

2. 使用说明

    将一个目录下的所有torrent转换成magnet，并保存于当前目录的magnet_link文件中。

2. 用法

    \# ttm是torrent2magnet.py的马甲 (alias vx='python2 /path/to/torrent2magnet.py')

        ttm /path/to/directory
        
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

        pn url # 91porn.com 视频的url

    播放

        pn -p url

