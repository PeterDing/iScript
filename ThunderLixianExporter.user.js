// ==UserScript==
// @name       ThunderLixianExporter
// @namespace  http://dynamic.cloud.vip.xunlei.com/
// @version    0.75
// @description  export thunder lixian url to aria2/wget
// @match      http://dynamic.cloud.vip.xunlei.com/user_task*
// @match      http://lixian.vip.xunlei.com/lx3_task.html*
// @match      http://jiayuan.xunlei.com/lxhome/lx3_task.html*
// @run-at document-end
// @copyright  2012+, Binux <root@binux.me>
// @updateURL http://s.binux.me/TLE/master/ThunderLixianExporter.meta.js
// ==/UserScript==

function tle_wrapper() {
// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<root@binux.me>
//         http://binux.me
// Created on Fri 20 Jul 2012 11:43:22 AM CST

TLE = {};

TLE.exporter = {
  '复制链接': function(todown) {
    //console.log(todown);
    var str = '<ul style="max-height: 300px; overflow-y: scroll; overflow-x: hidden;">';
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += '<li><a href="'+TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'" target="_blank">'+file.title+'</a></li>';
      });
    });
    str += "</ul>";
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': '复制选中的链接 &gt; <a href="'+"data:text/html;charset=utf-8,"+encodeURIComponent(str)+'" target="_blank">在新窗口中打开</a>', 'content': str}).show().pop({
      onHide: function() { $(document.body).click(); },
    });
  },
  'Aria2': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        var filepath = TLE.safe_title(file.title);
        if (task.tasktype == 0 && task.filelist.length > 1)
          filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
        str += "aria2c -c -s10 -x10 --out "+TLE.escape_command(filepath)+" --header 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("aria2 download command", str);
  },
  'wget': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "wget -c -O "+TLE.escape_command(TLE.safe_title(file.title))+" --header 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("wget download command", str);
  },
  'mpv': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "mpv --really-quiet --cache 8140 --cache-default 8140 --http-header-fields 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("play with mpv", str);
  },
  'mplayer': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "mplayer -really-quiet -cache 8140 -http-header-fields 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("play with mplayer", str);
  },
  "YAAW": function(todown) {
    if (TLE.getConfig("TLE_aria2_jsonrpc")) {
      show_tip("添加中...到YAAW界面查看是否添加成功");
      var aria2 = new ARIA2(TLE.getConfig("TLE_aria2_jsonrpc"));
      $.each(todown.tasklist, function(n, task) {
        $.each(task.filelist, function(l, file) {
          if (!file.downurl) return;
          var filepath = TLE.safe_title(file.title);
          if (task.tasktype == 0 && task.filelist.length > 1)
            filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
          aria2.addUri(file.downurl, {out: filepath, header: 'Cookie: gdriveid='+todown.gdriveid});
        });
      });
      hide_tip();
    } else {
      show_tip("尚未设置Aria2 JSONRPC地址");
      hide_tip();
    };
  },
  'Aria2导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        var filepath = TLE.safe_title(file.title);
        if (task.tasktype == 0 && task.filelist.length > 1)
          filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
        str += file.downurl+'\r\n  out='+filepath+'\r\n  header=Cookie: gdriveid='+todown.gdriveid+'\r\n  continue=true\r\n  max-connection-per-server=5\r\n  split=10\r\n  parameterized-uri=true\r\n\r\n';
      });
    });
    TLE.file_pop("Aria2导出文件下载", str, "aria2.down");
  },
  'IDM导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += '<\r\n'+TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'\r\ncookie: gdriveid='+todown.gdriveid+'\r\n>\r\n'
      });
    });
    TLE.file_pop("IDM导出文件下载", str, "idm.ef2");
  },
  'Orbit导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'|'+TLE.safe_title(file.title.replace("|", "_"))+'||gdriveid='+todown.gdriveid+'\r\n'
      });
    });
    TLE.file_pop("Orbit导出文件下载", str, "orbit.olt");
  },
  'eagleget': function(todown) {
    var ret = {tasks: []};
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        ret.tasks.push({
          cookie: 'gdriveid='+todown.gdriveid,
          fname: TLE.safe_title(file.title),
          url: TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))
        });
      });
    });
    TLE.file_pop("Eagleget导出文件下载(test)", JSON.stringify(ret), "eagleget.eg");
  },
};

(function(TLE) {
  function get_taskinfo(p) {
    var taskid = p.attr("taskid");
    var info = {};
    p.find("input").each(function(n, e) {
      var key = e.getAttribute("id").replace(taskid, "");
      info[key] = e.getAttribute("value");
    });
    return info;
  };

  function build_normal_taskinfo(info) {
    var taskinfo = {
      'taskname': info.taskname || info.cloud_taskname,
      'f_url': info.f_url,
      'cid': info.dcid || info.cloud_cid,
      'size': parseInt(info.ysfilesize),
      'tasktype': info.d_tasktype,
      'status': info.d_status,
    };
    var filelist = [];
    filelist.push({
      'title': info.taskname || info.cloud_taskname,
      'f_url': info.f_url,
      'downurl': info.dl_url || info.cloud_dl_url,
      'cid': info.dcid || info.cloud_cid,
      'gcid': "",
      'size': parseInt(info.ysfilesize),
    });
    taskinfo['filelist'] = filelist;

    return taskinfo;
  };
  function build_bt_taskinfo(info, rdata) {
    var taskinfo = {
      'taskname': info.taskname,
      'f_url': info.f_url,
      'cid': info.dcid,
      'size': parseInt(info.ysfilesize),
      'tasktype': info.d_tasktype,
      'status': info.d_status,
    };
    var filelist = [];
    $.each(rdata, function(n, e) {
      filelist.push({
        'title': e.title,
        'f_url': e.url,
        'downurl': e.downurl,
        'cid': e.cid,
        'gcid': e.gcid,
        'size': parseInt(e.filesize),
      });
    });
    taskinfo['filelist'] = filelist;
    return taskinfo;
  };

  TLE.safe_title = function safe_title(title) {
    return title.replace(/[\\\|\:\*\"\?\<\>]/g,"_");
  };

  TLE.down = function(_this, _do) {
    var p = $(_this).parents(".rw_list");
    var info = get_taskinfo(p);
    console.log(info);

    if (info.d_tasktype == "0") { //bt task
      show_tip("载入中...");
      $.getJSON(INTERFACE_URL+"/fill_bt_list?tid="+info.input+"&g_net="+G_section+"&uid="+G_USERID+"&callback=?", function(data) {
        hide_tip();
        var todown = {};
        todown.gdriveid = getCookie("gdriveid");
        todown.tasklist = {};
        todown.tasklist[info.input] = build_bt_taskinfo(info, data['Result'][info.input]);
        _do(todown);
      });
    } else {
      var todown = {}
      todown.gdriveid = getCookie("gdriveid");
      todown.tasklist = {};
      todown.tasklist[info.input] = build_normal_taskinfo(info);
      _do(todown);
    };
  };

  TLE.batch_down = function(_this, _do) {
    var ck = document.getElementsByName("ck");
    var bt_task_list = [];
    var normal_task_list = [];
    $.each(ck, function(n, e) {
      if (e.checked == false) return;

      var taskid = e.value;
      var d_status = $("#d_status"+taskid).val();
      var d_tasktype = $("#d_tasktype"+taskid).val();
      var d_flag = $("#dflag"+taskid).val();
      if (d_flag != 4 && d_status == 2) {
        if (d_tasktype == 0) {
          bt_task_list.push(taskid);
        } else {
          normal_task_list.push(taskid);
        };
      };
    });

    if (bt_task_list.length) {
      show_tip("载入中...");
      $.getJSON(INTERFACE_URL+"/fill_bt_list?tid="+bt_task_list.join(",")+"&g_net="+G_section+"&uid="+G_USERID+"&callback=?", function(data) {
        hide_tip();
        var todown = {};
        todown.gdriveid = getCookie("gdriveid");
        todown.tasklist = {};
        $.each(data['Result'], function(n, e) {
          var info = get_taskinfo($("#tr_c"+n));
          todown.tasklist[n] = build_bt_taskinfo(info, e);
        });
        $.each(normal_task_list, function(n, e) {
          var info = get_taskinfo($("#tr_c"+e));
          todown.tasklist[e] = build_normal_taskinfo(info);
        });
        _do(todown);
      });
    } else {
      var todown = {};
      todown.gdriveid = getCookie("gdriveid");
      todown.tasklist = {};
      $.each(normal_task_list, function(n, e) {
        var info = get_taskinfo($("#tr_c"+e));
        todown.tasklist[e] = build_normal_taskinfo(info);
      });
      _do(todown);
    };
  };

  TLE.bt_down = function(_this, _do) {
    var ck = document.getElementsByName("bt_list_ck");
    var files = [];
    $.each(ck, function(n, e) {
      if (e.checked == false) return;
      var fid = e.getAttribute("_i");
      var file = {
        'title': $("#bt_taskname"+fid).val(),
        'url': $("#bturl"+fid).val(),
        'downurl': $("#btdownurl"+fid).val(),
        'cid': $("#btcid"+fid).val(),
        'gcid': $("#btgcid"+fid).val(),
        'filesize': $("#bt_filesize"+fid).val(),
      };
      files.push(file);
    });
    var taskid = $("#view_bt_taskid").val();
    var info = get_taskinfo($("#tr_c"+taskid));

    var todown = {};
    todown.gdriveid = getCookie("gdriveid");
    todown.tasklist = {};
    todown.tasklist[taskid] = build_bt_taskinfo(info, files);
    //console.log(todown);

    _do(todown);

    //console.log("bt_down");
  };

  TLE.bt_down_one = function(_this, _do) {
    var files = []
    var fid = $(_this).parents(".rw_list").attr("i");
    var file = {
      'title': $("#bt_taskname"+fid).val(),
      'url': $("#bturl"+fid).val(),
      'downurl': $("#btdownurl"+fid).val(),
      'cid': $("#btcid"+fid).val(),
      'gcid': $("#btgcid"+fid).val(),
      'filesize': $("#bt_filesize"+fid).val(),
    };
    files.push(file);
    var taskid = $("#view_bt_taskid").val();
    var info = get_taskinfo($("#tr_c"+taskid));

    var todown = {};
    todown.gdriveid = getCookie("gdriveid");
    todown.tasklist = {};
    todown.tasklist[taskid] = build_bt_taskinfo(info, files);
    //console.log(todown);

    _do(todown);

    //console.log("bt_down");
  };

  TLE.getbtn = function(_this) {
    $(_this).parents(".TLE_get_btnbox").find(".TLE_p_getbtn").toggle();
    close_rightmenu_layer();
    return false;
  };

  TLE.text_pop = function(title, content) {
    content = $('<div></div>').text(content).html()
    content = '<textarea style="width: 100%; height: 260px;">'+content+'</textarea>'
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
      onHide: function() { $(document.body).click(); },
    });
  };
  TLE.file_pop = function(title, content, filename) {
    var url = "data:text/html;charset=utf-8,"+encodeURIComponent(content);
    var content = '<div style="width: 100%; height: 100px;">'
                    +'<div style="padding: 30px 0 0 30%;">'
                      +'<a href="'+url+'" target="_blank" title="右键另存为" class="TLE_down_btn" download="'+filename+'"><span><em class="TLE_icdwlocal">导出文件</em></span></a>'
                      +(isChrome ? '' : '(右键另存为'+filename+')')
                    +'</div>'
                 +'</div>'
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
      onHide: function() { $(document.body).click(); },
    });
  };
  TLE.window_pop = function(title, content) {
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
      onHide: function() { $(document.body).click(); },
    });
  };

  TLE.multiple_server_fix = function(url) {
    return "'"+url.replace("gdl", "'{gdl,dl.{f,g,h,i,twin}}'")+"'";
  }

  function encode_utf8(s) {
    return unescape( encodeURIComponent( s ) );
  };
  function to_hex(num) {
    var s = num.toString(16);
    if (s.length == 1)
      return '0'+s;
    else
      return s;
  };
  var thunder_filename_mask = [0x61, 0x31, 0xe4, 0x5f, 0x00, 0x00, 0x00, 0x00];
  function thunder_filename_encode(filename) {
    var result = ["01", ];
    $.each(encode_utf8(filename), function(i, n) {
      result.push(to_hex(n.charCodeAt(0)^thunder_filename_mask[i%8]).toUpperCase())
    });
    while (result.length % 8 != 1) {
      result.push(to_hex(thunder_filename_mask[(result.length-1)%8]).toUpperCase());
    }
    return result.join("");
  };

  TLE.url_rewrite = function(url, filename) {
    url = url.replace(/&n=\w+/, "&n="+thunder_filename_encode(filename));
    return url;
  };

  var alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  TLE.escape_command = function(str) {
    var result = "";
    for (var i = 0; i < str.length; i++) {
      if (alpha.indexOf(str[i]) == -1)
        result += "\\"+str[i];
      else
        result += str[i];
    }
    return result;
  };

  //setting
  TLE.getConfig = function(key) {
    if (window.localStorage) {
      return window.localStorage.getItem(key) || "";
    } else {
      return getCookie(key);
    }
  };
  TLE.setConfig = function(key, value) {
    if (window.localStorage) {
      window.localStorage.setItem(key, value);
    } else {
      setGdCookie(key, value, 86400*365);
    }
  };
  //set default config
  if (TLE.getConfig("TLE_exporter") == "") {
    var exporters = [];
    for (var key in TLE.exporter) {
      exporters.push(key);
    };
    TLE.setConfig("TLE_exporter", exporters.join("|"));
  };

  function init() {
    //css
    $("head").append('<style>'
          +'.TLE_get_btnbox {position:relative; float:left; z-index:11}'
          +'.TLE_getbtn {position: absolute; top:24px; left:0; border:1px #6FB2F3 solid; background:#fff; width:115px;-moz-border-radius:3px;-webkit-border-radius:3px;border-radius:3px;-moz-box-shadow:2px 2px 3px #ddd;-webkit-box-shadow:2px 2px 3px #ddd;}'
          +'.TLE_getbtn a {display:block; height:22px; line-height:22px; padding-left:18px}'
          +'.TLE_getbtn a:hover {background:#E4EFF9 url(http://cloud.vip.xunlei.com/190/img/ic_dianbo.png) no-repeat 8px 8px; *background-position:8px 6px ; text-decoration:none}'
          +'.TLE_get_btnbox .TLE_getlink {width:98px; height:22px; float:left; line-height:21px;*line-height:24px;display:block;color:#000000; margin-right:5px; overflow:hidden;background:url(http://cloud.vip.xunlei.com/190/img/bg_btnall.png?197) no-repeat  0 -390px}'
          +'.TLE_get_btnbox .TLE_link_gettxt {float:left; display: inline ; width:53px; text-align:center; padding-left:24px; color:#000}'
          +'.TLE_get_btnbox .TLE_link_gettxt:hover {text-decoration:none}'
          +'.rwbox .rwset .TLE_link_getic {float:left; display:block; width:20px;height:22px;}'
          +'.TLE_hiden {display: none; }'
          +'.TLE_down_btn {background: url(http://cloud.vip.xunlei.com/190/img/lx/bg_rpx.png) no-repeat 0 999em; display: block; float: left; margin: 0 1px; overflow: hidden; color: white; height: 28px; padding-left: 8px; background-position: 0 -60px; text-decoration: none; }'
          +'.TLE_down_btn span {background: url(http://cloud.vip.xunlei.com/190/img/lx/bg_rpx.png) no-repeat 0 999em; display: block; float: left; height: 28px; line-height: 27px; cursor: pointer; padding-right: 8px; background-position:100% -60px; }'
          +'.TLE_down_btn:active {background-position:0 -28px; }'
          +'.TLE_down_btn:active span {background-position:right -28px;}'
          +'.TLE_icdwlocal { padding-left: 20px; display: inline-block; background: url(http://cloud.vip.xunlei.com/190/img/lx/bg_menu.png) no-repeat 0 999em; background-position: 0 -108px; }'

          +'.rwbtn.ic_redownloca { display: none !important; }'
          +'.menu { width: 700px !important; }'
          // for thunder css
          +'.rwset {width:530px;}'
        +'</style>');
    //pop
    $("body").append('<div id="TLE_text_pop" class="pop_rwbox" style="display: none;margin: 0;"></div>');
    $("body").append('<textarea id="TLE_text_tpl" style="display: none;"></textarea>');
    $("#TLE_text_tpl").text('<div class="p_rw_pop">'
                            +'<div class="tt_box onlytitle">'
                              +'<h3>$[title]</h3>'
                            +'</div>'
                            +'<div class="psc_info">'
                              +'$[content]'
                            +'</div>'
                            +'<a href="#" class="close" title="关闭">关闭</a>'
                          +'</div>');
    $("#setting_main_tpl").text($("#setting_main_tpl").text().replace(/(<\/div>\s+<div class="btnin">)/,
          '<div class="doline mag01"></div>'
            +'<h3 style="background-position: 0 -180px;">Thunder Lixian Exporter 设定</h3>'
            +'<ul>'
              +'<li><b>启用以下导出器</b></li>'
              +'<li>'+(function(){
                var enabled_exporter = TLE.getConfig("TLE_exporter").split("|");
                var str = '';
                for (var name in TLE.exporter) {
                  str += '<span class="rw_col"><input type="checkbox" class="TLE_setting_ck" name="TLE_ck_'+name+'" '+(enabled_exporter.indexOf(name) == -1 ? "" : "checked")+' />'+name+'</span>';
                }
                return str;
              })()+'</li>'
              +'<li><b>Aria2 JSON-RPC Path</b></li>'
              +'<li>Path: <input type="text" id="TLE_aria2_jsonrpc" style="width: 350px" value="'+TLE.getConfig("TLE_aria2_jsonrpc")+'"/></li>'
            +'</ul>'
          +'$1'));
    var _set_notice_submit = set_notice_submit;
    set_notice_submit = function(f) {
      _set_notice_submit(f);
      var enabled_exporter = [];
      $(".TLE_setting_ck").each(function(n, e) {
        if (e.checked) enabled_exporter.push(e.name.replace(/^TLE_ck_/, ""));
      });
      var config_str = (enabled_exporter.length == 0) ? "_" : enabled_exporter.join("|");
      var jsonrpc_path = $("#TLE_aria2_jsonrpc").val();
      if (TLE.getConfig("TLE_exporter") != config_str || TLE.getConfig("TLE_aria2_jsonrpc") != jsonrpc_path) {
        TLE.setConfig("TLE_exporter", config_str);
        TLE.setConfig("TLE_aria2_jsonrpc", jsonrpc_path);
        TS2.show('设置已生效',1);
        setTimeout(function(){
          setting.hide();
          location.reload(true);
        }, 1*1000);
      }
    };

    function exporter_anchors(type) {
      var enabled_exporter = TLE.getConfig("TLE_exporter").split("|");
      var str = '';
      $.each(TLE.exporter, function(n, f) {
        if (enabled_exporter.indexOf(n) == -1) return;
        str+=('<a href="#" title="'+n+'" onmouseover="this.className=\'sel_on\'" onmouseout="this.className=\'\'" onclick="'+type+'(this, TLE.exporter[\''+n+'\'])">'+n+'</a>');
      });
      return str;
    }
    //down
    $(".rwbtn.ic_redownloca").each(function(n, e) {
      $(e).after('<div class="TLE_get_btnbox">'
                  + '<span class="TLE_getlink">'
                    + '<a href="#" class="TLE_link_gettxt TLE-down-text" style="padding-left: 20px; width: 57px;" onclick='+e.getAttribute("onclick")+'>取回本地</a>'
                    + '<a href="#" class="TLE_link_getic TLE-down-btn" onclick="return TLE.getbtn(this);"></a>'
                  + '</span>'
                  + '<div class="TLE_p_getbtn TLE_getbtn" style="display: none;">'
                    + exporter_anchors("TLE.down")
                  + '</div>'
                + '</div>');
    });

    //batch_down
    $("#li_task_down,#li_task_download").after('<a href="#" id="TLE_batch_down" title="批量导出" class="btn_m noit"><span><em class="icdwlocal">批量导出</em></span></a>')
                      .parents(".main_link").append(
                            '<div id="TLE_batch_getbtn" class="TLE_getbtn" style="top: 30px; display:none;">'
                            + exporter_anchors("TLE.batch_down")
                          + '</div>');
    var _task_check_click = task_check_click;
    task_check_click = function() {
      _task_check_click();
      if ($("#li_task_down,#li_task_download").hasClass("noit")) {
        $("#TLE_batch_down").addClass("noit").unbind("click");
      } else {
        $("#TLE_batch_down").removeClass("noit").unbind("click").click(function() {
          $("#TLE_batch_getbtn").css("left", $("#TLE_batch_down").position().left);
          $("#TLE_batch_getbtn").toggle();
          return false;
        });
      };
      //console.log("task_check_click called");
    };
    $('input[name=ck],input#ckbutton').click(task_check_click);

    //bt_down
    $("#view_bt_list_nav_tpl").text($("#view_bt_list_nav_tpl").text().replace('取回本地</em></span></a>',
          '取回本地</em></span></a>'
          +'<a href="#" class="btn_m noit" title="批量导出" id="TLE_bt_down"><span><em class="icdwlocal">批量导出</em></span></a>'
          +'<div id="TLE_bt_getbtn" class="TLE_getbtn" style="top: 30px; display:none;">'
            + exporter_anchors("TLE.bt_down")
          + '</div>'));
    $("#view_bt_list_tpl").text($("#view_bt_list_tpl").text().replace('ic_redownloca" title="">取回本地</a>',
        'ic_redownloca" title="">取回本地</a>'
        +'<div class="TLE_get_btnbox">'
          + '<span class="TLE_getlink">'
            + '<a href="#" class="TLE_link_gettxt TLE-down-text" style="padding-left: 20px; width: 57px;" onclick="thunder_download($[p.i],1);return false;">取回本地</a>'
            + '<a href="#" class="TLE_link_getic TLE-down-btn" onclick="return TLE.getbtn(this);"></a>'
          + '</span>'
          + '<div class="TLE_p_getbtn TLE_getbtn" style="display: none;">'
            + exporter_anchors("TLE.bt_down_one")
          + '</div>'
        + '</div>'));
    var _bt_view_nav = bt_view_nav;
    bt_view_nav = function() {
      _bt_view_nav();
      if ($("#view_bt_list_nav_down").hasClass("noit")) {
        $("#TLE_bt_down").addClass("noit").unbind("click");
      } else {
        $("#TLE_bt_down").removeClass("noit").unbind("click").click(function() {
          $("#TLE_bt_getbtn").css("left", $("#TLE_bt_down").position().left);
          $("#TLE_bt_getbtn").toggle();
          return false;
        });
      };
      $("#TLE_bt_getbtn").hide();
      //console.log("bt_view_nav called");
    };

    //close menu binding
    $(document.body).bind("click",function(){
      $("div.TLE_p_getbtn, #TLE_batch_getbtn, #TLE_bt_getbtn").hide();
    });
    $("div.rw_list").click(function(e){
      $("div.TLE_p_getbtn, #TLE_batch_getbtn, #TLE_bt_getbtn").hide();
    });
    $("div.TLE_get_btnbox").click(function(e){e.stopPropagation();});
  };

  init();
})(TLE);

var ARIA2 = (function() {
  var jsonrpc_version = '2.0';

  function get_auth(url) {
    return url.match(/^(?:(?![^:@]+:[^:@\/]*@)[^:\/?#.]+:)?(?:\/\/)?(?:([^:@]*(?::[^:@]*)?)?@)?/)[1];
  };

  function request(jsonrpc_path, method, params) {
    var request_obj = {
      jsonrpc: jsonrpc_version,
      method: method,
      id: (new Date()).getTime().toString(),
    };
    if (params) request_obj['params'] = params;

    var xhr = new XMLHttpRequest();
    var auth = get_auth(jsonrpc_path);
    jsonrpc_path = jsonrpc_path.replace(/^((?![^:@]+:[^:@\/]*@)[^:\/?#.]+:)?(\/\/)?(?:(?:[^:@]*(?::[^:@]*)?)?@)?(.*)/, '$1$2$3'); // auth string not allowed in url for firefox
    xhr.open("POST", jsonrpc_path+"?tm="+(new Date()).getTime().toString(), true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
    if (auth) xhr.setRequestHeader("Authorization", "Basic "+btoa(auth));
    xhr.send(JSON.stringify(request_obj));
  };

  return function(jsonrpc_path) {
    this.jsonrpc_path = jsonrpc_path;
    this.addUri = function (uri, options) {
      request(this.jsonrpc_path, 'aria2.addUri', [[uri, ], options]);
    };
    return this;
  }
})();
} // end of wrapper

function tle_lx3_wrapper() {
seajs.use("jquery", function(){
// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2013-12-27 23:00:34

TLE = {};

TLE.exporter = {
  '复制链接': function(todown) {
    //console.log(todown);
    var str = '<ul style="max-height: 300px; overflow-y: scroll; overflow-x: hidden;">';
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += '<li><a href="'+TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'" target="_blank">'+file.title+'</a></li>';
      });
    });
    str += "</ul>";
    TLE.window_pop('复制选中的链接 &gt; <a href="'+"data:text/html;charset=utf-8,"+encodeURIComponent(str)+'" target="_blank">在新窗口中打开</a>', str);
  },
  'Aria2': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        var filepath = TLE.safe_title(file.title);
        if (task.tasktype === 0 && task.filelist.length > 1)
          filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
        str += "aria2c -c -s10 -x10 --out "+TLE.escape_command(filepath)+" --header 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("aria2 download command", str);
  },
  'wget': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "wget -c -O "+TLE.escape_command(TLE.safe_title(file.title))+" --header 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("wget download command", str);
  },
  'mpv': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "mpv --really-quiet --cache 8140 --cache-default 8140 --http-header-fields 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("play with mpv", str);
  },
  'mplayer': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += "mplayer -really-quiet -cache 8140 -http-header-fields 'Cookie: gdriveid="+todown.gdriveid+";' '"+file.downurl+"'\n";
      });
    });
    TLE.text_pop("play with mplayer", str);
  },
  "YAAW": function(todown) {
    if (TLE.getConfig("TLE_aria2_jsonrpc")) {
      TLE.tip("添加中...到YAAW界面查看是否添加成功");
      var aria2 = new ARIA2(TLE.getConfig("TLE_aria2_jsonrpc"));
      $.each(todown.tasklist, function(n, task) {
        $.each(task.filelist, function(l, file) {
          if (!file.downurl) return;
          var filepath = TLE.safe_title(file.title);
          if (task.tasktype === 0 && task.filelist.length > 1)
            filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
          aria2.addUri(file.downurl, {out: filepath, header: 'Cookie: gdriveid='+todown.gdriveid});
        });
      });
      TLE.hide_tip();
    } else {
      TLE.tip("尚未设置Aria2 JSONRPC地址", 5);
    }
  },
  'Aria2导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        var filepath = TLE.safe_title(file.title);
        if (task.tasktype === 0 && task.filelist.length > 1)
          filepath = TLE.safe_title(task.taskname) + "/" + TLE.safe_title(file.title.replace(/\\+\*?/g,"/"));
        str += file.downurl+'\r\n  out='+filepath+'\r\n  header=Cookie: gdriveid='+todown.gdriveid+'\r\n  continue=true\r\n  max-connection-per-server=5\r\n  split=10\r\n  parameterized-uri=true\r\n\r\n';
      });
    });
    TLE.file_pop("Aria2导出文件下载", str, "aria2.down");
  },
  'IDM导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += '<\r\n'+TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'\r\ncookie: gdriveid='+todown.gdriveid+'\r\n>\r\n';
      });
    });
    TLE.file_pop("IDM导出文件下载", str, "idm.ef2");
  },
  'Orbit导出': function(todown) {
    //console.log(todown);
    var str = "";
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        str += TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))+'|'+TLE.safe_title(file.title.replace("|", "_"))+'||gdriveid='+todown.gdriveid+'\r\n';
      });
    });
    TLE.file_pop("Orbit导出文件下载", str, "orbit.olt");
  },
  'eagleget导出': function(todown) {
    var ret = {tasks: []};
    $.each(todown.tasklist, function(n, task) {
      $.each(task.filelist, function(l, file) {
        if (!file.downurl) return;
        ret.tasks.push({
          cookie: 'gdriveid='+todown.gdriveid,
          fname: TLE.safe_title(file.title),
          url: TLE.url_rewrite(file.downurl, TLE.safe_title(file.title))
        });
      });
    });
    TLE.file_pop("Eagleget导出文件下载(test)", JSON.stringify(ret), "eagleget.eg");
  },
};

(function(TLE) {
  function get_taskinfo(taskid) {
    return {
      taskname: $("#tr_c"+taskid+" .title .w_title").attr("title"),
      title: $("#tr_c"+taskid+" .title .w_title").attr("title"),
      f_url: $("#f_url"+taskid).val(),
      downurl: $("#dl_url"+taskid).val(),
      cid: $("#dcid"+taskid).val(),
      gcid: $("#gcid"+taskid).val(),
      size: parseInt($("#ysfilesize"+taskid).val()),
      tasktype: parseInt($("#d_tasktype"+taskid).val()),
      status: $("#d_status"+taskid).val(),
    };
  }
  function get_bt_taskinfo(taskid) {
    return {
      title: $("#bt_taskname"+taskid).val(),
      f_url: $("#bturl"+taskid).val(),
      downurl: $("#btdownurl"+taskid).val(),
      cid: $("#btcid"+taskid).val(),
      gcid: $("#btgcid"+taskid).val(),
      size: $("#bt_filesize"+taskid).val(),
      status: $("#btd_status"+taskid).val(),
    };
  }

  function build_bt_taskinfo(info, rdata) {
    var taskinfo = {
      'taskname': info.taskname,
      'f_url': info.f_url,
      'cid': info.dcid,
      'size': parseInt(info.ysfilesize),
      'tasktype': parseInt(info.d_tasktype),
      'status': info.d_status,
    };
    var filelist = [];
    $.each(rdata, function(n, e) {
      filelist.push({
        'title': e.title,
        'f_url': e.url,
        'downurl': e.downurl,
        'cid': e.cid,
        'gcid': e.gcid,
        'size': parseInt(e.filesize),
      });
    });
    taskinfo['filelist'] = filelist;
    return taskinfo;
  };

  TLE.safe_title = function safe_title(title) {
    return title.replace(/[\\\|\:\*\"\?\<\>]/g,"_");
  };

  TLE.bt_down = function(_this, _do) {
    var ck = document.getElementsByName("bt_list_ck");
    var files = [];
    $.each(ck, function(n, e) {
      if (e.checked == false) return;
      var fid = e.getAttribute("_i");
      var file = {
        'title': $("#bt_taskname"+fid).val(),
        'url': $("#bturl"+fid).val(),
        'downurl': $("#btdownurl"+fid).val(),
        'cid': $("#btcid"+fid).val(),
        'gcid': $("#btgcid"+fid).val(),
        'filesize': $("#bt_filesize"+fid).val(),
      };
      files.push(file);
    });
    var taskid = $("#view_bt_taskid").val();
    var info = get_taskinfo($("#tr_c"+taskid));

    var todown = {};
    todown.gdriveid = getCookie("gdriveid") || $("#cok").val();
    todown.tasklist = {};
    todown.tasklist[taskid] = build_bt_taskinfo(info, files);
    //console.log(todown);

    _do(todown);

    //console.log("bt_down");
  };

  TLE.text_pop = function(title, content) {
    content = $('<div></div>').text(content).html()
    content = '<textarea style="width: 100%; height: 260px;">'+content+'</textarea>'
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
      //onHide: function() { $(document.body).click(); },
    });
  };
  TLE.file_pop = function(title, content, filename) {
    var url = "data:text/html;charset=utf-8,"+encodeURIComponent(content);
    if (isChrome) {
      $('<a href="'+url+'" target="_blank" style="display:none;" download="'+filename+'"></a>').appendTo('body').get(0).click();
    } else {
      var content = '<div style="width: 100%; height: 100px;">'
                      +'<div style="padding: 30px 0 0 30%;">'
                        +'<a href="'+url+'" target="_blank" title="右键另存为" class="pop_btn" download="'+filename+'"><span><em class="TLE_icdwlocal">导出文件</em></span></a>'
                        +(isChrome ? '' : '(右键另存为'+filename+')')
                      +'</div>'
                   +'</div>'
      $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
        //onHide: function() { $(document.body).click(); },
      });
    }
  };
  TLE.window_pop = function(title, content) {
    $("#TLE_text_pop").tpl("TLE_text_tpl", {'title': title, 'content': content}).show().pop({
      //onHide: function() { $(document.body).click(); },
    });
  };
  TLE.tip = function(content, time) {
    TS2.show(content, time);
  };
  TLE.hide_tip = function() {
    TS2.hide();
  };

  TLE.multiple_server_fix = function(url) {
    return "'"+url.replace("gdl", "'{gdl,dl.{f,g,h,i,twin}}'")+"'";
  }

  function encode_utf8(s) {
    return unescape( encodeURIComponent( s ) );
  };
  function to_hex(num) {
    var s = num.toString(16);
    if (s.length == 1)
      return '0'+s;
    else
      return s;
  };
  var thunder_filename_mask = [0x61, 0x31, 0xe4, 0x5f, 0x00, 0x00, 0x00, 0x00];
  function thunder_filename_encode(filename) {
    var result = ["01", ];
    $.each(encode_utf8(filename), function(i, n) {
      result.push(to_hex(n.charCodeAt(0)^thunder_filename_mask[i%8]).toUpperCase())
    });
    while (result.length % 8 != 1) {
      result.push(to_hex(thunder_filename_mask[(result.length-1)%8]).toUpperCase());
    }
    return result.join("");
  };

  TLE.url_rewrite = function(url, filename) {
    url = url.replace(/&n=\w+/, "&n="+thunder_filename_encode(filename));
    return url;
  };

  var alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  TLE.escape_command = function(str) {
    var result = "";
    for (var i = 0; i < str.length; i++) {
      if (alpha.indexOf(str[i]) == -1)
        result += "\\"+str[i];
      else
        result += str[i];
    }
    return result;
  };

  //setting
  TLE.getConfig = function(key) {
    if (window.localStorage) {
      return window.localStorage.getItem(key) || "";
    } else {
      return getCookie(key);
    }
  };
  TLE.setConfig = function(key, value) {
    if (window.localStorage) {
      window.localStorage.setItem(key, value);
    } else {
      setGdCookie(key, value, 86400*365);
    }
  };
  //set default config
  if (TLE.getConfig("TLE_exporter") == "") {
    var exporters = [];
    for (var key in TLE.exporter) {
      exporters.push(key);
    };
    TLE.setConfig("TLE_exporter", exporters.join("|"));
  };

  function init() {
    //css
    $("head").append('<style>'
          +'#TLE_setting { padding: 10px 20px 20px 20px; }'
          +'#TLE_setting span { padding-left: 1em; }'
          +'#TLE_setting li { margin-top: 0.5em; }'
          +'#TLE_exporter_select { padding: 10px 20px 20px 20px; }'
          +'</style>');
    //pop
    $("body").append('<div id="TLE_text_pop" class="lixian_pop_wp pop_w400" style="display:none;margin:0;"></div>');
    $("body").append('<textarea id="TLE_text_tpl" style="display: none;"></textarea>');
    $("#TLE_text_tpl").text('<div class="lixian_pop">'
                            +'<div class="l_p_hd">'
                              +'<h3>$[title]</h3>'
                            +'</div>'
                            +'<div class="l_p_bd">'
                              +'$[content]'
                            +'</div>'
                            +'<a class="pop_close" title="关闭浮层" close="1" id="close">关闭浮层</a>'
                          +'</div>');
    //setting
    $("#view_down_bar ul").prepend('<li> <a href="#" id="TLE_setting_anchor">TLE设置</a></li>');
    $("#TLE_setting_anchor").on("click", function() {
      var content = '<div id="TLE_setting"><ul>'
                      +'<li><b>启用以下导出器</b></li>'
                      +'<li>'+(function(){
                        var enabled_exporter = TLE.getConfig("TLE_exporter").split("|");
                        var str = '';
                        for (var name in TLE.exporter) {
                          str += '<span class="rw_col"><input type="checkbox" class="TLE_setting_ck" name="TLE_ck_'+name+'" '+(enabled_exporter.indexOf(name) == -1 ? "" : "checked")+' />'+name+'</span>';
                        }
                        return str;
                      })()+'</li>'
                      +'<li><b>Aria2 JSON-RPC Path</b></li>'
                      +'<li>Path: <input type="text" id="TLE_aria2_jsonrpc" style="width: 350px" value="'+TLE.getConfig("TLE_aria2_jsonrpc")+'"/></li>'
                    +'</ul>'
                  +'</div>'
                +'</div>'
                +'<div class="l_p_ft"><div class="btn_area"><a id="TLE_setting_ok" class="pop_btn">确定</a> <a close="1" class="pop_btn pop_btn_cancel">取消</a></div></div>';
      $("#TLE_text_pop").tpl("TLE_text_tpl", {title: "Thunder Lixian Exporter 设定", content: content}).show().pop();
      $("#TLE_setting_ok").on("click", function() {
        var enabled_exporter = [];
        $(".TLE_setting_ck").each(function(n, e) {
          if (e.checked) enabled_exporter.push(e.name.replace(/^TLE_ck_/, ""));
        });
        var config_str = (enabled_exporter.length == 0) ? "_" : enabled_exporter.join("|");
        var jsonrpc_path = $("#TLE_aria2_jsonrpc").val();
        if (TLE.getConfig("TLE_exporter") != config_str || TLE.getConfig("TLE_aria2_jsonrpc") != jsonrpc_path) {
          TLE.setConfig("TLE_exporter", config_str);
          TLE.setConfig("TLE_aria2_jsonrpc", jsonrpc_path);
        }
        $("a.pop_close:visible").click();
        TLE.tip("配置已保存", 5);
      });
    });
    //download binding
    function exporter_anchors() {
      var enabled_exporter = TLE.getConfig("TLE_exporter").split("|");
      var str = '';
      $.each(TLE.exporter, function(n, f) {
        if (enabled_exporter.indexOf(n) == -1) return;
        str+=('<li><a href="#" title="'+n+'" onclick="TLE.exporter[\''+n+'\'](TLE.todown);return false;">'+n+'</a></li>');
      });
      return str;
    }
    function show_exporter_selector() {
      $("#TLE_text_pop").tpl("TLE_text_tpl", {title: "您正在使用Thunder Lixian Exporter",
                             content: '<ul id="TLE_exporter_select">'
                             +exporter_anchors()
                             +'</ul>'}).pop();
    }

    TLE.todown = {};
    window.thunder_download = function(taskid, type) {
      TLE.todown = {};
      TLE.todown.gdriveid = getCookie("gdriveid") || $("#cok").val();
      if (type === 1) {
        // bt_down_one
        var taskinfo = {
          taskname: $("#bt_info_list .title .w").text(),
          f_url: null,
          cid: null,
          size: null,
          tasktype: 0,
          status: 2,
        }
        var filelist = [];
        filelist.push(get_bt_taskinfo(taskid));
        taskinfo['filelist'] = filelist;
        TLE.todown.tasklist = {};
        TLE.todown.tasklist['0'] = taskinfo;
      } else {
        // down
        var taskinfo = get_taskinfo(taskid);
        var filelist = [];
        filelist.push(get_taskinfo(taskid));
        taskinfo['filelist'] = filelist;
        TLE.todown.tasklist = {};
        TLE.todown.tasklist[taskid] = taskinfo;
      }
      show_exporter_selector();
    }
    window.bt_task_down = function(cid, taskid) {
      // bt_down
      batch_down_all_f([taskid, ]);
    }
    window.batch_down_all_f = function(taskids) {
      // batch_down
      if (!taskids) {
        taskids = [];
        $("span[name=ck][checked]").each(function(n, e) {
          taskids.push($(e).attr("value"));
        });
      }

      var bt_task_list = [], normal_task_list = [];
      $.each(taskids, function(n, taskid) {
        var d_status = $("#d_status"+taskid).val();
        var d_tasktype = parseInt($("#d_tasktype"+taskid).val());
        var d_flag = $("#dflag"+taskid).val();
        if (d_flag != 4 && d_status == 2) {
          if (d_tasktype == 0) {
            bt_task_list.push(taskid);
          } else {
            normal_task_list.push(taskid);
          };
        };
      });

      if (bt_task_list.length) {
        TLE.tip("载入中...");
        $.getJSON(INTERFACE_URL+"/fill_bt_list?tid="+bt_task_list.join(",")+"&g_net="+G_section+"&uid="+G_USERID+"&callback=?", function(data) {
          TLE.hide_tip();
          var todown = {};
          todown.gdriveid = getCookie("gdriveid") || $("#cok").val();
          todown.tasklist = {};
          $.each(data['Result'], function(n, e) {
            var taskinfo = get_taskinfo(n);
            var filelist = [];
            $.each(e, function(n, e) {
              filelist.push({
                title: e.title,
                f_url: e.url,
                downurl: e.downurl,
                cid: e.cid,
                gcid: e.gcid,
                size: parseInt(e.filesize),
              });
            });
            taskinfo.filelist = filelist;
            todown.tasklist[n] = taskinfo;
          });
          $.each(normal_task_list, function(n, e) {
            var taskinfo = get_taskinfo(e);
            taskinfo['filelist'] = taskinfo;
            todown.tasklist[e] = taskinfo;
          });
          TLE.todown = todown;
          show_exporter_selector();
        });
      } else {
        var todown = {};
        todown.gdriveid = getCookie("gdriveid") || $("#cok").val();
        todown.tasklist = {};
        $.each(normal_task_list, function(n, e) {
          var taskinfo = get_taskinfo(e);
          taskinfo['filelist'] = taskinfo;
          todown.tasklist[e] = taskinfo;
        });
        TLE.todown = todown;
        show_exporter_selector();
      };
    };
    window.batch_down_bt = function() {
      var taskids = [];
      $("span[name=bt_list_ck][checked]").each(function(n, e) {
        var taskid = $(e).attr("value");
        if ($("#btd_status"+taskid).val() == 2)
          taskids.push(taskid);
      });

      TLE.todown = {};
      TLE.todown.gdriveid = getCookie("gdriveid") || $("#cok").val();
      var taskinfo = {
        taskname: $("#bt_info_list .title .w").text(),
        f_url: null,
        cid: null,
        size: null,
        tasktype: 0,
        status: 2,
      }
      var filelist = [];
      $.each(taskids, function(n, e) {
        filelist.push(get_bt_taskinfo(e));
      });
      taskinfo['filelist'] = filelist;
      TLE.todown.tasklist = {};
      TLE.todown.tasklist['0'] = taskinfo;
      show_exporter_selector();
    }
  }

  init();
})(TLE);

var ARIA2 = (function() {
  var jsonrpc_version = '2.0';

  function get_auth(url) {
    return url.match(/^(?:(?![^:@]+:[^:@\/]*@)[^:\/?#.]+:)?(?:\/\/)?(?:([^:@]*(?::[^:@]*)?)?@)?/)[1];
  };

  function request(jsonrpc_path, method, params) {
    var request_obj = {
      jsonrpc: jsonrpc_version,
      method: method,
      id: (new Date()).getTime().toString(),
    };
    if (params) request_obj['params'] = params;

    var xhr = new XMLHttpRequest();
    var auth = get_auth(jsonrpc_path);
    jsonrpc_path = jsonrpc_path.replace(/^((?![^:@]+:[^:@\/]*@)[^:\/?#.]+:)?(\/\/)?(?:(?:[^:@]*(?::[^:@]*)?)?@)?(.*)/, '$1$2$3'); // auth string not allowed in url for firefox
    xhr.open("POST", jsonrpc_path+"?tm="+(new Date()).getTime().toString(), false);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
    if (auth) xhr.setRequestHeader("Authorization", "Basic "+btoa(auth));
    xhr.send(JSON.stringify(request_obj));
  };

  return function(jsonrpc_path) {
    this.jsonrpc_path = jsonrpc_path;
    this.addUri = function (uri, options) {
      request(this.jsonrpc_path, 'aria2.addUri', [[uri, ], options]);
    };
    return this;
  }
})();
}); // end of seajs.use
} // end of wrapper

function onload(func) {
    if (document.readyState === "complete") {
      func();
    } else {
      window.addEventListener('load', func);
    }
}
onload(function(){
  var script = document.createElement('script');
  script.id = "TLE_script";
  if (location.host == "dynamic.cloud.vip.xunlei.com") {
    script.appendChild(document.createTextNode('('+ tle_wrapper +')();'));
  } else if (location.host == "lixian.vip.xunlei.com" || location.host == "jiayuan.xunlei.com") {
    script.appendChild(document.createTextNode('('+ tle_lx3_wrapper +')();'));
  }
  (document.body || document.head || document.documentElement).appendChild(script);
});
