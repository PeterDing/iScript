## iScript

包含项目:

> *[L]* *[W]* *[LW]* 分别表示，在linux, windows, linux和windows 下通过测试。

> ***windows用户可在babun (https://github.com/babun/babun) 下运行。***

- *[L]* [xiami.py](#xiami.py) - 下载或播放高品质虾米音乐(xiami.com)

- *[L]* [pan.baidu.com.py](#pan.baidu.com.py) - 百度网盘的下载、离线下载、上传、播放、转存、文件操作

- *[L]* [bt.py](#bt.py) - magnet torrent 互转、及 过滤敏.感.词

- *[L]* [115.py](#115.py) - 115网盘的下载和播放

- *[L]* [yunpan.360.cn.py](#yunpan.360.cn.py) - 360网盘的下载

- *[L]* [music.baidu.com.py](#music.baidu.com.py) - 下载或播放高品质百度音乐(music.baidu.com)

- *[L]* [music.163.com.py](#music.163.com.py) - 下载或播放高品质网易音乐(music.163.com)

- *[L]* [flvxz_cl.py](#flvxz_cl.py) - flvxz.com 视频解析 client - 支持下载、播放

- *[L]* [tumblr.py](#tumblr.py) - 下载某个tumblr.com的所有图片

- *[L]* [unzip.py](#unzip.py) - 解决linux下unzip乱码的问题

- *[L]* [ed2k_search.py](#ed2k_search.py) - 基于 donkey4u.com 的emule搜索

- *[L]* [91porn.py](#91porn.py) - 下载或播放91porn

- *[L]* [ThunderLixianExporter.user.js](#ThunderLixianExporter.user.js) - A fork of https://github.com/binux/ThunderLixianExporter - 增加了mpv和mplayer的导出。

- 待续

---

---

<a name="xiami.py"></a>
### xiami.py - 下载或播放高品质虾米音乐(xiami.com)

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

        python2-mutagen (https://code.google.com/p/mutagen/)

        mpv (http://mpv.io)

2. 使用说明

    初次使用需要登录 xm login

    **支持淘宝账户**         xm logintaobao

    **对于淘宝账户，登录后只保存有关虾米的cookies，删除了有关淘宝的cookies**

    **vip账户**支持高品质音乐的下载和播放。

    下载的MP3默认添加id3 tags，保存在当前目录下。

    cookies保存在 ~/.Xiami.cookies。

    关于播放操作:

    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

    命令:

        # 虾米账号登录
        g
        login
        login username
        login username password

        # 淘宝账号登录
        gt
        logintaobao
        logintaobao username
        logintaobao username password

        signout                      # 退出登录

        d 或 download url1 url2 ..      # 下载
        p 或 play  url1 url2 ..         # 播放
        s 或 save  url1 url2 ..         # 收藏

    参数:

        -p, --play                 play with mpv
        -d, --undescription        不加入disk的描述
        -f num, --from_ num        从第num个开始
        -t TAGS, --tags TAGS       收藏用的tags,用英文逗号分开, eg: -t piano,cello,guitar
        -n, --undownload           不下载,用于修改已存在的MP3的id3 tags

3. 用法

    \# xm 是xiami.py的马甲 (alias xm='python2 /path/to/xiami.py')

        # 登录
        xm g
        xm login
        xm login username
        xm login username password

        # 退出登录
        xm signout

        # 下载专辑
        xm d http://www.xiami.com/album/168709?spm=a1z1s.6928801.1561534521.114.ShN6mD

        # 下载单曲
        xm d http://www.xiami.com/song/2082998?spm=a1z1s.6659513.0.0.DT2j7T

        # 下载精选集
        xm d http://www.xiami.com/song/showcollect/id/30374035?spm=a1z1s.3061701.6856305.16.fvh75t

        # 下载该艺术家所有专辑, Top 20 歌曲, radio
        xm d http://www.xiami.com/artist/23460?spm=a1z1s.6928801.1561534521.115.ShW08b

        # 下载用户的收藏, 虾米推荐, radio
        xm d http://www.xiami.com/u/141825?spm=a1z1s.3521917.0.0.zI0APP

        # 下载排行榜
        xm d http://www.xiami.com/chart/index/c/2?spm=a1z1s.2943549.6827465.6.VrEAoY

        # 下载 风格 genre, radio
        xm d http://www.xiami.com/genre/detail/gid/2?spm=a1z1s.3057857.6850221.1.g9ySan
        xm d http://www.xiami.com/genre/detail/sid/2970?spm=a1z1s.3057857.6850221.4.pkepgt

    播放:

        # url 是上面的
        xm p url

    收藏:

        xm s http://www.xiami.com/album/168709?spm=a1z1s.6928801.1561534521.114.ShN6mD
        xm s -t 'tag1,tag 2,tag 3' http://www.xiami.com/song/2082998?spm=a1z1s.6659513.0.0.DT2j7T
        xm s http://www.xiami.com/song/showcollect/id/30374035?spm=a1z1s.3061701.6856305.16.fvh75t
        xm s http://www.xiami.com/artist/23460?spm=a1z1s.6928801.1561534521.115.ShW08b

4. 参考:

> http://kanoha.org/2011/08/30/xiami-absolute-address/

> http://www.blackglory.me/xiami-vip-audition-with-no-quality-difference-between-downloading/

> https://gist.github.com/lepture/1014329

> 淘宝登录代码: https://github.com/ly0/xiami-tools

---

<a name="pan.baidu.com.py"></a>
### pan.baidu.com.py - 百度网盘的下载、离线下载、上传、播放、转存、文件操作

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)

        requests-toolbelt (https://github.com/sigmavirus24/requests-toolbelt)

        mpv (http://mpv.io)

        mplayer # 我的linux上mpv播放wmv出错，换用mplayer

2. 使用说明

    初次使用需要登录 bp login

    **支持多帐号登录**

    他人分享的网盘连接，只支持单个的下载。

    下载工具默认为wget, 可用参数-a num选用aria2

    下载的文件，保存在当前目录下。

    下载默认为非递归，递归下载加 -R

    搜索时，默认在 /

    搜索支持高亮

    上传模式默认是 c (续传)。

    理论上，上传的单个文件最大支持 2T

    cookies保存在 ~/.bp.cookies

    上传数据保存在 ~/.bp.pickle

    关于播放操作:

    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

    <a name="cmd"></a>
    命令:

    **!!注意：命令参数中，所有网盘的路径必须是 绝对路径**

        # 登录
        g
        login
        login username
        login username password

        # 删除帐号
        userdelete 或 ud

        # 切换帐号
        userchange 或 uc

        # 帐号信息
        user

        p  或 play url1 url2 .. path1 path2 ..               播放
        u  或 upload localpath remotepath                    上传
        s  或 save url remotepath [-s secret]                转存

        # 下载
        d  或 download url1 url2 .. path1 path2 ..           非递归下载 到当前目录(cwd)
        d  或 download url1 url2 .. path1 path2 .. -R        递归下载 到当前目录(cwd)
        # !! 注意:
        # d /path/to/download -R      递归下载 *download文件夹* 到当前目录(cwd)
        # d /path/to/download/ -R     递归下载 *download文件夹中的文件* 到当前目录(cwd)

        # 文件操作
        md 或 mkdir path1 path2 ..                           创建文件夹
        rn 或 rename path new_path                           重命名
        rm 或 remove path1 path2 ..                          删除
        mv 或 move path1 path2 .. /path/to/directory         移动
        cp 或 copy path /path/to/directory_or_file           复制
        cp 或 copy path1 path2 .. /path/to/directory         复制

        # 使用正则表达式进行文件操作
        rnr 或 rnre foo bar dir1 dir2 .. -I re1 re2 ..                                            重命名文件夹中的文件名
        rmr 或 rmre dir1 dir2 .. -E re1 re2 ..                    删除文件夹下匹配到的文件
        mvr 或 mvre dir1 dir2 .. /path/to/dir -H head1 head2 ..   移动文件夹下匹配到的文件
        cpr 或 cpre dir1 dir2 .. /path/to/dir -T tail1 tail2 ..   复制文件夹下匹配到的文件
        # 递归加 -R
        # rmr, mvr, cpr 中 -t, -I, -E, -H, -T 至少要有一个，放在命令行末尾
        # -I, -E, -H, -T 后可跟多个匹配式
        # 可以用 -t 指定操作的文件类型
            -t f # 文件
            -t d # 文件夹
        # rnr 中 foo bar 都是 regex
        # -y, --yes   # 不显示警示，直接进行。  ！！注意，除非你知道你做什么，否则请不要使用。
        rmr / -I '.*' -y    # ！！ 删除网盘中的所有文件

        # 回复用bt.py做base64加密的文件
        rnr /path/to/decode1 /path/to/decode2 .. -t f,bd64

        # 搜索
        f   或 find keyword1 keyword2 .. [directory]             非递归搜索
        ff  keyword1 keyword2 .. [directory]                     非递归搜索 反序
        ft  keyword1 keyword2 .. [directory]                     非递归搜索 by time
        ftt keyword1 keyword2 .. [directory]                     非递归搜索 by time 反序
        fs  keyword1 keyword2 .. [directory]                     非递归搜索 by size
        fss keyword1 keyword2 .. [directory]                     非递归搜索 by size 反序
        fn  keyword1 keyword2 .. [directory]                     非递归搜索 by name
        fnn keyword1 keyword2 .. [directory]                     非递归搜索 by name 反序
        # 递归搜索加 -R
        f 'ice and fire' /doc -R
        # 搜索所有的账户加 -t all
        f keyword1 keyword2 .. [directory] -t all -R
        f keyword1 keyword2 .. [directory] -t f,all -R
        # directory 默认为 /
        # 关于-H, -T, -I, -E
        # -I, -E, -H, -T 后可跟多个匹配式, 需要放在命令行末尾
        f keyword1 keyword2 ... [directory] -H head -T tail -I "re(gul.*) ex(p|g)ress$"
        f keyword1 keyword2 ... [directory] -H head -T tail -E "re(gul.*) ex(p|g)ress$"
        # 搜索 加 通道(只支持 donwload, play, rnre, rm, mv)
        f keyword1 keyword2 .. [directory] \| d -R              递归搜索后递归下载
        ftt keyword1 keyword2 .. [directory] \| p -R            递归搜索(by time 反序)后递归播放
        f keyword1 keyword2 .. [directory] \| rnr foo bar -R    递归搜索后rename by regex
        f keyword1 keyword2 .. [directory] \| rm -R -T tail     递归搜索后删除
        f keyword1 keyword2 .. [directory] \| mv /path/to -R    递归搜索后移动

        # 列出文件
        l path1 path2 ..                               ls by name
        ll path1 path2 ..                              ls by name 反序
        ln path1 path2 ..                              ls by name
        lnn path1 path2 ..                             ls by name 反序
        lt path1 path2 ..                              ls by time
        ltt path1 path2 ..                             ls by time 反序
        ls path1 path2 ..                              ls by size
        lss path1 path2 ..                             ls by size 反序
        l /doc/books /videos
        # 以下是只列出文件或文件夹
        l path1 path2 .. -t f                         ls files
        l path1 path2 .. -t d                         ls directorys
        # 关于-H, -T, -I, -E
        # -I, -E, -H, -T 后可跟多个匹配式, 需要放在命令行末尾
        l path1 path2 .. -H head -T tail -I "^re(gul.*) ex(p|g)ress$"
        l path1 path2 .. -H head -T tail -E "^re(gul.*) ex(p|g)ress$"
        # 显示文件size, md5
        l path1 path2 .. -v
        # 空文件夹
        l path1 path2 -t e,d
        # 非空文件夹
        l path1 path2 -t ne,d

        # 查看文件占用空间
        du path1 path2 ..               文件夹下所有*文件(不包含下层文件夹)*总大小
        du path1 path2 .. -R            文件夹下所有*文件(包含下层文件夹)*总大小
                                        如果下层文件多，会花一些时间
        # 相当于 l path1 path2 .. -t du [-R]
        # eg:
        du /doc /videos -R

        # 离线下载
        a 或 add http https ftp ed2k .. remotepath
        a 或 add magnet .. remotepath [-t {m,i,d,p}]
        a 或 add remote_torrent .. [-t {m,i,d,p}]   # 使用网盘中torrent

        # 离线任务操作
        j  或 job                               # 列出离线下载任务
        jd 或 jobdump                           # 清除全部 *非正在下载中的任务*
        jc 或 jobclear taskid1 taskid2 ..       # 清除 *正在下载中的任务*
        jca 或 jobclearall                      # 清除 *全部任务*

    参数:

        -a num, --aria2c num                aria2c分段下载数量: eg: -a 10
        -p, --play                          play with mpv
        -y, --yes                           yes # 用于 rmre, mvre, cpre, ！！慎用
        -q, --quiet                         无输出模式
        -v, --view                          view detail
                                            eg: a magnet /path -v  # 离线下载并显示下载的文件
                                            d -p url1 url2 .. -v  # 显示播放文件的完整路径
                                            l path1 path2 .. -v  # 显示文件的size, md5
        -s SECRET, --secret SECRET          提取密码
        -f number, --from_ number           从第几个开始(用于download, play)，eg: p /video -f 42
        -t ext, --type_ ext                 类型参数, 用 “,” 分隔
                                            eg:
                                            l -t f      # 文件
                                            l -t d      # 文件夹
                                            l -t du     # 查看文件占用空间
                                            l -t e,d    # 空文件夹
                                            f -t all    # 搜索所有账户
                                            a -t m,d,p,a
                                            u -t r  # 只进行 rapidupload
                                            u -t e  # 如果云端已经存在则不上传(不比对md5)
                                            u -t r,e
        -l amount, --limit amount           下载速度限制，eg: -l 100k
        -m {o,c}, --uploadmode {o,c}        上传模式:  o   # 重新上传. c   # 连续上传.
        -R, --recursive                     递归, 用于download, play, ls, find, rmre, rnre, rmre, cpre
        -H HEADS, --head HEADS                匹配开头的字符，eg: -H Headishere
        -T TAILS, --tail TAILS                匹配结尾的字符，eg: -T Tailishere
        -I INCLUDES, --include INCLUDES       不排除匹配到表达的文件名, 可以是正则表达式，eg: -I "*.mp3"
        -E EXCLUDES, --exclude EXCLUDES       排除匹配到表达的文件名, 可以是正则表达式，eg: -E "*.html"
        -c {on, off}, --ls_color {on, off}  ls 颜色，默认是on

        # -t, -H, -T, -I, -E 都能用于 download, play, ls, find, rnre, rmre, cpre, mvre

3. 用法

    \# bp 是pan.baidu.com.py的马甲 (alias bp='python2 /path/to/pan.badiu.com.py')

    登录:

        bp g
        bp login
        bp login username
        bp login username password

        # 多帐号登录
        # 一直用 bp login 即可

    删除帐号:

        bp ud

    切换帐号:

        bp uc

    帐号信息:

        bp user

    下载:

        # 下载自己网盘中的*单个或多个文件*
        bp d http://pan.baidu.com/disk/home#dir/path=/path/to/filename1 http://pan.baidu.com/disk/home#dir/path=/path/to/filename2 ..
        # or
        bp d /path/to/filename1 /path/to/filename2 ..

        # 递归下载自己网盘中的*单个或多个文件夹*
        bp d -R http://pan.baidu.com/disk/home#dir/path=/path/to/directory1 http://pan.baidu.com/disk/home#dir/path=/path/to/directory2 ..
        # or
        bp d -R /path/to/directory1 /path/to/directory2 ..
        # 递归下载后缀为 .mp3 的文件
        bp d -R /path/to/directory1 /path/to/directory2 .. -T .mp3

        # 非递归下载
        bp d /path/to/directory1 /path/to/directory2 ..

        # 下载别人分享的*单个文件*
        bp d http://pan.baidu.com/s/1o6psfnxx ..
        bp d http://pan.baidu.com/share/link?shareid=1622654699&uk=1026372002&fid=2112674284 ..

        # 下载别人加密分享的*单个文件*，密码参数-s
        bp d http://pan.baidu.com/s/1i3FVlw5 -s vuej

        # 用aria2下载
        bp d http://pan.baidu.com/s/1i3FVlw5 -s vuej -a 5
        bp d /movie/her.mkv -a 4
        bp d url -s [secret] -a 10

    播放:

        bp p /movie/her.mkv
        bp p http://pan.baidu.com/s/xxxxxxxxx -s [secret]
        bp p /movie -R     # 递归播放 /movie 中所有媒体文件

    离线下载:

        bp a http://mirrors.kernel.org/archlinux/iso/latest/archlinux-2014.06.01-dual.iso /path/to/save
        bp a https://github.com/PeterDing/iScript/archive/master.zip /path/to/save
        bp a ftp://ftp.netscape.com/testfile /path/to/save

        bp a 'magnet:?xt=urn:btih:64b7700828fd44b37c0c045091939a2c0258ddc2' /path/to/save -v -t a
        bp a 'ed2k://|file|[美]徐中約《中国近代史》第六版原版PDF.rar|547821118|D09FC5F70DEA63E585A74FBDFBD7598F|/' /path/to/save

        bp a     /path/to/a.torrent .. -v -t m,i   # 使用网盘中torrent，下载到/path/to
        # 注意   ---------------------
                           ↓
                  网盘中的torrent

    magnet离线下载 -- 文件选择:

        -t m    # 视频文件 (默认), 如: mkv, avi ..etc
        -t i    # 图像文件, 如: jpg, png ..etc
        -t d    # 文档文件, 如: pdf, doc, docx, epub, mobi ..etc
        -t p    # 压缩文件, 如: rar, zip ..etc
        -t a    # 所有文件
        m, i, d, p, a 可以任意组合(用,分隔), 如: -t m,i,d   -t d,p   -t i,p
        remotepath 默认为 /

        bp a 'magnet:?xt=urn:btih:64b7700828fd44b37c0c045091939a2c0258ddc2' /path/to/save -v -t p,d
        bp a /download/a.torrent -v -t m,i,d    # 使用网盘中torrent，下载到/download

    离线任务操作:

        bp j
        bp j 3482938 8302833
        bp jd
        bp jc taskid1 taskid2 ..
        bp jc 1208382 58239221 ..
        bp jca

    上传:

        bp u ~/Documents/reading/三体\ by\ 刘慈欣.mobi /doc -m o
        # 上传模式:
        # -m o --> 重传
        # -m c --> 续传 (默认)

        bp u ~/Videos/*.mkv /videos -t r
        # 只进行rapidupload

        bp u ~/Documents ~/Videos ~/Documents /backup -t e
        # 如果云端已经存在则不上传(不比对md5)
        # 用 -t e 时, -m o 无效

        bp u ~/Documents ~/Videos ~/Documents /backup -t r,e  # 以上两种模式

    转存:

        bp s url remotepath [-s secret]
        # url是他人分享的连接, 如: http://pan.baidu.com/share/link?shareid=xxxxxxx&uk=xxxxxxx, http://pan.baidu.com/s/xxxxxxxx
        bp s http://pan.baidu.com/share/link?shareid=xxxxxxx&uk=xxxxxxx /path/to/save
        bp s http://pan.baidu.com/s/xxxxxxxx /path/to/save
        bp s http://pan.baidu.com/s/xxxxxxxx /path/to/save -s xxxx
        bp s http://pan.baidu.com/s/xxxxxxxx#dir/path=/path/to/anything /path/to/save -s xxxx

        bp s http://pan.baidu.com/inbox/i/xxxxxxxx /path/to/save

    搜索:

        bp f keyword1 keyword2
        bp f "this is one keyword" "this is another keyword" /path/to/search

        bp f ooxx -R
        bp f 三体 /doc/fiction -R
        bp f 晓波 /doc -R

        bp ff  keyword1 keyword2 .. /path/to/music       非递归搜索 反序
        bp ft  keyword1 keyword2 .. /path/to/doc         非递归搜索 by time
        bp ftt keyword1 keyword2 .. /path/to/other       非递归搜索 by time 反序
        bp fs  keyword1 keyword2 ..                      非递归搜索 by size
        bp fss keyword1 keyword2 ..                      非递归搜索 by size 反序
        bp fn  keyword1 keyword2 ..                      非递归搜索 by name
        bp fnn keyword1 keyword2 ..                      非递归搜索 by name 反序

        # 递归搜索加 -R
        # 关于-H, -T, -I, -E
        bp f mp3 /path/to/search -H "[" "01" -T ".tmp" -I ".*-.*" -R

        # 搜索所有的账户
        f iDoNotKnow .. [directory] -t all -R
        f archlinux ubuntu .. [directory] -t f,all -T .iso -R

        # 搜索 加 通道(只支持 donwload, play, rnre, rm, mv)
        f bioloy \| d -R                          递归搜索后递归下载
        ftt ooxx \| p -R -t f                     递归搜索(by time 反序)后递归播放
        f sound \| rnr mp3 mp4 -R                 递归搜索后rename by regex
        f ccav \| rm -R -T avi                    递归搜索后删除
        f 新闻联播（大结局） \| mv /Favor -R      递归搜索后移动

    回复用bt.py做base64加密的文件:

        rnr /ooxx -t f,bd64
        !! 注意： /ooxx 中的所有文件都必须是被base64加密的，且加密段要有.base64后缀
        # 可以参考 by.py 的用法

    ls、重命名、移动、删除、复制、使用正则表达式进行文件操作:

    见[命令](#cmd)

4. 参考:

> https://gist.github.com/HououinRedflag/6191023

> https://github.com/banbanchs/pan-baidu-download/blob/master/bddown_core.py

> https://github.com/houtianze/bypy

---

<a name="bt.py"></a>
### bt.py - magnet torrent 互转、及 过滤敏.感.词

1. 依赖

        python2-requests (https://github.com/kennethreitz/requests)
        bencode (https://github.com/bittorrent/bencode)

2. 使用说明

    magnet 和 torrent 的相互转换

    ~~过滤敏.感.词功能用于净网时期的 baidu, xunlei~~

    **8.30日后，无法使用。 见 http://tieba.baidu.com/p/3265467666**

    ~~**!! 注意：过滤后生成的torrent在百度网盘只能用一次，如果需要再次使用，则需用 -n 改顶层目录名**~~

    磁力连接转种子，用的是

        http://bt.box.n0808.com
        http://btcache.me
        http://www.sobt.org  # 302 --> http://www.win8down.com/url.php?hash=
        http://www.31bt.com
        http://178.73.198.210
        http://www.btspread.com  # link to http://btcache.me
        http://torcache.net
        http://zoink.it
        http://torrage.com   # 用torrage.com需要设置代理, eg: -p 127.0.0.1:8087
        http://torrentproject.se
        http://istoretor.com
        http://torrentbox.sx
        http://www.torrenthound.com
        http://www.silvertorrent.org
        http://magnet.vuze.com

    如果有更好的种子库，请提交issue

    > 对于baidu, 加入离线任务后，需等待一段时间才会下载完成。

    命令:

        # magnet 2 torrent
        m 或 mt magnet_link1 magnet_link2 .. [-d /path/to/save]
        m -i /there/are/files -d new

        # torrent 2 magnet, 输出magnet
        t 或 tm path1 path2 ..

        # 过滤敏.感.词
        # 有2种模式
        # -t n (默认)     用数字替换文件名
        # -t be64         用base64加密文件名，torrent用百度下载后，可用 pan.baidu.com.py rnr /path -t f,bd64 改回原名字
        c 或 ct magnet_link1 magnet_link2 .. /path/to/torrent1 /path/to/torrent2 .. [-d /path/to/save]
        c -i /there/are/files and_other_dir -d new    # 从文件或文件夹中寻找 magnet，再过滤
        # 过滤敏.感.词 - 将magnet或torrent转成不敏感的 torrent
        # /path/to/save 默认为 .

        # 用base64加密的文件名:
        c magnet_link1 magnet_link2 .. /path/to/torrent1 /path/to/torrent2 .. [-d /path/to/save] -t be64

        # 使用正则表达式过滤敏.感.词
        cr 或 ctre foo bar magnet_link1 /path/to/torrent1 .. [-d /path/to/save]
        # foo bar 都是 regex

    参数:

        -p PROXY, --proxy PROXY                 proxy for torrage.com, eg: -p 127.0.0.1:8087 (默认)
        -t TYPE_, --type_ TYPE_                 类型参数：
                                                -t n (默认)     用数字替换文件名
                                                -t be64         用base64加密文件名，torrent用百度下载后，可用 pan.baidu.com.py rnr /path -t f,bd64 改回原名字
        -d DIRECTORY, --directory DIRECTORY     指定torrents的保存路径, eg: -d /path/to/save
        -n NAME, --name NAME                    顶级文件夹名称, eg: -m thistopdirectory
        -i localpath1 localpath2 .., --import_from localpath1 localpath2 ..      从本地文本文件导入magnet (用正则表达式匹配)

3. 用法

    \# bt 是bt.py的马甲 (alias bt='python2 /path/to/bt.py')

        bt mt magnet_link1 magnet_link2 .. [-d /path/to/save]
        bt tm path1 path2 ..
        bt ct magnet_link1 path1 .. [-d /path/to/save]

        bt m magnet_link1 magnet_link2 .. [-d /path/to/save]
        bt t path1 path2 ..
        bt c magnet_link1 path1 .. [-d /path/to/save]

        # 用torrage.com
        bt m magnet_link1 path1 .. -p 127.0.0.1:8087
        bt c magnet_link1 path1 .. -p 127.0.0.1:8087

        # 从文件或文件夹中寻找 magnet，再过滤
        bt c -i ~/Downloads -d new

        # 使用正则表达式过滤敏.感.词
        bt cr '.*(old).*' '\1'  magnet_link
        bt cr 'old.iso' 'new.iso' /path/to/torrent

        # 用base64加密的文件名:
        bt c magnet_link -t be64

4. 参考:

> http://blog.chinaunix.net/uid-28450123-id-4051635.html

> http://en.wikipedia.org/wiki/Torrent_file

---

<a name="115.py"></a>
### 115.py - 115网盘的下载和播放

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)

        mpv (http://mpv.io)

        mplayer # 我的linux上mpv播放wmv出错，换用mplayer

2. 使用说明

    初次使用需要登录 pan115 login

    **脚本是用于下载自己的115网盘文件，不支持他人分享文件。**

    **非vip用户下载只能有4个通道，理论上，用aria2的下载速度最大为 4*300kb/s。**

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
        -d "url"                       增加离线下载 "http/ftp/magnet/ed2k"

3. 用法

    \# pan115 是115.py的马甲 (alias pan115='python2 /path/to/115.py')

        # 登录
        pan115 g
        pan115 login
        pan115 login username
        pan115 login username password

        # 退出登录
        pan115 signout

        # 递归下载自己网盘中的*文件夹*
        pan115 http://115.com/?cid=xxxxxxxxxxxx&offset=0&mode=wangpan

        # 下载自己网盘中的*单个文件* -- 只能是115上可单独打开的文件，如pdf，视频
        pan115 http://wenku.115.com/preview/?pickcode=xxxxxxxxxxxx

        # 下载用aria2, url 是上面的
        pan115 -a url

        # 增加离线下载
        pan115 -d "magnet:?xt=urn:btih:757fc565c56462b28b4f9c86b21ac753500eb2a7&dn=archlinux-2014.04.01-dual.iso"

    播放

        # url 是上面的
        pan115 -p url

4. 参考:

> http://passport.115.com/static/wap/js/common.js?v=1.6.39

---

<a name="yunpan.360.cn.py"></a>
### yunpan.360.cn.py - 360网盘的下载

1. 依赖

        wget, aria2

        python2-requests (https://github.com/kennethreitz/requests)


2. 使用说明

    初次使用需要登录 yp login

    **!!!!!!  万恶的360不支持断点续传   !!!!!!**

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

        # 登录
        yp g
        yp login
        yp login username
        yp login username password

        # 退出登录
        yp signout

        # 递归下载自己网盘中的*文件夹*
        yp http://c17.yunpan.360.cn/my/?sid=#/path/to/directory
        yp http://c17.yunpan.360.cn/my/?sid=#%2Fpath%3D%2Fpath%2Fto%2Fdirectory
        # or
        yp sid=/path/to/directory
        yp sid%3D%2Fpath%2Fto%2Fdirectory

        # 下载用aria2, url 是上面的
        yp -a url

4. 参考:

> https://github.com/Shu-Ji/gorthon/blob/master/_3rdapp/CloudDisk360/main.py

---

<a name="music.baidu.com.py"></a>
### music.baidu.com.py - 下载或播放高品质百度音乐(music.baidu.com)

1. 依赖

        wget

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

    \# bm 是music.baidu.com.py的马甲 (alias bm='python2 /path/to/music.baidu.com.py')

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

<a name="music.163.com.py"></a>
### music.163.com.py - 下载或播放高品质网易音乐(music.163.com)

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

        python2-mutagen (https://code.google.com/p/mutagen/)

        mpv (http://mpv.io)

2. 使用说明

    **默认下载和播放高品质音乐，如果服务器没有高品质音乐则转到低品质音乐。**

    默认执行下载，如要播放，加参数-p。

    下载的MP3默认添加id3 tags，保存在当前目录下。

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

        # 下载排行榜
        nm http://music.163.com/#/discover/toplist?id=11641012


    播放:

        # url 是上面的
        nm -p url

4. 参考:

> https://github.com/yanunon/NeteaseCloudMusic/wiki/%E7%BD%91%E6%98%93%E4%BA%91%E9%9F%B3%E4%B9%90API%E5%88%86%E6%9E%90

> http://s3.music.126.net/s/2/core.js

---

<a name="flvxz_cl.py"></a>
### flvxz_cl.py - flvxz.com 视频解析 client - 支持下载、播放

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

        mpv (http://mpv.io)

2. 使用说明

    flvxz.com 视频解析

    **不提供视频合并操作**

    支持的网站:

        """
        已知支持120个以上视频网站，覆盖大多数国内视频站点，少量国外视频站点
                                                              """
                                                       -- flvxz.com

    关于播放操作:

    > 在运行脚本的终端，输入1次Enter，关闭当前播放并播放下一个文件，连续输入2次Enter，关闭当前播放并退出。

3. 用法

    \# fl是flvxz_cl.py的马甲 (alias fl='python2 /path/to/flvxz_cl.py')

    下载:

        fl http://v.youku.com/v_show/id_XNTI2Mzg4NjAw.html
        fl http://www.tudou.com/albumplay/Lqfme5hSolM/tJ_Gl3POz7Y.html

    播放:

        # url 是上面的
        fl url -p

4. 相关脚本:

> https://github.com/iambus/youku-lixian

> https://github.com/rg3/youtube-dl

> https://github.com/soimort/you-get

---

<a name="tumblr.py"></a>
### tumblr.py - 下载某个tumblr.com的所有图片

1. 依赖

        wget

        python2-requests (https://github.com/kennethreitz/requests)

2. 使用说明

    * 使用前需用在 http://www.tumblr.com/oauth/apps 加入一个app，证实后得到api_key，再在源码中填入，完成后则可使用。

    * 或者用 http://www.tumblr.com/docs/en/api/v2 提供的api_key ( fuiKNFp9vQFvjLNvx4sUwti4Yb5yGutBN4Xh10LXZhhRKjWlV4 )

    默认开5个进程，如需改变用参数-p [num]。

    下载的文件，保存在当前目录下。

    默认下载原图。

    支持连续下载，下载进度储存在下载文件夹内的 json.json。

    参数:

        -p PROCESSES, --processes PROCESSES      指定多进程数,默认为5个,最多为20个 eg: -p 20
        -c, --check           尝试修复未下载成功的图片
        -t TAG, --tag TAG     下载特定tag的图片, eg: -t beautiful

3. 用法

    \# tm是tumblr.py的马甲 (alias tm='python2 /path/to/tumblr.py')

        # 下载某个tumblr
        tm http://sosuperawesome.tumblr.com/
        tm http://sosuperawesome.tumblr.com/ -t beautiful

        # 指定tag下载
        tm beautiful
        tm cool

---

<a name="unzip.py"></a>
### unzip.py - 解决linux下unzip乱码的问题

用法

        python2 unzip.py azipfile1.zip azipfile2.zip ..
        python2 unzip.py azipfile.zip -s secret
        # -s 密码

代码来自以下连接，我改了一点。

> http://wangqige.com/the-solution-of-unzip-files-which-zip-under-windows/解决在Linux环境下解压zip的乱码问题

---

<a name="ed2k_search.py"></a>
### ed2k_search.py - 基于 donkey4u.com 的emule搜索

1. 依赖
        python2

2. 用法

    \# ed 是ed2k_search.py的马甲 (alias ed='python2 /path/to/ed2k_search.py')

        ed this is a keyword
        or
        ed "this is a keyword"

---

<a name="91porn.py"></a>
### 91porn.py - 下载或播放91porn

**警告: 18岁以下者，请自觉远离。**

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

    播放:

        pn -p url

4. 参考

> http://v2ex.com/t/110196 # 第16楼

---

<a name="ThunderLixianExporter.user.js"></a>
### ThunderLixianExporter.user.js - A fork of https://github.com/binux/ThunderLixianExporter

**一个github.com/binux的迅雷离线导出脚本的fork。**

增加了mpv和mplayer的导出。

用法见: https://github.com/binux/ThunderLixianExporter

