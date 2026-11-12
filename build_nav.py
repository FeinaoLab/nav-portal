# -*- coding: utf-8 -*-
"""把 registry.py 渲染成单文件导航页。"""
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registry import GROUPS
from apps import APPS

HOST = "42.193.158.63"

ACCENTS = {
    "platform": "#2f6fed",
    "rd": "#7c3aed",
    "biz": "#0d9488",
    "ec": "#e11d48",
    "api": "#d97706",
}


def build_apps():
    """手机 APP 区块：应用商店式紧凑卡片，每张卡有「打开」和「安装」。"""
    cards = []
    for a in APPS:
        sub = a["desc"] or a["name"]
        cards.append(
            '''        <div class="appcard" data-app="%(prefix)s">
          <a class="appmain" href="%(landing)s" target="_blank" rel="noopener"
             title="%(name)s · %(landing)s"
             data-name="%(name)s" data-path="%(landing)s" data-desc="%(desc)s" data-code="APP"
             data-group="手机 APP" data-port="-">
            <span class="appicon" style="background:%(theme)s">
              <img src="%(icon)s" alt="" loading="lazy" onerror="this.style.display='none'">
            </span>
            <span class="appbody">
              <span class="appname">%(short)s</span>
              <span class="appdesc">%(sub)s</span>
            </span>
            <span class="dot" data-probe="%(landing)s" title="检测中"></span>
          </a>
          <button class="appinstall" type="button"
                  data-prefix="%(prefix)s" data-name="%(name)s" data-short="%(short)s"
                  data-icon="%(icon)s" data-theme="%(theme)s" data-landing="%(landing)s"
                  title="安装到手机桌面">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
            安装
          </button>
        </div>''' % dict(a, sub=sub)
        )
    return "\n".join(cards)


def build():
    total = sum(len(g["systems"]) for g in GROUPS)
    data = []
    for g in GROUPS:
        for code, name, path, port, desc, tag in g["systems"]:
            data.append({
                "g": g["key"], "code": code, "name": name, "path": path,
                "port": port, "desc": desc, "tag": tag,
            })

    scanned = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 分组导航条
    nav = "\n".join(
        '      <a class="jump" href="#g-%s"><i style="background:%s"></i>%s<span>%d</span></a>'
        % (g["key"], ACCENTS[g["key"]], g["name"], len(g["systems"]))
        for g in GROUPS
    )
    nav = ('      <a class="jump jump-app" href="#g-app"><i></i>手机 APP<span>%d</span></a>\n' % len(APPS)) + nav

    blocks = []
    for g in GROUPS:
        accent = ACCENTS[g["key"]]
        cards = []
        for code, name, path, port, desc, tag in g["systems"]:
            tag_html = '<span class="tag">%s</span>' % tag if tag else ""
            cards.append(
                '''        <a class="card" href="%(path)s" target="_blank" rel="noopener"
           data-name="%(name)s" data-path="%(path)s" data-desc="%(desc)s" data-code="%(code)s"
           data-group="%(group)s" data-port="%(port)s">
          <span class="dot" data-probe="%(path)s" title="检测中"></span>
          <span class="code" style="color:%(accent)s;background:%(accent)s14">%(code)s</span>
          <span class="body">
            <span class="line1"><b>%(name)s</b>%(tag)s</span>
            <span class="desc">%(desc)s</span>
            <span class="meta"><i>%(path)s</i><em>:%(port)s</em></span>
          </span>
        </a>''' % {
                    "path": path, "name": name, "desc": desc, "code": code,
                    "accent": accent, "tag": tag_html, "port": port, "group": g["name"],
                }
            )
        blocks.append(
            '''    <section class="group" id="g-%(key)s">
      <header class="ghead">
        <h2><i style="background:%(accent)s"></i>%(name)s</h2>
        <p>%(desc)s<span class="cnt">%(n)d 个</span></p>
      </header>
      <div class="grid">
%(cards)s
      </div>
    </section>''' % {
                "key": g["key"], "accent": accent, "name": g["name"],
                "desc": g["desc"], "n": len(g["systems"]), "cards": "\n".join(cards),
            }
        )
    apps_block = '''    <section class="group group-app" id="g-app">
      <header class="ghead">
        <h2><i style="background:linear-gradient(180deg,#2f6fed,#7c3aed)"></i>手机 APP</h2>
        <p>每个系统都有一套手机端，装到桌面后点图标直接进，全屏、没有地址栏。<span class="cnt">%(n)d 个</span></p>
      </header>
      <div class="agrid">
%(cards)s
      </div>
      <p class="anote">这些是 PWA 应用，不上应用商店、不下载安装包。点「安装」看对应手机的添加步骤，一般三步完成；装完的图标和原生 APP 一样躺在桌面。</p>
    </section>''' % {"n": len(APPS), "cards": build_apps()}

    html = TEMPLATE.replace("{{TOTAL}}", str(total)) \
                   .replace("{{SCANNED}}", scanned) \
                   .replace("{{HOST}}", HOST) \
                   .replace("{{NAV}}", nav) \
                   .replace("{{APPBLOCK}}", apps_block) \
                   .replace("{{APPCOUNT}}", str(len(APPS))) \
                   .replace("{{BLOCKS}}", "\n\n".join(blocks)) \
                   .replace("{{DATA}}", json.dumps(data, ensure_ascii=False))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)
    print("生成:", out, "| 字节", len(html), "| 系统数", total)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>系统导航 · 全部已部署项目</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%232f6fed'/><path d='M9 22h14M9 16h14M9 10h14' stroke='white' stroke-width='2.6' stroke-linecap='round'/></svg>">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --pri:#2f6fed; --bg:#f4f6fa; --card:#fff; --line:#e3e8f0;
  --ink:#151b26; --ink2:#5a6577; --ink3:#8b95a7;
}
body{
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  background:var(--bg); color:var(--ink); -webkit-font-smoothing:antialiased;
}
a{color:inherit;text-decoration:none}

/* 顶栏 */
header.top{
  background:linear-gradient(135deg,#1c3f8f,#2f6fed 55%,#4f8ef7);
  color:#fff; padding:34px 0 30px;
}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.top h1{font-size:26px;font-weight:650;letter-spacing:.5px;display:flex;align-items:center;gap:11px}
.top h1 svg{flex:none;opacity:.92}
.top .sub{margin-top:9px;font-size:13.5px;color:#c8d8f8}
.top .sub b{color:#fff;font-weight:600}
.stats{display:flex;gap:26px;margin-top:20px;flex-wrap:wrap}
.stat{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.16);border-radius:9px;padding:9px 16px;min-width:96px}
.stat em{display:block;font-size:20px;font-weight:650;font-style:normal;line-height:1.25}
.stat span{font-size:12px;color:#c8d8f8}

/* 工具条 */
.bar{position:sticky;top:0;z-index:20;background:rgba(244,246,250,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.bar .wrap{display:flex;align-items:center;gap:14px;padding-top:11px;padding-bottom:11px;flex-wrap:wrap}
.search{position:relative;flex:1;min-width:220px;max-width:360px}
.search input{
  width:100%;height:36px;border:1px solid var(--line);border-radius:8px;background:#fff;
  padding:0 34px 0 33px;font-size:14px;color:var(--ink);outline:none;transition:.16s;
}
.search input:focus{border-color:var(--pri);box-shadow:0 0 0 3px rgba(47,111,237,.12)}
.search svg{position:absolute;left:10px;top:9px;color:var(--ink3)}
.search kbd{position:absolute;right:9px;top:8px;font:11px/18px ui-monospace,monospace;color:var(--ink3);border:1px solid var(--line);border-radius:4px;padding:0 5px;background:#fafbfd}
.jumps{display:flex;gap:7px;flex-wrap:wrap}
.jump{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink2);background:#fff;border:1px solid var(--line);border-radius:20px;padding:5px 11px 5px 8px;transition:.15s}
.jump:hover{border-color:var(--pri);color:var(--pri)}
.jump i{width:7px;height:7px;border-radius:50%;display:block}
.jump span{color:var(--ink3);font-size:11.5px}
.bar .right{margin-left:auto;display:flex;align-items:center;gap:9px;font-size:12.5px;color:var(--ink3)}
.btn{border:1px solid var(--line);background:#fff;border-radius:7px;height:30px;padding:0 12px;font-size:12.5px;color:var(--ink2);cursor:pointer;transition:.15s}
.btn:hover{border-color:var(--pri);color:var(--pri)}
.btn:disabled{opacity:.55;cursor:default}

/* 分组 */
main{padding:26px 0 60px}
.group{margin-bottom:34px;scroll-margin-top:64px}
.ghead{margin-bottom:13px}
.ghead h2{font-size:16.5px;font-weight:640;display:flex;align-items:center;gap:9px}
.ghead h2 i{width:4px;height:16px;border-radius:2px;display:block}
.ghead p{font-size:13px;color:var(--ink2);margin-top:5px;margin-left:13px}
.ghead .cnt{color:var(--ink3);margin-left:9px;font-size:12.5px}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(292px,1fr));gap:11px}

/* 卡片 */
.card{
  position:relative;display:flex;gap:11px;background:var(--card);border:1px solid var(--line);
  border-radius:10px;padding:13px 14px 12px;transition:border-color .16s,box-shadow .16s,transform .16s;
}
.card:hover{border-color:#c3d3f2;box-shadow:0 4px 16px -6px rgba(21,27,38,.13);transform:translateY(-1px)}
.code{
  flex:none;width:42px;height:42px;border-radius:9px;display:flex;align-items:center;justify-content:center;
  font:600 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.2px;
}
.body{display:flex;flex-direction:column;min-width:0;flex:1}
.line1{display:flex;align-items:center;gap:7px;min-width:0}
.line1 b{font-size:14.5px;font-weight:620;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tag{flex:none;font-size:10.5px;letter-spacing:.3px;color:#2f6fed;background:#eaf1fe;border-radius:4px;padding:1px 5px;font-weight:600}
.desc{font-size:12.5px;color:var(--ink2);margin-top:4px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.meta{display:flex;align-items:center;gap:8px;margin-top:7px;font-size:11.5px;color:var(--ink3)}
.meta i{font-family:ui-monospace,monospace;font-style:normal}

/* 状态点 */
.dot{
  position:absolute;top:12px;right:12px;width:6px;height:6px;border-radius:50%;
  background:#cbd2de;transition:background .2s
}
.dot[data-st=ok]{background:#16a34a;box-shadow:0 0 0 3px rgba(22,163,74,.13)}
.dot[data-st=warn]{background:#f59e0b;box-shadow:0 0 0 3px rgba(245,158,11,.13)}
.dot[data-st=err]{background:#dc2626;box-shadow:0 0 0 3px rgba(220,38,38,.13)}

.empty{padding:60px 0;text-align:center;color:var(--ink3);font-size:14px;display:none}

/* 手机 APP 区 */
.jump-app i{background:linear-gradient(135deg,#2f6fed,#7c3aed)}
.agrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:9px}
.appcard{
  background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;
  display:flex;flex-direction:column;transition:border-color .16s,box-shadow .16s,transform .16s;
}
.appcard:hover{border-color:#c3d3f2;box-shadow:0 4px 16px -6px rgba(21,27,38,.13);transform:translateY(-1px)}
.appmain{position:relative;display:flex;align-items:center;gap:10px;padding:11px 12px 10px;min-width:0}
.appicon{
  flex:none;width:38px;height:38px;border-radius:10px;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 1px 3px rgba(21,27,38,.16);
}
.appicon img{width:100%;height:100%;object-fit:contain;display:block}
.appbody{display:flex;flex-direction:column;min-width:0;flex:1;padding-right:10px}
.appname{font-size:13.5px;font-weight:620;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.appdesc{font-size:11.5px;color:var(--ink3);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.appcard .dot{top:11px;right:11px;width:5px;height:5px}
.appinstall{
  display:flex;align-items:center;justify-content:center;gap:5px;width:100%;
  border:0;border-top:1px solid var(--line);background:#fbfcfe;color:var(--ink2);
  font-size:12px;padding:7px 0 8px;cursor:pointer;transition:.15s;font-family:inherit;
}
.appinstall:hover{background:#eef4ff;color:var(--pri)}
.appinstall svg{flex:none}
.anote{margin-top:11px;font-size:12px;color:var(--ink3);line-height:1.65}

/* 安装引导弹层 */
.mask{
  position:fixed;inset:0;z-index:60;background:rgba(15,23,42,.44);
  display:flex;align-items:center;justify-content:center;padding:20px;
  animation:fade .16s ease-out;
}
.mask[hidden]{display:none}
@keyframes fade{from{opacity:0}to{opacity:1}}
.sheet{
  position:relative;width:100%;max-width:420px;background:#fff;border-radius:14px;
  padding:22px 22px 18px;box-shadow:0 24px 60px -18px rgba(15,23,42,.45);
  animation:pop .18s cubic-bezier(.2,.9,.3,1.1);
}
@keyframes pop{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}
.sheet .x{
  position:absolute;top:12px;right:12px;width:26px;height:26px;border:0;border-radius:50%;
  background:#f1f4f9;color:var(--ink3);font-size:16px;line-height:1;cursor:pointer;
}
.sheet .x:hover{background:#e6ebf4;color:var(--ink)}
.sh-head{display:flex;align-items:center;gap:12px;padding-right:26px}
.sh-icon{flex:none;width:46px;height:46px;border-radius:12px;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(21,27,38,.18)}
.sh-icon img{width:100%;height:100%;object-fit:contain;display:block}
.sh-head b{display:block;font-size:15px;font-weight:640;line-height:1.35}
.sh-head i{display:block;font-size:12px;font-style:normal;color:var(--ink3);margin-top:3px;line-height:1.4}
.tabs{display:flex;gap:6px;margin:16px 0 12px;background:#f1f4f9;padding:3px;border-radius:8px}
.tabs button{
  flex:1;border:0;background:transparent;font-size:12.5px;color:var(--ink2);
  padding:6px 0;border-radius:6px;cursor:pointer;transition:.14s;font-family:inherit;
}
.tabs button[aria-selected=true]{background:#fff;color:var(--pri);font-weight:600;box-shadow:0 1px 3px rgba(21,27,38,.1)}
.steps{list-style:none;counter-reset:s;font-size:13px;color:var(--ink2);line-height:1.65}
.steps li{position:relative;padding-left:26px;margin-bottom:9px}
.steps li::before{
  counter-increment:s;content:counter(s);
  position:absolute;left:0;top:1px;width:18px;height:18px;border-radius:50%;
  background:#eaf1fe;color:var(--pri);font:600 11px/18px ui-monospace,monospace;text-align:center;
}
.steps li b{color:var(--ink);font-weight:620}
.steps li code{font-family:ui-monospace,monospace;background:#f1f4f9;border-radius:4px;padding:1px 4px;font-size:12px}
.sh-warn{
  margin-top:4px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;
  border-radius:8px;padding:9px 11px;font-size:12.5px;line-height:1.55;
}
.sh-warn[hidden]{display:none}
.sh-foot{display:flex;gap:9px;margin-top:16px}
.sh-foot a,.sh-foot button{
  flex:1;height:36px;border-radius:8px;font-size:13px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  font-family:inherit;transition:.15s;text-decoration:none;
}
.sh-open{background:var(--pri);color:#fff;border:1px solid var(--pri)}
.sh-open:hover{background:#2560d0}
.sh-copy{background:#fff;color:var(--ink2);border:1px solid var(--line)}
.sh-copy:hover{border-color:var(--pri);color:var(--pri)}

footer.btm{border-top:1px solid var(--line);padding:20px 0 34px;font-size:12.5px;color:var(--ink3)}
footer.btm .wrap{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
footer.btm code{font-family:ui-monospace,monospace;color:var(--ink2)}

@media (max-width:640px){
  .wrap{padding:0 15px}
  body{overflow-x:hidden}
  .top{padding:26px 0 22px}
  .top h1{font-size:20px;gap:8px}
  .top h1 svg{width:22px;height:22px}
  .top .sub{font-size:12.5px;line-height:1.55;margin-top:8px}
  .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:16px}
  .stat{min-width:0;padding:8px 11px}
  .stat em{font-size:17px}
  .stat span{font-size:11.5px}
  .grid{grid-template-columns:1fr}
  .search{max-width:none;flex:1 1 100%}
  .bar .wrap{gap:9px;padding-top:10px;padding-bottom:10px}
  .bar .right{margin-left:0;width:100%;justify-content:flex-start;gap:10px;flex-wrap:wrap}
  .jumps{width:100%;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;padding-bottom:2px}
  .jumps::-webkit-scrollbar{display:none}
  .jump{flex:0 0 auto;font-size:12px;padding:4px 9px 4px 7px}
  .ghead p{margin-left:13px;font-size:12.5px}
  main{padding:20px 0 44px}
  .group{margin-bottom:26px}
  .agrid{grid-template-columns:repeat(2,1fr);gap:8px}
  .appmain{padding:9px 9px 8px;gap:8px}
  .appicon{width:32px;height:32px;border-radius:8px}
  .appname{font-size:12.5px}
  .appdesc{display:none}
  .appbody{padding-right:8px}
  .appinstall{font-size:11.5px;padding:6px 0 7px}
  .anote{font-size:11.5px;line-height:1.6}
  .mask{padding:0;align-items:flex-end}
  .sheet{max-width:none;border-radius:16px 16px 0 0;padding:20px 16px calc(16px + env(safe-area-inset-bottom))}
}
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <h1>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <rect x="3" y="3" width="7" height="7" rx="1.6"/><rect x="14" y="3" width="7" height="7" rx="1.6"/>
        <rect x="3" y="14" width="7" height="7" rx="1.6"/><rect x="14" y="14" width="7" height="7" rx="1.6"/>
      </svg>
      系统导航
    </h1>
    <div class="sub">云服务器 <b>{{HOST}}</b> 上部署的 <b>{{TOTAL}}</b> 个系统、<b>{{APPCOUNT}}</b> 个手机 APP，一处进入。</div>
    <div class="stats">
      <div class="stat"><em>{{TOTAL}}</em><span>已部署系统</span></div>
      <div class="stat"><em>{{APPCOUNT}}</em><span>手机 APP</span></div>
      <div class="stat"><em id="stOk">—</em><span>当前在线</span></div>
      <div class="stat"><em id="stBad">—</em><span>待确认</span></div>
    </div>
  </div>
</header>

<div class="bar">
  <div class="wrap">
    <div class="search">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/></svg>
      <input id="q" type="search" placeholder="搜索名称、路径或用途" autocomplete="off">
      <kbd>/</kbd>
    </div>
    <div class="jumps">
{{NAV}}
    </div>
    <div class="right">
      <span id="probeTip">状态检测中…</span>
      <button class="btn" id="reprobe">重新检测</button>
    </div>
  </div>
</div>

<main>
  <div class="wrap">
{{APPBLOCK}}
{{BLOCKS}}
    <div class="empty" id="empty">没有匹配的系统，换个关键词试试。</div>
  </div>
</main>

<footer class="btm">
  <div class="wrap">
    <span>登记时间 {{SCANNED}} · 新增系统后重跑 <code>build_nav.py</code> 刷新本页</span>
    <span>绿点在线 · 黄点需登录或非 200 · 红点无响应</span>
  </div>
</footer>

<div class="mask" id="mask" hidden>
  <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="shName">
    <button class="x" id="shX" type="button" aria-label="关闭">×</button>
    <div class="sh-head">
      <span class="sh-icon" id="shIcon"></span>
      <span>
        <b id="shName">应用名称</b>
        <i>添加到主屏幕后从桌面图标直接进，全屏、没有地址栏</i>
      </span>
    </div>
    <div class="tabs" id="shTabs" role="tablist">
      <button type="button" data-os="android" role="tab">安卓</button>
      <button type="button" data-os="ios" role="tab">iPhone / iPad</button>
      <button type="button" data-os="pc" role="tab">电脑</button>
    </div>
    <ol class="steps" id="shSteps"></ol>
    <div class="sh-warn" id="shWarn" hidden>
      你在微信里打开这个页面，微信内不支持添加到桌面。点右上角「···」→「在浏览器打开」，再回来装。
    </div>
    <div class="sh-foot">
      <a class="sh-open" id="shOpen" href="#" target="_blank" rel="noopener">直接打开</a>
      <button class="sh-copy" id="shCopy" type="button">复制链接</button>
    </div>
  </div>
</div>

<script>
(function () {
  var DATA = {{DATA}};

  /* ---- 搜索 ---- */
  var q = document.getElementById('q');
  var items = [].slice.call(document.querySelectorAll('.card, .appmain'));
  var groups = [].slice.call(document.querySelectorAll('.group'));
  var empty = document.getElementById('empty');

  function filter() {
    var kw = q.value.trim().toLowerCase();
    var hit = 0;
    items.forEach(function (el) {
      var d = el.dataset;
      var hay = (d.name + ' ' + d.path + ' ' + d.desc + ' ' + d.code + ' ' + d.port + ' ' + (d.group || '')).toLowerCase();
      var on = !kw || hay.indexOf(kw) > -1;
      var box = (el.closest && el.closest('.appcard')) || el;
      box.style.display = on ? '' : 'none';
      if (on) hit++;
    });
    groups.forEach(function (g) {
      var n = g.querySelectorAll('.card:not([style*="none"]), .appcard:not([style*="none"])').length;
      g.style.display = n ? '' : 'none';
    });
    empty.style.display = hit ? 'none' : 'block';
  }
  q.addEventListener('input', filter);
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if (e.key === 'Escape' && document.activeElement === q) { q.value = ''; filter(); q.blur(); }
  });

  /* ---- 状态探活（同源，限并发 6） ---- */
  var dots = [].slice.call(document.querySelectorAll('.dot'));
  var tip = document.getElementById('probeTip');
  var btn = document.getElementById('reprobe');
  var stOk = document.getElementById('stOk');
  var stBad = document.getElementById('stBad');

  function probeOne(dot) {
    var path = dot.dataset.probe;
    var done = false;
    var ac = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ac) ac.abort(); }, 6000);
    function finish(st) {
      if (done) return;
      done = true;
      clearTimeout(timer);
      dot.dataset.st = st;
      dot.title = st === 'ok' ? '在线' : (st === 'warn' ? '有响应但非 200（可能需登录）' : '无响应');
      tally();
    }
    fetch(path, { method: 'GET', cache: 'no-store', credentials: 'omit', signal: ac ? ac.signal : undefined })
      .then(function (r) { finish(r.ok ? 'ok' : (r.status < 500 ? 'warn' : 'err')); })
      .catch(function () { finish('err'); });
  }

  var counted = 0, nOk = 0, nBad = 0;
  function tally(reset) {
    if (reset) { counted = 0; nOk = 0; nBad = 0; }
    counted++;
    var st = dots.filter(function (d) { return d.dataset.st; });
    nOk = st.filter(function (d) { return d.dataset.st === 'ok'; }).length;
    nBad = st.length - nOk;
    stOk.textContent = nOk;
    stBad.textContent = nBad;
    tip.textContent = st.length + ' / ' + dots.length + ' 已检测';
  }

  function runProbe() {
    btn.disabled = true;
    dots.forEach(function (d) { delete d.dataset.st; d.title = '检测中'; });
    stOk.textContent = '—'; stBad.textContent = '—';
    tip.textContent = '状态检测中…';
    counted = 0; nOk = 0; nBad = 0;

    var i = 0, running = 0, MAX = 6;
    function next() {
      while (running < MAX && i < dots.length) {
        running++;
        (function (dot) {
          probeOne(dot);
          setTimeout(function () { running--; next(); }, 40);
        })(dots[i++]);
      }
      if (i >= dots.length && running === 0) {
        btn.disabled = false;
        tip.textContent = dots.length + ' 个已检测';
      }
    }
    next();
  }

  btn.addEventListener('click', runProbe);
  runProbe();

  /* ---- 手机 APP 安装引导 ---- */
  var UA = navigator.userAgent;
  var inWx = /MicroMessenger/i.test(UA);
  var OS_STEPS = {
    android: [
      '用手机上的 Chrome 或 Edge 打开下面的链接，进入 <b>%N%</b>',
      '点浏览器右上角 <b>⋮</b>，选「安装应用」或「添加到主屏幕」',
      '确认后桌面出现图标，以后点图标直接进，全屏、没有地址栏'
    ],
    ios: [
      '用 <b>Safari</b> 打开下面的链接（微信、QQ 的内置浏览器装不了）',
      '点屏幕底部中间的 <b>分享</b> 按钮，往下找「添加到主屏幕」',
      '点右上角「添加」，桌面就出现图标了'
    ],
    pc: [
      '用 Chrome 或 Edge 打开下面的链接，进入 <b>%N%</b>',
      '地址栏右侧会出现 <b>安装</b> 图标，点它；或者菜单 → 应用 → 安装此站点',
      '装完从开始菜单或桌面启动，独立窗口运行，不占浏览器标签'
    ]
  };

  var mask = document.getElementById('mask');
  var shIcon = document.getElementById('shIcon');
  var shName = document.getElementById('shName');
  var shSteps = document.getElementById('shSteps');
  var shOpen = document.getElementById('shOpen');
  var shWarn = document.getElementById('shWarn');
  var shCopy = document.getElementById('shCopy');
  var osTab = 'android';
  var curShort = '';
  var curUrl = '';

  function guessOS() {
    if (/iPad|iPhone|iPod/.test(UA) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)) return 'ios';
    if (/Android/i.test(UA)) return 'android';
    return 'pc';
  }

  function renderSteps() {
    [].slice.call(document.querySelectorAll('#shTabs button')).forEach(function (b) {
      b.setAttribute('aria-selected', b.dataset.os === osTab ? 'true' : 'false');
    });
    shSteps.innerHTML = OS_STEPS[osTab].map(function (t) {
      return '<li>' + t.replace(/%N%/g, '<b>' + curShort + '</b>') + '</li>';
    }).join('');
  }

  function openSheet(btn) {
    var d = btn.dataset;
    curShort = d.short;
    curUrl = d.landing;
    shIcon.innerHTML = '<img src="' + d.icon + '" alt="" onerror="this.style.display=\'none\'">';
    shIcon.style.background = d.theme;
    shName.textContent = d.name;
    shOpen.href = d.landing;
    shWarn.hidden = !inWx;
    osTab = guessOS();
    renderSteps();
    mask.hidden = false;
    document.body.style.overflow = 'hidden';
  }

  function closeSheet() {
    mask.hidden = true;
    document.body.style.overflow = '';
  }

  [].slice.call(document.querySelectorAll('.appinstall')).forEach(function (b) {
    b.addEventListener('click', function (e) { e.preventDefault(); openSheet(b); });
  });
  [].slice.call(document.querySelectorAll('#shTabs button')).forEach(function (b) {
    b.addEventListener('click', function () { osTab = b.dataset.os; renderSteps(); });
  });
  document.getElementById('shX').addEventListener('click', closeSheet);
  mask.addEventListener('click', function (e) { if (e.target === mask) closeSheet(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !mask.hidden) closeSheet(); });

  function flash(msg) {
    var old = shCopy.textContent;
    shCopy.textContent = msg;
    setTimeout(function () { shCopy.textContent = old; }, 1500);
  }
  function fallbackCopy(t) {
    var ta = document.createElement('textarea');
    ta.value = t;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); flash('已复制'); } catch (err) { flash('复制失败，手动选吧'); }
    document.body.removeChild(ta);
  }
  shCopy.addEventListener('click', function () {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(curUrl).then(function () { flash('已复制'); }, function () { fallbackCopy(curUrl); });
    } else {
      fallbackCopy(curUrl);
    }
  });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
