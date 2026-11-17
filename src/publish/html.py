"""把生成的 Markdown 转成微信公众号可直接粘贴的 HTML（全内联样式）。

微信编辑器会剥离 <style> 标签和外部 CSS，所以这里全部写成内联 style。
"""
import html as _html
import re

H2 = 'style="font-size:19px;font-weight:bold;color:#1a1a1a;margin:22px 0 12px;line-height:1.4;"'
H3 = 'style="font-size:16px;font-weight:bold;color:#0a0a0a;border-left:4px solid #07c160;padding-left:10px;margin:20px 0 10px;line-height:1.4;"'
P = 'style="font-size:15px;color:#3f3f3f;line-height:1.75;margin:0 0 12px;letter-spacing:0.3px;"'
CODE_INLINE = 'style="font-family:Consolas,Monaco,monospace;background:#f2f2f2;color:#c7254e;padding:1px 6px;border-radius:3px;font-size:13px;"'
PRE = 'style="background:#2d2d2d;color:#f8f8f2;padding:12px 14px;border-radius:6px;font-size:13px;line-height:1.6;overflow-x:auto;white-space:pre-wrap;word-break:break-all;margin:0 0 12px;"'
BLOCKQUOTE = 'style="border-left:3px solid #d9d9d9;background:#fafafa;color:#666;padding:10px 14px;margin:0 0 12px;font-size:14px;"'
A = 'style="color:#576b95;text-decoration:none;"'
HR = 'style="border:none;border-top:1px solid #e5e5e5;margin:24px 0;"'
LI = 'style="font-size:15px;color:#3f3f3f;line-height:1.75;margin:4px 0;"'


def _inline(text: str) -> str:
    text = _html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", rf'<code {CODE_INLINE}>\1</code>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", rf'<a {A} href="\2">\1</a>', text)
    return text


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out = []
    in_code = False
    code_buf = []
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                out.append(f'<section><pre {PRE}><code>{_html.escape(chr(10).join(code_buf))}</code></pre></section>')
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue

        if not stripped:
            continue

        if stripped.startswith("### "):
            out.append(f'<p {P}><strong>{_inline(stripped[4:])}</strong></p>')
        elif stripped.startswith("## "):
            out.append(f'<h2 {H3}>{_inline(stripped[3:])}</h2>')
        elif stripped.startswith("# "):
            out.append(f'<h2 {H2}>{_inline(stripped[2:])}</h2>')
        elif stripped.startswith("> "):
            out.append(f'<blockquote {BLOCKQUOTE}>{_inline(stripped[2:])}</blockquote>')
        elif stripped.startswith("- ") or stripped.startswith("* "):
            out.append(f'<ul style="margin:0 0 12px;padding-left:22px;"><li {LI}>{_inline(stripped[2:])}</li></ul>')
        elif re.match(r"^\d+[.、]\s", stripped):
            text = re.sub(r"^\d+[.、]\s", "", stripped)
            out.append(f'<ul style="margin:0 0 12px;padding-left:22px;"><li {LI}>{_inline(text)}</li></ul>')
        elif stripped == "---":
            out.append(f'<hr {HR}/>')
        elif stripped.startswith("*") and stripped.endswith("*") and len(stripped) > 2:
            out.append(f'<p {P} style="color:#888;font-size:13px;">{_inline(stripped.strip("*"))}</p>')
        else:
            out.append(f'<p {P}>{_inline(stripped)}</p>')

    if in_code and code_buf:
        out.append(f'<section><pre {PRE}><code>{_html.escape(chr(10).join(code_buf))}</code></pre></section>')

    return "\n".join(out)


def to_wechat_html(md: str) -> str:
    """生成可直接粘贴进微信编辑器“源代码”模式的整段 HTML。"""
    return f'<section style="padding:0;">{markdown_to_html(md)}</section>'
