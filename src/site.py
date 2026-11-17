"""本地 / 公网「个人日报网站」生成器。

把 output/ 下的 Markdown 文章渲染成一个可浏览、可搜索、可分类、可收藏的静态网站：
- docs/index.html              首页（Hero 横幅 + 标签云 + 搜索高亮 + 收藏/已读 + 随机一篇 + 深色模式）
- docs/articles/日期/xxx.html  每篇文章独立页面（目录 TOC + 阅读进度 + 字号调节 + 收藏 + 分享 + 上下篇 + 键盘翻页）
- docs/feed.xml                RSS 订阅源
- docs/assets/                 图片等静态资源
"""
import html as _html
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

CSS = """
:root{
  --bg:#f5f6f8;--card:#ffffff;--text:#1f2328;--muted:#6b7280;
  --accent:#0a7d3f;--accent2:#1f6feb;--border:#e5e7eb;
  --header:#0d1117;--headerfg:#ffffff;--headersub:#9aa4b2;
  --chip:#eef0f3;--chipfg:#374151;--chipactive:#0a7d3f;--chipactivefg:#ffffff;
  --quote:#f0f9f4;--codebg:#f0f0f0;--codefg:#c7254e;--fs:16px;
}
[data-theme="dark"]{
  --bg:#0d1117;--card:#161b22;--text:#e6edf3;--muted:#8b949e;
  --accent:#3fb950;--accent2:#58a6ff;--border:#30363d;
  --header:#010409;--headerfg:#ffffff;--headersub:#8b949e;
  --chip:#21262d;--chipfg:#c9d1d9;--chipactive:#238636;--chipactivefg:#ffffff;
  --quote:#12261a;--codebg:#21262d;--codefg:#ff7b72;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.7;}
a{color:var(--accent);text-decoration:none;}
.header{background:var(--header);color:var(--headerfg);padding:12px 20px;position:sticky;top:0;z-index:20;box-shadow:0 1px 8px rgba(0,0,0,.18);}
.header-inner{max-width:880px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
.brand{color:#fff;font-weight:700;font-size:15px;}
.hbtns{display:flex;align-items:center;gap:8px;}
.rsslink{color:#9aa4b2;font-size:13px;border:1px solid rgba(255,255,255,.22);border-radius:8px;padding:5px 10px;}
.rsslink:hover{color:#fff;background:rgba(255,255,255,.1);}
.themebtn{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.22);color:#fff;padding:6px 12px;border-radius:8px;cursor:pointer;font-size:13px;white-space:nowrap;}
.themebtn:hover{background:rgba(255,255,255,.16);}
.hero{position:relative;background:#0a1419 url('assets/hero.jpg') center/cover;color:#fff;padding:44px 20px 42px;}
.hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,12,16,.62),rgba(4,12,16,.82));}
.hero-inner{position:relative;max-width:880px;margin:0 auto;}
.hero h1{font-size:27px;margin:0 0 8px;font-weight:800;letter-spacing:.5px;}
.hero p{color:#c9d6dd;font-size:14px;margin:0 0 16px;max-width:640px;}
.hstats{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;}
.hstat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:8px;padding:5px 12px;font-size:12.5px;color:#e6edf3;backdrop-filter:blur(4px);}
.hstat b{color:#fff;font-size:14px;}
.randbtn{display:inline-block;background:linear-gradient(135deg,#1f6feb,#00c2a8);color:#fff;border:none;border-radius:10px;padding:9px 16px;font-size:14px;cursor:pointer;font-weight:600;box-shadow:0 6px 16px rgba(31,111,235,.35);}
.randbtn:hover{filter:brightness(1.08);}
.wrap{max-width:880px;margin:0 auto;padding:18px 16px 70px;}
.search{width:100%;padding:11px 14px;font-size:15px;border:1px solid var(--border);border-radius:10px;margin-bottom:10px;outline:none;background:var(--card);color:var(--text);}
.search:focus{border-color:var(--accent2);}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;}
.chip{background:var(--chip);color:var(--chipfg);border:1px solid transparent;border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer;}
.chip:hover{border-color:var(--accent);}
.chip.active{background:var(--chipactive);color:var(--chipactivefg);}
.chip em{font-style:normal;opacity:.65;font-size:11px;margin-left:3px;}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;}
.toggle{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:5px 11px;font-size:12.5px;cursor:pointer;}
.toggle:hover{border-color:var(--accent);color:var(--text);}
.toggle.active{background:var(--accent);border-color:var(--accent);color:#fff;}
.date{font-size:14px;font-weight:700;color:var(--text);margin:22px 0 10px;padding-left:10px;border-left:4px solid var(--accent);}
.item{display:flex;align-items:flex-start;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:10px;color:inherit;cursor:pointer;transition:border-color .15s,box-shadow .15s,opacity .15s;}
.item:hover{border-color:var(--accent);box-shadow:0 4px 14px rgba(0,0,0,.06);}
.cover{flex:none;width:46px;height:46px;border-radius:10px;margin-right:12px;}
.item .body{flex:1;min-width:0;}
.item .t{font-size:16px;font-weight:600;margin-bottom:5px;}
.item .s{font-size:13.5px;color:var(--muted);margin-bottom:9px;}
.item .meta{display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:12px;color:var(--muted);margin-bottom:8px;}
.badge{background:var(--accent);color:#fff;padding:1px 8px;border-radius:6px;font-size:11px;}
.tags{display:flex;flex-wrap:wrap;gap:6px;}
.tag{background:var(--chip);color:var(--chipfg);padding:1px 8px;border-radius:6px;font-size:11px;}
.star{color:var(--muted);cursor:pointer;font-size:16px;line-height:1;margin-left:auto;user-select:none;padding:4px 7px;border-radius:6px;}
.star:hover{color:#f5a623;background:var(--chip);}
.star.on{color:#f5a623;}
.srclink{color:var(--accent2);font-size:12px;white-space:nowrap;}
.srclink:hover{text-decoration:underline;}
.readmark{display:none;color:var(--muted);font-size:11px;border:1px solid var(--border);border-radius:6px;padding:0 6px;}
.read .readmark{display:inline-block;}
.read{opacity:.5;}
.read:hover{opacity:.85;}
mark{background:#fde047;color:#111;padding:0 2px;border-radius:3px;}
.empty{color:var(--muted);text-align:center;padding:44px 0;}
.footer{max-width:880px;margin:0 auto;padding:0 16px 30px;color:var(--muted);font-size:12px;text-align:center;}
.footer a{color:var(--muted);text-decoration:underline;}
.topbtn{position:fixed;right:18px;bottom:22px;width:42px;height:42px;border-radius:50%;border:1px solid var(--border);background:var(--card);color:var(--text);cursor:pointer;font-size:18px;box-shadow:0 4px 12px rgba(0,0,0,.18);display:none;z-index:30;}
.progressbar{position:fixed;top:0;left:0;height:3px;background:var(--accent);width:0;z-index:50;}
article{max-width:1180px;margin:0 auto;padding:0;font-size:var(--fs,16px);}
.article-layout{display:flex;gap:22px;align-items:flex-start;padding:20px 16px 56px;}
.article-main{flex:1;min-width:0;}
.tocside{flex:none;width:260px;display:none;}
.toc-mobile{display:block;}
.tocside .toc{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:12px 14px;margin:0;}
.toctitle{font-weight:600;font-size:14px;margin-bottom:8px;}
@media(min-width:1120px){.toc-mobile{display:none;}.tocside{display:block;position:sticky;top:70px;max-height:calc(100vh - 88px);overflow:auto;}}
article .card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:26px 24px;}
article h1{font-size:1.6em;line-height:1.4;margin:0 0 8px;}
article .meta{display:flex;flex-wrap:wrap;align-items:center;gap:10px;color:var(--muted);font-size:13px;margin-bottom:12px;padding-bottom:14px;border-bottom:1px solid var(--border);}
article .tags{margin-bottom:4px;}
.tools{margin-left:auto;display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
.favbtn,.fsbtn,.copybtn{background:var(--chip);color:var(--chipfg);border:1px solid var(--border);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;}
.favbtn.on{color:#f5a623;border-color:#f5a623;}
.toc{background:var(--quote);border:1px solid var(--border);border-radius:10px;padding:10px 14px;margin:0 0 18px;}
.toc summary{cursor:pointer;font-weight:600;color:var(--text);}
.toc ul{margin:8px 0 0;padding-left:18px;}
.toc li{margin:4px 0;font-size:14px;}
.toc li.l3{margin-left:14px;font-size:13px;color:var(--muted);}
.toc a{color:var(--accent2);}
article h2{font-size:1.25em;margin:26px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border);scroll-margin-top:70px;}
article h3{font-size:1.05em;margin:20px 0 8px;scroll-margin-top:70px;}
article p{margin:0 0 14px;}
article ul,article ol{margin:0 0 14px;padding-left:22px;}
article li{margin:6px 0;}
article blockquote{border-left:3px solid var(--accent);background:var(--quote);margin:0 0 14px;padding:10px 14px;color:var(--muted);border-radius:0 8px 8px 0;}
article pre{background:#0d1117;color:#e6edf3;padding:14px;border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.6;}
article code{font-family:Consolas,Monaco,monospace;font-size:0.92em;}
article :not(pre)>code{background:var(--codebg);color:var(--codefg);padding:1px 6px;border-radius:4px;}
article hr{border:none;border-top:1px solid var(--border);margin:24px 0;}
.pagenav{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 0;}
.navlink{flex:1 1 200px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 14px;color:var(--text);font-size:13px;line-height:1.45;}
.navlink:hover{border-color:var(--accent);}
.navlink span{color:var(--muted);font-size:12px;}
.navlink.next{text-align:right;}
.archpanel{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:14px;padding:10px 14px;}
.archpanel summary{cursor:pointer;font-weight:600;font-size:14px;color:var(--text);}
.archlist{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
.architem{background:var(--chip);color:var(--chipfg);border:1px solid transparent;border-radius:8px;padding:4px 10px;font-size:12.5px;cursor:pointer;}
.architem:hover{border-color:var(--accent);}
.architem em{font-style:normal;opacity:.6;margin-left:3px;font-size:11px;}
.helpwrap{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;display:none;align-items:center;justify-content:center;padding:20px;}
.helpwrap.show{display:flex;}
.helpcard{background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:14px;max-width:440px;width:100%;padding:20px 22px;}
.helpcard h3{margin:0 0 12px;font-size:16px;}
.helpline{display:flex;justify-content:space-between;gap:12px;font-size:13px;margin:7px 0;}
.helpline>span:last-child{color:var(--muted);}
.kbd{background:var(--chip);border:1px solid var(--border);border-bottom-width:2px;border-radius:5px;padding:1px 7px;font-size:12px;font-family:Consolas,Monaco,monospace;}
.helpclose{display:block;margin:16px auto 0;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:7px 18px;cursor:pointer;font-size:13px;}
.related{margin:18px 0 0;}
.related h3{font-size:15px;margin:0 0 10px;}
.relcard{display:block;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px;margin-bottom:8px;color:var(--text);font-size:14px;}
.relcard:hover{border-color:var(--accent);}
.relcard .rm{color:var(--muted);font-size:12px;margin-left:8px;}
.toc a.active{color:var(--accent);font-weight:700;}
.codewrap{position:relative;margin:0 0 14px;}
.codewrap pre{margin:0;}
.copycode{position:absolute;top:8px;right:8px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);color:#c9d1d9;border-radius:6px;padding:3px 9px;font-size:12px;cursor:pointer;}
.copycode:hover{background:rgba(255,255,255,.2);}
.continue{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px 16px;margin-bottom:14px;}
.cthead{font-size:12px;color:var(--muted);margin-bottom:6px;}
.clink{font-size:15px;font-weight:600;color:var(--accent2);display:block;margin-bottom:6px;}
.clink:hover{text-decoration:underline;}
.crecent{font-size:12px;color:var(--muted);margin-top:6px;}
.cmini{display:inline-block;margin:0 10px 4px 0;color:var(--muted);}
.cmini:hover{color:var(--accent);text-decoration:underline;}
[data-reader="on"] .header,[data-reader="on"] .footer,[data-reader="on"] .tocside,[data-reader="on"] .toc-mobile,[data-reader="on"] .related{display:none!important;}
[data-reader="on"] .article-layout{padding-top:8px;}
[data-reader="on"] .article-main{margin:0 auto;max-width:760px;}
[data-reader="on"] article .card{border:none;background:transparent;padding:10px 0;}
[data-font="serif"] article{font-family:Georgia,"Songti SC","STSong","SimSun",serif;}
.reader-exit{position:fixed;top:14px;right:14px;z-index:60;display:none;background:var(--card);color:var(--text);border:1px solid var(--border);border-radius:999px;padding:6px 14px;cursor:pointer;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,.2);}
[data-reader="on"] .reader-exit{display:block;}
@media print{
  .header,.hero,.search,.chips,.filters,.tools,.pagenav,.progressbar,.topbtn,.footer,.toc,.tocside,.toc-mobile,.helpwrap,.related,.archpanel,.copycode,.continue,.reader-exit{display:none!important;}
  .article-layout{display:block;padding:0;}
  body{background:#fff;color:#000;}
  article .card{border:none;padding:0;}
  a{color:#000;}
}
"""

FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230a7d3f'/%3E%3Cpath d='M12 38l10-10 8 8 14-14 8 8' stroke='%23ffffff' stroke-width='5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E"

TAG_ORDER = ["生物医学", "嵌入式", "AI/大模型", "通信/信号", "3D打印", "开源工具"]

TAG_RULES = {
    "生物医学": ["生物医学", "医学", "医疗", "脑电", "睡眠", "健康", "论文", "文献", "术语",
                 "biomed", "medical", "eeg", "ecg", "mri", "医生", "疾病", "临床", "药"],
    "嵌入式": ["stm32", "esp32", "arduino", "单片机", "mcu", "嵌入式", "固件", "机器人",
               "反作用轮", "独轮", "板", "传感器", "gpio", "rtos", "firmware", "arm"],
    "AI/大模型": ["ai", "大模型", "模型", "算法", "深度学习", "llm", "神经网络", "transformer", "智能"],
    "通信/信号": ["雷达", "太赫兹", "通信", "频谱", "信号", "接收机", "6g", "电磁", "无线", "指纹识别"],
    "3D打印": ["3d打印", "3d 打印", "增材制造", "打印", "3d printing", "fdm", "sla"],
    "开源工具": ["github", "开源", "工具", "项目", "库", "lib", "mcp", "固件"],
}

TAG_COLORS = {
    "生物医学": "linear-gradient(135deg,#0a7d3f,#34d399)",
    "嵌入式": "linear-gradient(135deg,#1f6feb,#22d3ee)",
    "AI/大模型": "linear-gradient(135deg,#7c3aed,#60a5fa)",
    "通信/信号": "linear-gradient(135deg,#ea580c,#fbbf24)",
    "3D打印": "linear-gradient(135deg,#db2777,#fb7185)",
    "开源工具": "linear-gradient(135deg,#475569,#94a3b8)",
    "综合": "linear-gradient(135deg,#0ea5e9,#34d399)",
}

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{__FAVICON__}">
<title>{__TITLE__} · {__SITE__}</title>
{__HEAD__}
<style>{__CSS__}</style>
</head>
<body data-url="{__URL__}" data-title="{__TITLE_ATTR__}" data-src="{__SRC__}">
<button class="reader-exit" type="button" id="readerExit">✕ 退出阅读</button>
<div class="progressbar" id="bar"></div>
<div class="header"><div class="header-inner">
<a href="../../index.html" style="color:#fff;font-weight:600;">← 返回目录</a>
<div class="hbtns"><button class="themebtn" type="button" id="fontBtn">字体：无衬线</button><button class="themebtn" type="button" id="readerBtn">阅读模式</button><button class="themebtn" type="button" id="themeBtn">深色模式</button></div>
</div></div>
<article>
<div class="article-layout">
<div class="article-main">
<div class="card">
<h1>{__TITLE__}</h1>
<div class="meta">{__META__}</div>
<div class="tags">{__TAGS__}</div>
{__TOCMOBILE__}
{__BODY__}
</div>
{__NAV__}
{__RELATED__}
</div>
{__TOCSIDE__}
</div>
</article>
<button class="topbtn" id="topBtn" title="回到顶部">↑</button>
<div class="footer">由 AI 自动生成 · 仅供学习参考 · 快捷键 ←/→ 或 j/k 上下篇 · f 收藏 · m 已读 · o 原文</div>
<script>
(function(){
  function setTheme(d){ if(d) document.documentElement.setAttribute('data-theme','dark'); else document.documentElement.removeAttribute('data-theme'); }
  try{ var saved=localStorage.getItem('theme'); if(saved==='dark'){ setTheme(true); } else if(saved==='light'){ setTheme(false); } else if(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches){ setTheme(true); } }catch(e){}
  var tb=document.getElementById('themeBtn');
  function syncTheme(){ var d=document.documentElement.getAttribute('data-theme')==='dark'; if(tb) tb.textContent=d?'浅色模式':'深色模式'; }
  if(tb) tb.addEventListener('click',function(){
    var d=document.documentElement.getAttribute('data-theme')==='dark';
    setTheme(!d); try{localStorage.setItem('theme', d?'light':'dark');}catch(e){}
    syncTheme();
  });
  syncTheme();

  function applyReader(){ var on=document.documentElement.getAttribute('data-reader')==='on'; var b=document.getElementById('readerBtn'); if(b) b.textContent=on?'退出阅读':'阅读模式'; }
  try{ if(localStorage.getItem('reader')==='on') document.documentElement.setAttribute('data-reader','on'); }catch(e){}
  var rb=document.getElementById('readerBtn');
  rb.addEventListener('click',function(){ var on=document.documentElement.getAttribute('data-reader')==='on'; if(on) document.documentElement.removeAttribute('data-reader'); else document.documentElement.setAttribute('data-reader','on'); try{localStorage.setItem('reader', on?'off':'on');}catch(e){} applyReader(); });
  var re=document.getElementById('readerExit');
  re.addEventListener('click',function(){ document.documentElement.removeAttribute('data-reader'); try{localStorage.setItem('reader','off');}catch(e){} applyReader(); });
  applyReader();

  function applyFont(){ var s=document.documentElement.getAttribute('data-font')==='serif'; var b=document.getElementById('fontBtn'); if(b) b.textContent=s?'字体：衬线':'字体：无衬线'; }
  try{ if(localStorage.getItem('font')==='serif') document.documentElement.setAttribute('data-font','serif'); }catch(e){}
  var fbtn=document.getElementById('fontBtn');
  fbtn.addEventListener('click',function(){ var s=document.documentElement.getAttribute('data-font')==='serif'; if(s) document.documentElement.removeAttribute('data-font'); else document.documentElement.setAttribute('data-font','serif'); try{localStorage.setItem('font', s?'sans':'serif');}catch(e){} applyFont(); });
  applyFont();

  function loadSet(k){ try{ var v=localStorage.getItem(k); return v?JSON.parse(v):[]; }catch(e){ return []; } }
  function saveSet(k,a){ try{ localStorage.setItem(k,JSON.stringify(a)); }catch(e){} }
  function has(a,x){ return a.indexOf(x)>=0; }

  var favBtn=document.getElementById('favBtn');
  var key=favBtn.getAttribute('data-key');
  var favs=loadSet('favs'); var reads=loadSet('read');
  if(!has(reads,key)){ reads.push(key); saveSet('read',reads); }
  function syncFav(){ var on=has(favs,key); favBtn.textContent=on?'★ 已收藏':'☆ 收藏'; favBtn.classList.toggle('on',on); }
  favBtn.addEventListener('click',function(){
    var i=favs.indexOf(key); if(i>=0) favs.splice(i,1); else favs.push(key);
    saveSet('favs',favs); syncFav();
  });
  syncFav();

  var fs=16; try{ var sv=localStorage.getItem('fs'); if(sv) fs=parseInt(sv)||16; }catch(e){}
  function applyFs(){ document.documentElement.style.setProperty('--fs',fs+'px'); try{localStorage.setItem('fs',fs);}catch(e){} }
  applyFs();
  document.getElementById('inc').addEventListener('click',function(){ fs=Math.min(22,fs+1); applyFs(); });
  document.getElementById('dec').addEventListener('click',function(){ fs=Math.max(13,fs-1); applyFs(); });

  var selfTitle=document.body.getAttribute('data-title');
  var selfUrl=document.body.getAttribute('data-url');
  var hist=loadSet('hist');
  hist=hist.filter(function(x){ return x && x.t!==selfTitle; });
  hist.unshift({t:selfTitle,u:selfUrl});
  if(hist.length>20) hist=hist.slice(0,20);
  saveSet('hist',hist);
  try{ var pos=JSON.parse(localStorage.getItem('pos')||'{}'); if(pos[selfTitle]){ var he=document.documentElement; var ob=he.style.scrollBehavior; he.style.scrollBehavior='auto'; window.scrollTo(0,pos[selfTitle]); he.style.scrollBehavior=ob; } }catch(e){}
  var posTimer;
  window.addEventListener('scroll',function(){
    clearTimeout(posTimer);
    posTimer=setTimeout(function(){
      try{ var p=JSON.parse(localStorage.getItem('pos')||'{}'); p[selfTitle]=window.scrollY; localStorage.setItem('pos',JSON.stringify(p)); }catch(e){}
    },300);
  });

  var bar=document.getElementById('bar');
  function onScroll(){ var h=document.documentElement; var m=h.scrollHeight-h.clientHeight; bar.style.width=(m>0?(h.scrollTop/m*100):0)+'%'; }
  window.addEventListener('scroll',onScroll); onScroll();

  var topBtn=document.getElementById('topBtn');
  window.addEventListener('scroll',function(){ topBtn.style.display=(window.scrollY>400)?'block':'none'; });
  topBtn.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });

  var tocLinks=[].slice.call(document.querySelectorAll('.toc a'));
  if(tocLinks.length){
    var heads=[].slice.call(document.querySelectorAll('article h2[id], article h3[id]'));
    function spy(){
      var y=window.scrollY+90, cur=null;
      heads.forEach(function(h){ if(h.offsetTop<=y) cur=h.id; });
      tocLinks.forEach(function(a){ a.classList.toggle('active', a.getAttribute('href')==='#'+cur); });
    }
    window.addEventListener('scroll',spy); spy();
  }

  function copyText(t, done){
    function fallback(){ var x=document.createElement('textarea'); x.value=t; document.body.appendChild(x); x.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(x); }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(t).then(done,function(){ fallback(); done(); }); } else { fallback(); done(); }
  }
  var cb=document.getElementById('copyBtn');
  cb.addEventListener('click',function(){
    var done=function(){ cb.textContent='已复制'; setTimeout(function(){ cb.textContent='复制链接'; },1500); };
    copyText(location.href, done);
  });

  document.querySelectorAll('article pre').forEach(function(pre){
    var wrap=document.createElement('div'); wrap.className='codewrap';
    pre.parentNode.insertBefore(wrap,pre); wrap.appendChild(pre);
    var btn=document.createElement('button'); btn.type='button'; btn.className='copycode'; btn.textContent='复制';
    btn.addEventListener('click',function(){
      copyText(pre.innerText, function(){ btn.textContent='已复制'; setTimeout(function(){ btn.textContent='复制'; },1500); });
    });
    wrap.appendChild(btn);
  });

  function goPrev(){ var p=document.querySelector('.navlink.prev'); if(p) location.href=p.getAttribute('href'); }
  function goNext(){ var n=document.querySelector('.navlink.next'); if(n) location.href=n.getAttribute('href'); }
  document.addEventListener('keydown',function(ev){
    if(ev.target && (ev.target.tagName==='INPUT'||ev.target.tagName==='TEXTAREA')) return;
    var k=ev.key;
    if(k==='Escape'){ if(document.documentElement.getAttribute('data-reader')==='on'){ document.documentElement.removeAttribute('data-reader'); try{localStorage.setItem('reader','off');}catch(e){} applyReader(); } }
    else if(k==='ArrowLeft'||k==='k'){ goPrev(); }
    else if(k==='ArrowRight'||k==='j'){ goNext(); }
    else if(k==='f'){ favBtn.click(); }
    else if(k==='m'){ var i=reads.indexOf(key); if(i>=0) reads.splice(i,1); else reads.push(key); saveSet('read',reads); }
    else if(k==='o'){ var s=document.body.getAttribute('data-src'); if(s) window.open(s,'_blank'); }
  });
})();
</script>
</body>
</html>"""

INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="{__FAVICON__}">
<title>{__TITLE__}</title>
{__HEAD__}
<style>{__CSS__}</style>
</head>
<body>
<div class="header"><div class="header-inner">
<a class="brand" href="index.html">{__TITLE__}</a>
<div class="hbtns"><a class="rsslink" href="feed.xml">RSS 订阅</a><button class="themebtn" type="button" id="themeBtn">深色模式</button><button class="themebtn" type="button" id="helpBtn" title="快捷键">?</button></div>
</div></div>
<div class="hero"><div class="hero-inner">
<h1>{__TITLE__}</h1>
<p>{__SUBTITLE__}</p>
<div class="hstats">{__HSTATS__}</div>
<button class="randbtn" type="button" id="randBtn">随机读一篇 →</button>
</div></div>
<div class="wrap">
{__ARCHIVE__}
<input class="search" id="q" placeholder="搜索标题 / 关键词 / 正文（按 / 聚焦）">
<div class="chips">{__CHIPS__}</div>
<div class="filters">
<button class="toggle" type="button" id="favOnlyBtn">☆ 只看收藏</button>
<button class="toggle" type="button" id="unreadOnlyBtn">只看未读</button>
<button class="toggle" type="button" id="sortBtn">排序：最新在前</button>
<button class="toggle" type="button" id="resetBtn">重置</button>
</div>
<div id="continueBox"></div>
<div id="list">{__BODY__}</div>
<div class="empty" id="empty" style="display:none;">没有匹配的内容</div>
</div>
<button class="topbtn" id="topBtn" title="回到顶部">↑</button>
<div class="footer">每天自动更新 · <a href="feed.xml">RSS 订阅</a> · 快捷键：/ 搜索 · F 收藏 · U 未读 · A 全部 · R 随机 · D 主题 · ? 帮助</div>
<div class="helpwrap" id="helpWrap">
<div class="helpcard">
<h3>快捷键 & 使用说明</h3>
<div class="helpline"><span><span class="kbd">/</span> 或 <span class="kbd">Ctrl+K</span></span><span>聚焦搜索（含正文）</span></div>
<div class="helpline"><span><span class="kbd">F</span> 收藏 / <span class="kbd">U</span> 未读 / <span class="kbd">A</span> 全部</span><span>快速筛选</span></div>
<div class="helpline"><span><span class="kbd">R</span> 随机</span><span>随机读一篇</span></div>
<div class="helpline"><span><span class="kbd">D</span> 主题</span><span>切换深色 / 浅色</span></div>
<div class="helpline"><span><span class="kbd">?</span> 帮助</span><span>打开本说明</span></div>
<div class="helpline"><span>文章页 <span class="kbd">j</span>/<span class="kbd">k</span> 上下篇 · <span class="kbd">f</span> 收藏 · <span class="kbd">m</span> 已读 · <span class="kbd">o</span> 原文</span><span>Vim 风快捷键</span></div>
<button class="helpclose" id="helpClose">知道了</button>
</div>
</div>
<script>
(function(){
  function setTheme(d){ if(d) document.documentElement.setAttribute('data-theme','dark'); else document.documentElement.removeAttribute('data-theme'); }
  try{ var saved=localStorage.getItem('theme'); if(saved==='dark'){ setTheme(true); } else if(saved==='light'){ setTheme(false); } else if(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches){ setTheme(true); } }catch(e){}
  var tb=document.getElementById('themeBtn');
  function syncTheme(){ var d=document.documentElement.getAttribute('data-theme')==='dark'; if(tb) tb.textContent=d?'浅色模式':'深色模式'; }
  if(tb) tb.addEventListener('click',function(){
    var d=document.documentElement.getAttribute('data-theme')==='dark';
    setTheme(!d); try{localStorage.setItem('theme', d?'light':'dark');}catch(e){}
    syncTheme();
  });
  syncTheme();

  var topBtn=document.getElementById('topBtn');
  window.addEventListener('scroll',function(){ topBtn.style.display=(window.scrollY>400)?'block':'none'; });
  topBtn.addEventListener('click',function(){ window.scrollTo({top:0,behavior:'smooth'}); });

  function loadSet(k){ try{ var v=localStorage.getItem(k); return v?JSON.parse(v):[]; }catch(e){ return []; } }
  function saveSet(k,a){ try{ localStorage.setItem(k,JSON.stringify(a)); }catch(e){} }
  function has(a,x){ return a.indexOf(x)>=0; }
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function escRe(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
  function hl(t,kw){ var x=esc(t); if(!kw) return x; var re=new RegExp(escRe(kw),'gi'); return x.replace(re,function(m){ return '<mark>'+m+'</mark>'; }); }

  var DATA={__DATA__};
  var bodyMap={};
  try{ fetch('search.json').then(function(r){ return r.json(); }).then(function(list){ list.forEach(function(x){ bodyMap[x.t]=x.b; }); apply(); }).catch(function(){}); }catch(e){}
  var favs=loadSet('favs'), reads=loadSet('read');
  var nodeMap={};
  var favOnly=false, unreadOnly=false;
  var visible={};
  var activeTag='全部';
  try{ var h=location.hash; if(h && h.length>1){ var tt=decodeURIComponent(h.slice(1)); if(tt==='全部' || DATA.some(function(e){return (e.tags||[]).indexOf(tt)>=0;})){ activeTag=tt; } } }catch(e){}

  var dateNodes={};
  document.querySelectorAll('.date').forEach(function(d){ dateNodes[d.getAttribute('data-date')]=d; });
  document.querySelectorAll('.item').forEach(function(a){
    var k=a.getAttribute('data-key'); nodeMap[k]=a;
    if(has(reads,k)) a.classList.add('read');
    var s=a.querySelector('.star'); if(s && has(favs,k)) s.classList.add('on');
    a.addEventListener('click',function(ev){
      if(ev.target.closest && (ev.target.closest('.star')||ev.target.closest('.srclink'))) return;
      if(!has(reads,k)){ reads.push(k); saveSet('read',reads); }
      a.classList.add('read');
      location.href=a.getAttribute('data-href');
    });
    a.addEventListener('keydown',function(ev){ if(ev.key==='Enter' && !(ev.target.closest && ev.target.closest('.star'))){ location.href=a.getAttribute('data-href'); } });
  });
  document.querySelectorAll('.star').forEach(function(s){
    s.addEventListener('click',function(ev){
      ev.preventDefault(); ev.stopPropagation();
      var k=s.getAttribute('data-key'); var i=favs.indexOf(k);
      if(i>=0) favs.splice(i,1); else favs.push(k);
      saveSet('favs',favs); s.classList.toggle('on',has(favs,k)); apply();
    });
  });

  var q=document.getElementById('q');
  function score(e,kw){
    var s=0;
    if((e.t||'').toLowerCase().indexOf(kw)>=0) s+=3;
    if((e.s||'').toLowerCase().indexOf(kw)>=0) s+=2;
    if((bodyMap[e.t]||'').toLowerCase().indexOf(kw)>=0) s+=1;
    if((e.tags||[]).some(function(t){ return t.toLowerCase().indexOf(kw)>=0; })) s+=1;
    return s;
  }
  function layoutDate(){
    var list=document.getElementById('list');
    var dates=[]; DATA.forEach(function(e){ if(dates.indexOf(e.d)<0) dates.push(e.d); });
    if(!sortDesc) dates.reverse();
    dates.forEach(function(d){
      var dn=dateNodes[d]; if(dn) list.appendChild(dn);
      DATA.forEach(function(e){ if(e.d===d){ var n=nodeMap[e.t]; if(n) list.appendChild(n); } });
    });
    Object.keys(dateNodes).forEach(function(d){
      var any=false; DATA.forEach(function(e){ if(e.d===d && visible[e.t]) any=true; });
      dateNodes[d].style.display=any?'':'none';
    });
  }
  function layoutSearch(kw){
    var list=document.getElementById('list');
    var scored=[];
    DATA.forEach(function(e){ if(visible[e.t]) scored.push({n:nodeMap[e.t], s:score(e,kw)}); });
    scored.sort(function(a,b){ return b.s-a.s; });
    scored.forEach(function(x){ if(x.n) list.appendChild(x.n); });
    Object.keys(dateNodes).forEach(function(d){ dateNodes[d].style.display='none'; });
  }
  function apply(){
    var kw=(q.value||'').trim().toLowerCase();
    visible={};
    DATA.forEach(function(e){
      var tagHit=(activeTag==='全部')||(e.tags||[]).indexOf(activeTag)>=0;
      var kwHit=!kw||(e.t||'').toLowerCase().indexOf(kw)>=0||(e.s||'').toLowerCase().indexOf(kw)>=0||(bodyMap[e.t]||'').toLowerCase().indexOf(kw)>=0;
      var favHit=!favOnly||has(favs,e.t);
      var readHit=!unreadOnly||!has(reads,e.t);
      visible[e.t]=tagHit&&kwHit&&favHit&&readHit;
      var a=nodeMap[e.t];
      if(a){
        a.style.display=visible[e.t]?'':'none';
        var tEl=a.querySelector('.t'); if(tEl) tEl.innerHTML=hl(e.t,kw);
        var sEl=a.querySelector('.s'); if(sEl) sEl.innerHTML=hl(e.s,kw);
      }
    });
    if(kw){ layoutSearch(kw); } else { layoutDate(); }
    var hasAny=false; DATA.forEach(function(e){ if(visible[e.t]) hasAny=true; });
    document.getElementById('empty').style.display=hasAny?'none':'';
  }
  q.addEventListener('input',apply);
  function setTag(tag){
    activeTag=tag;
    document.querySelectorAll('.chip').forEach(function(x){ x.classList.toggle('active', x.getAttribute('data-tag')===tag); });
    try{ if(history.replaceState) history.replaceState(null,'','#'+encodeURIComponent(tag)); }catch(e){}
    apply();
  }
  document.querySelectorAll('.chip').forEach(function(c){
    c.addEventListener('click',function(){ setTag(c.getAttribute('data-tag')); });
  });
  document.getElementById('favOnlyBtn').addEventListener('click',function(){
    favOnly=!favOnly; this.classList.toggle('active',favOnly); apply();
  });
  document.getElementById('unreadOnlyBtn').addEventListener('click',function(){
    unreadOnly=!unreadOnly; this.classList.toggle('active',unreadOnly); apply();
  });
  document.getElementById('randBtn').addEventListener('click',function(){
    if(!DATA.length) return;
    var e=DATA[Math.floor(Math.random()*DATA.length)];
    location.href=e.u;
  });
  document.addEventListener('keydown',function(ev){
    if(ev.key==='/' && document.activeElement!==q){ ev.preventDefault(); q.focus(); }
    else if((ev.ctrlKey||ev.metaKey) && ev.key.toLowerCase()==='k'){ ev.preventDefault(); q.focus(); }
    else if(ev.key.toLowerCase()==='f' && document.activeElement!==q){ document.getElementById('favOnlyBtn').click(); }
    else if(ev.key.toLowerCase()==='u' && document.activeElement!==q){ document.getElementById('unreadOnlyBtn').click(); }
    else if(ev.key.toLowerCase()==='a' && document.activeElement!==q){ setTag('全部'); }
    else if(ev.key.toLowerCase()==='r' && document.activeElement!==q){ document.getElementById('randBtn').click(); }
    else if(ev.key.toLowerCase()==='d' && document.activeElement!==q){ document.getElementById('themeBtn').click(); }
    else if(ev.key==='?'){ ev.preventDefault(); showHelp(); }
    else if(ev.key==='Escape'){ hideHelp(); }
  });

  var helpWrap=document.getElementById('helpWrap');
  function showHelp(){ helpWrap.classList.add('show'); }
  function hideHelp(){ helpWrap.classList.remove('show'); }
  document.getElementById('helpBtn').addEventListener('click',showHelp);
  document.getElementById('helpClose').addEventListener('click',hideHelp);
  helpWrap.addEventListener('click',function(ev){ if(ev.target===helpWrap) hideHelp(); });

  var sortDesc=true;
  document.getElementById('sortBtn').addEventListener('click',function(){
    sortDesc=!sortDesc;
    this.textContent=sortDesc?'排序：最新在前':'排序：最旧在前';
    apply();
  });
  document.getElementById('resetBtn').addEventListener('click',function(){
    q.value=''; favOnly=false; unreadOnly=false;
    document.getElementById('favOnlyBtn').classList.remove('active');
    document.getElementById('unreadOnlyBtn').classList.remove('active');
    setTag('全部');
  });
  document.querySelectorAll('.architem').forEach(function(b){
    b.addEventListener('click',function(){
      var d=document.querySelector('.date[data-date="'+b.getAttribute('data-date')+'"]');
      if(d) d.scrollIntoView({behavior:'smooth',block:'start'});
    });
  });

  document.querySelectorAll('.chip').forEach(function(c){ c.classList.toggle('active', c.getAttribute('data-tag')===activeTag); });
  function renderContinue(){
    var box=document.getElementById('continueBox');
    var hist=loadSet('hist');
    if(!hist || !hist.length){ box.innerHTML=''; return; }
    var c=hist[0];
    var html='<div class="continue"><div class="cthead">继续阅读</div><a class="clink" href="'+esc(c.u)+'">'+esc(c.t)+'</a>';
    var rest=hist.slice(1,4);
    if(rest.length){
      html+='<div class="crecent">最近读过：';
      rest.forEach(function(x){ html+='<a class="cmini" href="'+esc(x.u)+'">'+esc(x.t)+'</a>'; });
      html+='</div>';
    }
    html+='</div>';
    box.innerHTML=html;
  }
  renderContinue();
  apply();
})();
</script>
</body>
</html>"""


def _inline(text: str) -> str:
    text = _html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    out = []
    in_code = False
    code_buf = []
    h_counter = 0
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("```"):
            if in_code:
                out.append("<pre><code>" + _html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        if not s:
            continue
        h_counter += 1
        if s.startswith("### "):
            out.append(f'<h3 id="h-{h_counter}">{_inline(s[4:])}</h3>')
        elif s.startswith("## "):
            out.append(f'<h2 id="h-{h_counter}">{_inline(s[3:])}</h2>')
        elif s.startswith("# "):
            out.append(f'<h2 id="h-{h_counter}">{_inline(s[2:])}</h2>')
        elif s.startswith("> "):
            out.append(f"<blockquote>{_inline(s[2:])}</blockquote>")
        elif s.startswith("- ") or s.startswith("* "):
            out.append(f"<ul><li>{_inline(s[2:])}</li></ul>")
        elif re.match(r"^\d+[.、]\s", s):
            text = re.sub(r"^\d+[.、]\s", "", s)
            out.append(f"<ul><li>{_inline(text)}</li></ul>")
        elif s == "---":
            out.append("<hr>")
        elif s.startswith("*") and s.endswith("*") and len(s) > 2:
            out.append(f'<p style="color:var(--muted);font-size:13px;">{_inline(s.strip("*"))}</p>')
        else:
            out.append(f"<p>{_inline(s)}</p>")
    if in_code and code_buf:
        out.append("<pre><code>" + _html.escape("\n".join(code_buf)) + "</code></pre>")
    return "\n".join(out)


def _extract_toc(body_html: str):
    items = []
    for m in re.finditer(r'<h([23]) id="(h-\d+)">(.*?)</h\1>', body_html, flags=re.S):
        level, aid, text = m.group(1), m.group(2), m.group(3)
        text = re.sub(r"<[^>]+>", "", text)
        text = _html.unescape(text).strip()
        if text:
            items.append((level, aid, text))
    return items


def _safe_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", title).strip("_")
    return (name[:40] or "article")


def parse_article(md_text: str):
    lines = md_text.splitlines()
    title = "(无标题)"
    rest = lines
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            rest = lines[i + 1:]
            break
    return title, "\n".join(rest)


def _extract_source(rest: str) -> str:
    m = re.search(r"^\*来源[:：]\s*(.+?)\*?\s*$", rest, flags=re.M)
    if m:
        src = re.sub(r"\s*[·|]\s*\d{4}-\d{2}-\d{2}\s*$", "", m.group(1).strip()).strip()
        return src
    return ""


def _extract_source_url(rest: str) -> str:
    m = re.search(r"参考来源.*?(https?://[^\s)\]]+)", rest, flags=re.S)
    if m:
        return m.group(1).rstrip(".,;")
    m = re.search(r"https?://[^\s)\]]+", rest)
    return m.group(0).rstrip(".,;") if m else ""


def _plain_text(rest: str) -> str:
    t = re.sub(r"```.*?```", " ", rest, flags=re.S)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*_\-]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _extract_summary(rest: str) -> str:
    for line in rest.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", "##", "###", ">", "-", "*", "```", "---")):
            continue
        s = re.sub(r"\*\*", "", s)
        s = re.sub(r"`", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        if len(s) > 8:
            return s[:90] + ("…" if len(s) > 90 else "")
    return ""


def _classify(title: str, summary: str) -> list:
    text = (title + " " + summary).lower()
    tags = []
    for tag in TAG_ORDER:
        if any(kw in text for kw in TAG_RULES[tag]):
            tags.append(tag)
    if not tags:
        tags = ["综合"]
    return tags[:3]


def _read_minutes(rest: str) -> int:
    return max(1, round(len(rest) / 400))


def _word_count(rest: str) -> int:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", rest))
    latin = len(re.findall(r"[A-Za-z0-9]+", rest))
    return cjk + latin


def _cover_style(tags: list) -> str:
    t = tags[0] if tags else "综合"
    return TAG_COLORS.get(t, TAG_COLORS["综合"])


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def _rfc2822(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=8, tzinfo=timezone(timedelta(hours=8)))
        return dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        return date_str


def render_article_page(e: dict, site_title: str, site_url: str, older, newer, related) -> str:
    abs_url = site_url.rstrip("/") + "/" + quote(e["url"], safe="/")
    head = (
        f'<meta name="description" content="{_html.escape(e.get("summary") or site_title, quote=True)}">'
        f'<meta property="og:title" content="{_html.escape(e["title"], quote=True)}">'
        f'<meta property="og:description" content="{_html.escape(e.get("summary") or "", quote=True)}">'
        f'<meta property="og:type" content="article">'
        f'<meta property="og:url" content="{_html.escape(abs_url, quote=True)}">'
        f'<meta property="og:image" content="{_html.escape(site_url.rstrip("/") + "/assets/hero.jpg", quote=True)}">'
        f'<meta name="twitter:card" content="summary_large_image">'
    )
    tags_html = "".join(f'<span class="tag">{_html.escape(t)}</span>' for t in e["tags"])
    toc_items = _extract_toc(e["body_html"])
    toc_html = ""
    toc_side_html = ""
    if len(toc_items) >= 2:
        lis = []
        for level, aid, text in toc_items:
            cls = ' class="l3"' if level == "3" else ""
            lis.append(f'<li{cls}><a href="#{aid}">{_html.escape(text)}</a></li>')
        toc_html = f'<div class="toc-mobile"><details class="toc" open><summary>目录</summary><ul>{"".join(lis)}</ul></details></div>'
        toc_side_html = f'<aside class="tocside"><div class="toc"><div class="toctitle">目录</div><ul>{"".join(lis)}</ul></div></aside>'

    meta = (
        f'<span class="badge">{_html.escape(e.get("source") or "来源")}</span>'
        f'<span>{_html.escape(e["date"])}</span>'
        f'<span>约 {e["read_minutes"]} 分钟</span>'
        f'<span>{e["word_count"]} 字</span>'
        f'<span class="tools">'
        f'<button class="favbtn" type="button" id="favBtn" data-key="{_html.escape(e["title"])}" title="收藏">☆ 收藏</button>'
        f'<button class="fsbtn" type="button" id="dec" title="缩小字号">A−</button>'
        f'<button class="fsbtn" type="button" id="inc" title="放大字号">A＋</button>'
        f'<button class="copybtn" type="button" id="copyBtn">复制链接</button>'
        f'</span>'
    )

    nav = []
    if older:
        u = "../../" + quote(older["url"], safe="/")
        nav.append(f'<a class="navlink prev" href="{_html.escape(u)}">← 上一篇<br><span>{_html.escape(older["title"])}</span></a>')
    if newer:
        u = "../../" + quote(newer["url"], safe="/")
        nav.append(f'<a class="navlink next" href="{_html.escape(u)}">下一篇 →<br><span>{_html.escape(newer["title"])}</span></a>')
    nav_html = f'<div class="pagenav">{"".join(nav)}</div>' if nav else ""

    related_html = ""
    if related:
        cards = []
        for r in related:
            u = "../../" + quote(r["url"], safe="/")
            cards.append(f'<a class="relcard" href="{_html.escape(u)}">{_html.escape(r["title"])}<span class="rm">约 {r["read_minutes"]} 分钟</span></a>')
        related_html = f'<div class="related"><h3>相关文章</h3>{"".join(cards)}</div>'

    return (ARTICLE_TEMPLATE
            .replace("{__TITLE__}", _html.escape(e["title"]))
            .replace("{__SITE__}", _html.escape(site_title))
            .replace("{__HEAD__}", head)
            .replace("{__URL__}", _html.escape(e["url"], quote=True))
            .replace("{__TITLE_ATTR__}", _html.escape(e["title"], quote=True))
            .replace("{__SRC__}", _html.escape(e.get("source_url") or "", quote=True))
            .replace("{__META__}", meta)
            .replace("{__TAGS__}", tags_html)
            .replace("{__TOCMOBILE__}", toc_html)
            .replace("{__TOCSIDE__}", toc_side_html)
            .replace("{__BODY__}", e["body_html"])
            .replace("{__NAV__}", nav_html)
            .replace("{__RELATED__}", related_html)
            .replace("{__CSS__}", CSS)
            .replace("{__FAVICON__}", FAVICON))


def render_index(site_title: str, subtitle: str, site_url: str, entries: list) -> str:
    groups = OrderedDict()
    for e in entries:
        groups.setdefault(e["date"], []).append(e)

    parts = []
    for date_str, es in groups.items():
        parts.append(f'<div class="date" data-date="{_html.escape(date_str)}">{_html.escape(date_str)}</div>')
        for e in es:
            u = quote(e["url"], safe="/")
            key = _html.escape(e["title"])
            tags_html = "".join(f'<span class="tag">{_html.escape(t)}</span>' for t in e["tags"])
            source = e.get("source") or "来源"
            src_url = e.get("source_url") or ""
            srclink = f'<a class="srclink" href="{_html.escape(src_url)}" target="_blank" rel="noopener">原文 ↗</a>' if src_url else ""
            parts.append(
                f'<div class="item" data-key="{key}" data-href="{_html.escape(u)}" tabindex="0" role="link">'
                f'<div class="cover" style="background:{_cover_style(e["tags"])}"></div>'
                f'<div class="body">'
                f'<div class="t">{key}</div>'
                + (f'<div class="s">{_html.escape(e["summary"])}</div>' if e["summary"] else "")
                + f'<div class="meta"><span class="badge">{_html.escape(source)}</span>'
                f'<span>{_html.escape(e["date"])}</span><span>约 {e["read_minutes"]} 分钟</span><span>{e["word_count"]} 字</span>'
                f'<span class="readmark">已读</span>'
                + srclink
                + f'<span class="star" data-key="{key}" title="收藏">☆</span></div>'
                f'<div class="tags">{tags_html}</div>'
                f'</div></div>'
            )
    body = "\n".join(parts) if parts else '<div class="empty">暂无文章，先运行一次生成</div>'

    tag_counts = {}
    for e in entries:
        for t in e["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    ordered_tags = [t for t in TAG_ORDER if t in tag_counts]
    ordered_tags += [t for t in sorted(tag_counts) if t not in ordered_tags]
    chips = [f'<button class="chip" type="button" data-tag="全部">全部<em>{len(entries)}</em></button>']
    chips += [f'<button class="chip" type="button" data-tag="{_html.escape(t)}">{_html.escape(t)}<em>{tag_counts[t]}</em></button>' for t in ordered_tags]
    chips_html = "".join(chips)

    archive_items = []
    for date_str, es in groups.items():
        archive_items.append(
            f'<button class="architem" type="button" data-date="{_html.escape(date_str)}">{_html.escape(date_str)}<em>{len(es)}</em></button>'
        )
    archive_html = f'<details class="archpanel"><summary>按日期归档（{len(groups)} 天）</summary><div class="archlist">{"".join(archive_items)}</div></details>' if groups else ""

    total = len(entries)
    latest = entries[0]["date"] if entries else ""
    today_count = sum(1 for e in entries if e["date"] == latest) if entries else 0
    hstat_html = (
        f'<span class="hstat">累计 <b>{total}</b> 篇</span>'
        f'<span class="hstat">最新 <b>{_html.escape(latest)}</b></span>'
        f'<span class="hstat">当日新增 <b>{today_count}</b> 篇</span>'
        f'<span class="hstat">覆盖 <b>{len(ordered_tags)}</b> 个方向</span>'
    )

    data = [{"t": e["title"], "d": e["date"], "u": quote(e["url"], safe="/"),
             "s": e["summary"], "tags": e["tags"]} for e in entries]
    data_json = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")

    head = (
        f'<meta name="description" content="{_html.escape(subtitle, quote=True)}">'
        f'<meta property="og:title" content="{_html.escape(site_title, quote=True)}">'
        f'<meta property="og:description" content="{_html.escape(subtitle, quote=True)}">'
        f'<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{_html.escape(site_url, quote=True)}">'
        f'<meta property="og:image" content="{_html.escape(site_url.rstrip("/") + "/assets/hero.jpg", quote=True)}">'
        f'<meta name="twitter:card" content="summary_large_image">'
    )

    return (INDEX_TEMPLATE
            .replace("{__TITLE__}", _html.escape(site_title))
            .replace("{__SUBTITLE__}", _html.escape(subtitle))
            .replace("{__HEAD__}", head)
            .replace("{__HSTATS__}", hstat_html)
            .replace("{__ARCHIVE__}", archive_html)
            .replace("{__CHIPS__}", chips_html)
            .replace("{__BODY__}", body)
            .replace("{__DATA__}", data_json)
            .replace("{__CSS__}", CSS)
            .replace("{__FAVICON__}", FAVICON))


def render_feed(site_title: str, subtitle: str, site_url: str, entries: list) -> str:
    base = site_url.rstrip("/") + "/"
    items = []
    for e in entries:
        link = base + quote(e["url"], safe="/")
        items.append(
            "<item>"
            f"<title>{_xml_escape(e['title'])}</title>"
            f"<link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{_rfc2822(e['date'])}</pubDate>"
            f"<description>{_xml_escape(e.get('summary') or '')}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{_xml_escape(site_title)}</title>"
        f"<link>{base}</link>"
        f"<description>{_xml_escape(subtitle)}</description>"
        f"<lastBuildDate>{_rfc2822(entries[0]['date']) if entries else ''}</lastBuildDate>"
        + "".join(items)
        + "</channel></rss>"
    )


def build_site(cfg: dict):
    output_dir = Path(cfg["run"]["output_dir"])
    site_cfg = cfg.get("site", {})
    site_title = site_cfg.get("title", "我的专业科技日报")
    subtitle = site_cfg.get("subtitle", "")
    site_url = site_cfg.get("url") or "https://qzl666-glitch.github.io/tech-daily/"
    site_dir = Path(site_cfg.get("output_dir", output_dir.parent / "docs"))
    site_dir.mkdir(parents=True, exist_ok=True)

    raw = []
    for md_file in sorted(output_dir.rglob("*.md"), reverse=True):
        try:
            rel = md_file.relative_to(output_dir)
            date_str = rel.parts[0] if len(rel.parts) > 1 else "未归档"
            md_text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[site] 跳过 {md_file}: {e}")
            continue
        title, rest = parse_article(md_text)
        summary = _extract_summary(rest)
        raw.append({
            "title": title,
            "date": date_str,
            "source": _extract_source(rest),
            "source_url": _extract_source_url(rest),
            "summary": summary,
            "slug": _safe_filename(title),
            "tags": _classify(title, summary),
            "read_minutes": _read_minutes(rest),
            "word_count": _word_count(rest),
            "body_html": md_to_html(rest),
            "body_text": _plain_text(rest),
        })

    raw.sort(key=lambda e: (e["date"], e["title"]), reverse=True)
    entries = []
    for e in raw:
        e["url"] = f"articles/{e['date']}/{e['slug']}.html"
        entries.append(e)

    for i, e in enumerate(entries):
        older = entries[i + 1] if i + 1 < len(entries) else None
        newer = entries[i - 1] if i > 0 else None
        related = []
        for o in entries:
            if o is e:
                continue
            if set(o["tags"]) & set(e["tags"]):
                related.append(o)
            if len(related) >= 3:
                break
        if len(related) < 3:
            for o in entries:
                if o is e or o in related:
                    continue
                related.append(o)
                if len(related) >= 3:
                    break
        related = related[:3]
        art_dir = site_dir / "articles" / e["date"]
        art_dir.mkdir(parents=True, exist_ok=True)
        (art_dir / f"{e['slug']}.html").write_text(
            render_article_page(e, site_title, site_url, older, newer, related), encoding="utf-8")

    (site_dir / "index.html").write_text(render_index(site_title, subtitle, site_url, entries), encoding="utf-8")
    (site_dir / "feed.xml").write_text(render_feed(site_title, subtitle, site_url, entries), encoding="utf-8")
    search_data = [{"t": e["title"], "u": e["url"], "b": e["body_text"]} for e in entries]
    (site_dir / "search.json").write_text(json.dumps(search_data, ensure_ascii=False), encoding="utf-8")
    return str(site_dir), len(entries)
