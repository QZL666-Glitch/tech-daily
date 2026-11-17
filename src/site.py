"""本地 / 公网「个人日报网站」生成器。

把 output/ 下的 Markdown 文章渲染成一个可浏览、可搜索的静态网站：
- site/index.html              首页（按日期归档 + 实时搜索）
- site/articles/日期/xxx.html  每篇文章独立页面
"""
import html as _html
import json
import re
from collections import OrderedDict
from pathlib import Path
from urllib.parse import quote

CSS = """
:root{--bg:#f5f6f8;--card:#ffffff;--text:#1f2328;--muted:#6b7280;--accent:#0a7d3f;--border:#e5e7eb;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.7;}
a{color:var(--accent);text-decoration:none;}
.header{background:#0d1117;color:#fff;padding:30px 20px;}
.header h1{margin:0 0 6px;font-size:26px;}
.header p{margin:0;color:#9aa4b2;font-size:14px;}
.wrap{max-width:780px;margin:0 auto;padding:20px 16px 60px;}
.search{width:100%;padding:12px 14px;font-size:15px;border:1px solid var(--border);border-radius:10px;margin-bottom:8px;outline:none;background:#fff;}
.hint{color:var(--muted);font-size:13px;margin:0 0 18px;}
.date{font-size:15px;font-weight:700;color:#374151;margin:24px 0 10px;padding-left:10px;border-left:4px solid var(--accent);}
.item{display:block;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:10px;color:inherit;}
.item:hover{border-color:var(--accent);}
.item .t{font-size:16px;font-weight:600;margin-bottom:4px;}
.item .s{font-size:13.5px;color:var(--muted);}
.item .meta{font-size:12px;color:#9aa4b2;margin-top:6px;}
.empty{color:var(--muted);text-align:center;padding:40px 0;}
article{max-width:780px;margin:0 auto;padding:20px 16px 60px;}
article .card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:24px 22px;}
article h1{font-size:24px;line-height:1.4;margin:0 0 6px;}
article .meta{color:var(--muted);font-size:13px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--border);}
article h2{font-size:19px;margin:26px 0 10px;}
article h3{font-size:16px;margin:20px 0 8px;}
article p{margin:0 0 14px;}
article ul,article ol{margin:0 0 14px;padding-left:22px;}
article li{margin:6px 0;}
article blockquote{border-left:3px solid var(--accent);background:#f0f9f4;margin:0 0 14px;padding:10px 14px;color:#4b5563;border-radius:0 8px 8px 0;}
article pre{background:#0d1117;color:#e6edf3;padding:14px;border-radius:10px;overflow-x:auto;font-size:13px;line-height:1.6;}
article code{font-family:Consolas,Monaco,monospace;font-size:0.92em;}
article :not(pre)>code{background:#f0f0f0;color:#c7254e;padding:1px 6px;border-radius:4px;}
article hr{border:none;border-top:1px solid var(--border);margin:24px 0;}
.footer{max-width:780px;margin:0 auto;padding:0 16px 40px;color:#9aa4b2;font-size:12px;text-align:center;}
"""

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{__TITLE__} · {__SITE__}</title>
<style>{__CSS__}</style>
</head>
<body>
<div class="header"><div style="max-width:780px;margin:0 auto;"><a href="../../index.html" style="color:#fff;">← 返回目录</a></div></div>
<article><div class="card">
<h1>{__TITLE__}</h1>
<div class="meta">{__DATE__}</div>
{__BODY__}
</div></article>
<div class="footer">由 AI 自动生成 · 仅供学习参考</div>
</body>
</html>"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{__TITLE__}</title>
<style>{__CSS__}</style>
</head>
<body>
<div class="header">
<div style="max-width:780px;margin:0 auto;">
<h1>{__TITLE__}</h1>
<p>{__SUBTITLE__}</p>
</div>
</div>
<div class="wrap">
<input class="search" id="q" placeholder="搜索文章标题 / 关键词…">
<p class="hint">共 {__COUNT__} 篇 · 输入关键词实时筛选</p>
<div id="list">
{__BODY__}
</div>
</div>
<div class="footer">每天自动更新 · 由 AI 生成，仅供学习参考</div>
<script>
const DATA = {__DATA__};
const q = document.getElementById('q');
q.addEventListener('input', function(){
  var kw = q.value.trim().toLowerCase();
  var items = document.querySelectorAll('.item,.date');
  for (var i=0;i<items.length;i++){ items[i].style.display = ''; }
  if (!kw) return;
  DATA.forEach(function(e){
    var hit = (e.t||'').toLowerCase().indexOf(kw) >= 0 || (e.s||'').toLowerCase().indexOf(kw) >= 0;
    if (!hit){
      var a = document.querySelector('a[href="'+e.u+'"]');
      if (a) a.style.display = 'none';
    }
  });
});
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
        if s.startswith("### "):
            out.append(f"<h3>{_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{_inline(s[3:])}</h2>")
        elif s.startswith("# "):
            out.append(f"<h2>{_inline(s[2:])}</h2>")
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
            out.append(f'<p style="color:#9aa4b2;font-size:13px;">{_inline(s.strip("*"))}</p>')
        else:
            out.append(f"<p>{_inline(s)}</p>")
    if in_code and code_buf:
        out.append("<pre><code>" + _html.escape("\n".join(code_buf)) + "</code></pre>")
    return "\n".join(out)


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
        return m.group(1).strip()
    return ""


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


def render_article_page(title: str, date_str: str, body_html: str, site_title: str) -> str:
    return (ARTICLE_TEMPLATE
            .replace("{__TITLE__}", _html.escape(title))
            .replace("{__SITE__}", _html.escape(site_title))
            .replace("{__DATE__}", _html.escape(date_str))
            .replace("{__BODY__}", body_html)
            .replace("{__CSS__}", CSS))


def render_index(site_title: str, subtitle: str, entries: list) -> str:
    groups = OrderedDict()
    for e in entries:
        groups.setdefault(e["date"], []).append(e)

    parts = []
    for date, es in groups.items():
        parts.append(f'<div class="date">{_html.escape(date)}</div>')
        for e in es:
            u = quote(e["url"], safe="/")  # 中文路径做 URL 编码，file:// 与 http 下都能正确跳转
            parts.append(
                f'<a class="item" href="{_html.escape(u)}">'
                f'<div class="t">{_html.escape(e["title"])}</div>'
                + (f'<div class="s">{_html.escape(e["summary"])}</div>' if e["summary"] else "")
                + f'<div class="meta">{_html.escape(e["source"] or "")}</div>'
                f'</a>'
            )
    body = "\n".join(parts) if parts else '<div class="empty">暂无文章，先运行一次生成</div>'
    data = [{"t": e["title"], "d": e["date"], "u": quote(e["url"], safe="/"), "s": e["summary"]} for e in entries]

    return (INDEX_TEMPLATE
            .replace("{__TITLE__}", _html.escape(site_title))
            .replace("{__SUBTITLE__}", _html.escape(subtitle))
            .replace("{__COUNT__}", str(len(entries)))
            .replace("{__BODY__}", body)
            .replace("{__DATA__}", json.dumps(data, ensure_ascii=False))
            .replace("{__CSS__}", CSS))


def build_site(cfg: dict):
    output_dir = Path(cfg["run"]["output_dir"])
    site_cfg = cfg.get("site", {})
    site_title = site_cfg.get("title", "我的专业科技日报")
    subtitle = site_cfg.get("subtitle", "")
    site_dir = Path(site_cfg.get("output_dir", output_dir.parent / "docs"))
    site_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for md_file in sorted(output_dir.rglob("*.md"), reverse=True):
        try:
            rel = md_file.relative_to(output_dir)
            date_str = rel.parts[0] if len(rel.parts) > 1 else "未归档"
            md_text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[site] 跳过 {md_file}: {e}")
            continue

        title, rest = parse_article(md_text)
        body_html = md_to_html(rest)
        source = _extract_source(rest)
        summary = _extract_summary(rest)
        slug = _safe_filename(title)

        art_dir = site_dir / "articles" / date_str
        art_dir.mkdir(parents=True, exist_ok=True)
        art_path = art_dir / f"{slug}.html"
        art_path.write_text(render_article_page(title, date_str, body_html, site_title), encoding="utf-8")

        entries.append({
            "title": title,
            "date": date_str,
            "source": source,
            "summary": summary,
            "url": f"articles/{date_str}/{slug}.html",
        })

    entries.sort(key=lambda e: e["date"], reverse=True)
    (site_dir / "index.html").write_text(render_index(site_title, subtitle, entries), encoding="utf-8")
    return str(site_dir), len(entries)
