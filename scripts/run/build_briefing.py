"""docs/BRIEFING.md -> docs/BRIEFING.html: one page, for the team only.

The Markdown file is the text; this turns it into a page to read from in a
meeting: a jump bar, a search box that filters the questions and the table
rows, "Say" lines set apart, and the screen guide's pictures embedded (so
the page is one file that opens anywhere, with no network).

    python scripts/run/build_briefing.py

Pictures: docs/briefing_shots/*.webp, retaken with
scripts/run/capture_briefing_shots.py. A missing picture is skipped.

Only the Markdown this file uses is understood: #..#### headings, paragraphs,
"> " quotes, "- " and "1. " lists (one level, wrapped lines indented), pipe
tables, "---", **bold**, *italic*, `code` and [links](url).
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "BRIEFING.md"
OUT = ROOT / "docs" / "BRIEFING.html"
SHOTS = ROOT / "docs" / "briefing_shots"

# pictures placed right after a heading (matched on its start)
PICTURES = {
    "A0 ·": [("landing", "The top of the landing page: the name, the line, the module tiles and the Data Backbone strip.")],
    "SlideSense → Forecast": [
        ("sl_main", "SlideSense → Forecast, Itanagar, the whole week. Left: the card, the 7 days, the place's tiles. Centre: the map and its key. Below: roads by level and districts to watch."),
        ("sl_strip", "The framed strip under the map: All of Arunachal, the same whichever place is picked.")],
    "SlideSense → Roads": [
        ("sl_roads_main", "SlideSense → Roads, the route Itanagar → Ziro: the route's card, its kilometres each day, the route by level, the map."),
        ("sl_roads_strip", "With a route picked, the strip turns amber and says so: This route · Current route.")],
    "FloodSense → Live forecast": [
        ("fl_main", "FloodSense → Live forecast, Pasighat, the whole week. Left: the card, the 7 days, the place's four tiles. Centre: the map with the gauged rivers. Below: the rivers list."),
        ("fl_strip", "The All of Arunachal strip for floods.")],
    "FloodSense → one river gauge": [
        ("fl_gauge30", "One gauge (Kibithu): four facts, then the graph. 30 days: measured daily highs, the level line after Now, the official lines, the chance bars."),
        ("fl_gauge3", "The same gauge, Last 3 days: every reading CWC sent, and each day's expected high drawn across that day.")],
}

LABELS = {"Say": "say", "Detail": "detail", "Careful": "careful", "Keep back": "keep",
          "Only if asked": "detail", "In one line": "detail", "The picture to hold": "detail",
          "In short": "detail", "How we got it": "detail", "Still on APSSDI, not pulled yet": "detail",
          "Why the high country needs their field data most": "detail", "Who they are": "plain",
          "Infrastructure": "plain", "Their plan": "plain", "On the morning": "careful"}


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"(https?://[^\s<'),]+)", lambda m: m.group(1) if "href=" in s[max(0, m.start() - 7):m.start()]
               else f"<a href='{m.group(1)}'>{m.group(1)}</a>", s)
    return s


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def picture(name: str, cap: str) -> str:
    p = SHOTS / f"{name}.webp"
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f"<figure class='shot'><a href='#' class='zoom' title='Click to enlarge'>"
            f"<img alt='{html.escape(cap)}' loading='lazy' src='data:image/webp;base64,{b64}'></a>"
            f"<figcaption>{inline(cap)}</figcaption></figure>")


def para_class(text: str) -> tuple[str, str]:
    m = re.match(r"\*\*([^*:]+?)(?: \(([^)]*)\))?:\*\*\s*(.*)", text, re.S)
    if m and m.group(1) in LABELS:
        kind = LABELS[m.group(1)]
        lab = m.group(1) + (f" ({m.group(2)})" if m.group(2) else "")
        if kind == "plain":
            return "", f"<p><b>{inline(lab)}.</b> {inline(m.group(3))}</p>"
        return kind, (f"<div class='call {kind}'><span class='tag'>{html.escape(lab)}</span>"
                      f"<p>{inline(m.group(3))}</p></div>")
    if text.startswith("*On screen") or text.startswith("*On screen,"):
        return "screen", f"<div class='onscreen'><span class='tag'>On screen</span><p>{inline(text.strip('*').split(':', 1)[1].strip())}</p></div>"
    return "", f"<p>{inline(text)}</p>"


def table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [c for c in cells[2:]]
    align = ["center" if re.fullmatch(r":-+:", a.strip()) else "" for a in cells[1]]
    th = "".join(f"<th{' class=c' if align[i] == 'center' else ''}>{inline(h)}</th>" for i, h in enumerate(head))
    tb = "".join("<tr>" + "".join(f"<td{' class=c' if i < len(align) and align[i] == 'center' else ''}>{inline(c)}</td>"
                                  for i, c in enumerate(r)) + "</tr>" for r in body)
    return f"<div class='tw'><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>"


def convert(md: str) -> tuple[str, list]:
    lines = md.splitlines()
    out, nav, i = [], [], 0
    open_q = open_sec = header_open = False
    title = ""

    def close_q():
        nonlocal open_q
        if open_q:
            out.append("</div>")
            open_q = False

    def close_sec():
        nonlocal open_sec
        close_q()
        if open_sec:
            out.append("</section>")
            open_sec = False

    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("#### "):
            close_q()
            q = ln[5:].strip()
            room = ""
            m = re.match(r"Q(?: \(([^)]+)\))?:\s*(.*)", q)
            if m:
                room, q = m.group(1) or "", m.group(2)
            out.append(f"<div class='q'><h4>{f'<span class=room>{html.escape(room)}</span>' if room else ''}{inline(q)}</h4>")
            open_q = True
        elif ln.startswith("### "):
            close_q()
            t = ln[4:].strip()
            out.append(f"<h3 id='{slug(t)}'>{inline(t)}</h3>")
            for start, pics in PICTURES.items():
                if t.startswith(start):
                    out.extend(picture(*p) for p in pics)
        elif ln.startswith("## "):
            close_sec()
            t = ln[3:].strip()
            sid = slug(t)
            nav.append(("sec", t, sid))
            out.append(f"<section id='{sid}'><h2>{inline(t)}</h2>")
            open_sec = True
            for start, pics in PICTURES.items():
                if t.startswith(start):
                    out.extend(picture(*p) for p in pics)
        elif ln.startswith("# "):
            close_sec()
            t = ln[2:].strip()
            if not title:
                title = t
                out.append(f"<header class='top' id='top'><p class='eyebrow'>BEE Solutions · team only</p><h1>{inline(t)}</h1>")
                header_open = True
                i += 1
                continue
            sid = slug(t)
            nav.append(("part", t, sid))
            out.append(f"<div class='part' id='{sid}'><h1>{inline(t)}</h1></div>")
        elif ln.strip() == "---":
            # the first rule closes the title block; the rest are rules
            out.append("</header>" if header_open else "<hr>")
            header_open = False
        elif ln.startswith(">"):
            buf, paras = [], []
            while i < len(lines) and lines[i].startswith(">"):
                t = lines[i][1:].strip()
                if not t:
                    paras.append(" ".join(buf)); buf = []
                else:
                    buf.append(t)
                i += 1
            paras.append(" ".join(buf))
            paras = [p for p in paras if p]
            lab = "Say"
            m = re.match(r"\*\*([^*]+?):\*\*\s*(.*)", paras[0])
            if m:
                lab, paras[0] = m.group(1), m.group(2)
            out.append(f"<div class='say'><span class='tag'>{html.escape(lab)}</span>"
                       + "".join(f"<p>{inline(p)}</p>" for p in paras) + "</div>")
            continue
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            out.append(table(rows))
            continue
        elif re.match(r"(- |\d+\. )", ln):
            ordered = bool(re.match(r"\d+\. ", ln))
            items = []
            while i < len(lines) and (re.match(r"(- |\d+\. )", lines[i]) or
                                      (lines[i].startswith("   ") and items)):
                if re.match(r"(- |\d+\. )", lines[i]):
                    items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        else:
            buf = [ln.strip()]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|>|\||- |\d+\. |---)", lines[i]):
                buf.append(lines[i].strip()); i += 1
            if not buf[0].startswith("**Visual version:**"):     # this IS the visual version
                out.append(para_class(" ".join(buf))[1])
            continue
        i += 1
    close_sec()
    return "\n".join(out), nav


CSS = """
:root{--bg:#f2f5f7;--surface:#fbfcfd;--surface-2:#e9eef2;--ink:#0f1b26;--ink-2:#435466;--ink-3:#617384;
--line:#d7dfe6;--line-2:#c0cbd5;--teal:#0d9488;--teal-ink:#0b6f66;--teal-wash:#e2f3f0;--blue:#2a78d6;
--blue-ink:#1c5cab;--blue-wash:#e5eefb;--slate:#5b6b7f;--slate-ink:#3f4f64;--slate-wash:#e6ebf1;
--warn:#c98500;--warn-ink:#855600;--warn-wash:#fcf1d9;--crit:#d03b3b;--crit-ink:#a32626;--crit-wash:#fae8e8;
--gold:#b7791f;--gold-wash:#fbf3e3;--mark:#ffe08a;
--f-display:"Sora","Segoe UI Semibold","Segoe UI",system-ui,sans-serif;
--f-body:"IBM Plex Sans","Segoe UI",system-ui,-apple-system,sans-serif;
--f-mono:"IBM Plex Mono","Cascadia Mono",Consolas,ui-monospace,monospace;--gut:clamp(14px,4vw,40px)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0b0f14;--surface:#111823;--surface-2:#18222f;
--ink:#e5edf5;--ink-2:#a9b9ca;--ink-3:#8196ac;--line:#223044;--line-2:#2f4258;--teal:#1fa89e;--teal-ink:#63e0d3;
--teal-wash:#0f2a2c;--blue:#3987e5;--blue-ink:#8fbaf6;--blue-wash:#13233d;--slate:#8b9bb4;--slate-ink:#c3cfdf;
--slate-wash:#1a2431;--warn:#fab219;--warn-ink:#f6c55e;--warn-wash:#2a2210;--crit:#e66767;--crit-ink:#f39c9c;
--crit-wash:#2c1618;--gold:#f5a623;--gold-wash:#2a2010;--mark:#6b5310;color-scheme:dark}}
:root[data-theme=dark]{--bg:#0b0f14;--surface:#111823;--surface-2:#18222f;--ink:#e5edf5;--ink-2:#a9b9ca;--ink-3:#8196ac;
--line:#223044;--line-2:#2f4258;--teal:#1fa89e;--teal-ink:#63e0d3;--teal-wash:#0f2a2c;--blue:#3987e5;--blue-ink:#8fbaf6;
--blue-wash:#13233d;--slate:#8b9bb4;--slate-ink:#c3cfdf;--slate-wash:#1a2431;--warn:#fab219;--warn-ink:#f6c55e;
--warn-wash:#2a2210;--crit:#e66767;--crit-ink:#f39c9c;--crit-wash:#2c1618;--gold:#f5a623;--gold-wash:#2a2010;--mark:#6b5310;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:6.2rem;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 1.02rem/1.62 var(--f-body)}
.wrap{max-width:72rem;margin-inline:auto;padding:0 var(--gut) 6rem}
h1,h2,h3,h4{font-family:var(--f-display);letter-spacing:-.015em;margin:0;text-wrap:balance}
.top{padding:2.4rem 0 1rem;display:grid;gap:.7rem}.top h1{font-size:clamp(1.9rem,1.2rem + 3vw,3rem);line-height:1.08}
.eyebrow{font:500 .72rem/1.2 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin:0}
.part{margin:4.2rem 0 .4rem;padding:1.1rem 1.2rem;border-radius:16px;background:var(--ink);color:var(--bg)}
.part h1{font-size:clamp(1.4rem,1rem + 1.6vw,2rem)}
section{padding-top:2.4rem}h2{font-size:clamp(1.35rem,1.05rem + 1.3vw,1.85rem);line-height:1.18;margin-bottom:.9rem;
padding-bottom:.45rem;border-bottom:2px solid var(--ink)}
h3{font-size:1.12rem;margin:1.9rem 0 .6rem;color:var(--slate-ink)}
p{margin:.55rem 0;max-width:78ch}ul,ol{margin:.5rem 0;padding-left:1.3rem;max-width:80ch}li{margin:.28rem 0}
a{color:var(--blue-ink)}code{font:500 .86em var(--f-mono);background:var(--surface-2);padding:.08em .35em;border-radius:5px}
hr{border:0;border-top:1px solid var(--line);margin:2rem 0}
.tag{display:inline-block;font:600 .64rem/1 var(--f-mono);letter-spacing:.13em;text-transform:uppercase;margin-bottom:.35rem}
.say{background:var(--teal-wash);border:1px solid var(--teal);border-left:5px solid var(--teal);border-radius:12px;
padding:.85rem 1.1rem;margin:.8rem 0}.say .tag{color:var(--teal-ink)}
.say p{font-size:1.07rem;line-height:1.58;color:var(--ink);max-width:none;margin:.3rem 0}
.call{border-radius:10px;padding:.6rem .95rem;margin:.6rem 0;border:1px solid var(--line-2);background:var(--surface)}
.call p{margin:.15rem 0;max-width:none}.call.detail{border-left:4px solid var(--blue)}.call.detail .tag{color:var(--blue-ink)}
.call.careful{border-left:4px solid var(--warn);background:var(--warn-wash)}.call.careful .tag{color:var(--warn-ink)}
.call.keep{border-left:4px solid var(--crit);background:var(--crit-wash)}.call.keep .tag{color:var(--crit-ink)}
.onscreen{border:1px dashed var(--line-2);border-radius:10px;padding:.55rem .9rem;margin:.4rem 0 .9rem;
background:var(--surface-2);font-size:.92rem;color:var(--ink-2)}.onscreen .tag{color:var(--slate-ink)}.onscreen p{margin:0;max-width:none}
.q{border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:.85rem 1.05rem;margin:.75rem 0}
.q h4{font-size:1.02rem;line-height:1.35;margin-bottom:.25rem}.q h4::before{content:"Q  ";color:var(--gold);font-family:var(--f-mono)}
.room{display:inline-block;font:600 .66rem/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;
background:var(--gold-wash);color:var(--gold);border:1px solid var(--gold);border-radius:999px;padding:.25rem .5rem;margin-right:.5rem;vertical-align:2px}
.q .say{margin:.45rem 0}
.tw{overflow-x:auto;margin:.8rem 0;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.9rem;line-height:1.45}
th,td{padding:.5rem .7rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font:600 .7rem/1.3 var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);background:var(--surface-2)}
td.c,th.c{text-align:center}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:var(--surface-2)}
td:first-child{font-weight:500}
.shot{margin:1rem 0 1.4rem;display:grid;gap:.45rem}.shot img{width:100%;border-radius:12px;border:1px solid var(--line-2);display:block;cursor:zoom-in}
.shot figcaption{font-size:.86rem;color:var(--ink-2)}
.bar{position:sticky;top:0;z-index:30;background:var(--bg);border-bottom:1px solid var(--line)}
.bar-in{max-width:72rem;margin-inline:auto;padding:.45rem var(--gut);display:grid;gap:.4rem}
.row1{display:flex;gap:.5rem;align-items:center}
#q{flex:1;min-width:0;font:400 .95rem var(--f-body);padding:.5rem .8rem;border-radius:10px;border:1px solid var(--line-2);
background:var(--surface);color:var(--ink)}#n{font:500 .74rem var(--f-mono);color:var(--ink-3);white-space:nowrap}
.btn{font:500 .74rem var(--f-mono);padding:.45rem .65rem;border-radius:9px;border:1px solid var(--line-2);background:var(--surface);color:var(--ink-2);cursor:pointer}
.nav{display:flex;gap:.25rem;overflow-x:auto;scrollbar-width:none}.nav::-webkit-scrollbar{display:none}
.nav a{flex:none;font:500 .7rem/1 var(--f-mono);color:var(--ink-2);text-decoration:none;padding:.42rem .55rem;border-radius:999px;border:1px solid transparent}
.nav a.part{background:var(--ink);color:var(--bg);margin:0 0 0 .5rem;padding:.42rem .65rem;border-radius:999px}
.nav a:hover{border-color:var(--line-2)}.nav a.on{border-color:var(--teal);color:var(--teal-ink)}
mark{background:var(--mark);color:inherit;border-radius:3px;padding:0 .1em}
.hide{display:none!important}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.86);display:grid;place-items:center;z-index:50;cursor:zoom-out;padding:2vh 2vw}
.lb img{max-width:100%;max-height:96vh;border-radius:8px}
@media print{.bar{display:none}.q,.say,.call{break-inside:avoid}body{font-size:.92rem}}
"""

JS = r"""
const q=document.getElementById('q'),n=document.getElementById('n');
const units=[...document.querySelectorAll('.q, tbody tr, section > p, section > ul, section > ol, section > .say, section > .call')];
function clear(){document.querySelectorAll('mark').forEach(m=>m.replaceWith(m.textContent));document.querySelectorAll('section,.part').forEach(s=>s.normalize())}
function hl(el,re){const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);const ns=[];while(w.nextNode())ns.push(w.currentNode);
ns.forEach(t=>{if(!re.test(t.nodeValue))return;re.lastIndex=0;const f=document.createDocumentFragment();let s=t.nodeValue,last=0,m;
while((m=re.exec(s))){f.append(s.slice(last,m.index));const k=document.createElement('mark');k.textContent=m[0];f.append(k);last=m.index+m[0].length}
f.append(s.slice(last));t.replaceWith(f)})}
let tmr;q.addEventListener('input',()=>{clearTimeout(tmr);tmr=setTimeout(run,160)});
function run(){clear();const v=q.value.trim();document.querySelectorAll('.hide').forEach(e=>e.classList.remove('hide'));
if(v.length<2){n.textContent='';return}
const words=v.toLowerCase().split(/\s+/).filter(Boolean);let c=0;
units.forEach(u=>{const t=u.textContent.toLowerCase();const ok=words.every(w=>t.includes(w));if(!ok)u.classList.add('hide');else c++});
document.querySelectorAll('.tw').forEach(t=>{if(!t.querySelector('tbody tr:not(.hide)'))t.classList.add('hide')});
document.querySelectorAll('section').forEach(s=>{const vis=s.querySelector('.q:not(.hide), tbody tr:not(.hide), :scope > p:not(.hide), :scope > ul:not(.hide), :scope > ol:not(.hide), :scope > .say:not(.hide), :scope > .call:not(.hide)');
if(!vis)s.classList.add('hide');else s.querySelectorAll(':scope > .shot, :scope > h3, :scope > .onscreen, :scope > .tw').forEach(x=>{if(x.classList.contains('tw'))return;x.classList.add('hide')})});
document.querySelectorAll('.part').forEach(p=>p.classList.add('hide'));
const re=new RegExp(words.map(w=>w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|'),'gi');
document.querySelectorAll('section:not(.hide)').forEach(s=>hl(s,re));n.textContent=c+' match'+(c==1?'':'es')}
document.getElementById('x').onclick=()=>{q.value='';run();q.focus()};
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus()}
if(e.key==='Escape'){q.value='';run();q.blur()}});
document.getElementById('qs').onclick=()=>{q.value='';run();const on=document.body.classList.toggle('qonly');
document.getElementById('qs').textContent=on?'Show everything':'Questions only';
document.querySelectorAll('section').forEach(s=>{[...s.children].forEach(ch=>{if(on&&!ch.classList.contains('q')&&ch.tagName!=='H2'&&ch.tagName!=='H3')ch.classList.add('hide');else if(!on)ch.classList.remove('hide')})})};
const links=[...document.querySelectorAll('.nav a')];const obs=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id))}})},{rootMargin:'-20% 0px -70% 0px'});
document.querySelectorAll('section[id]').forEach(s=>obs.observe(s));
document.querySelectorAll('.zoom').forEach(a=>a.onclick=e=>{e.preventDefault();const d=document.createElement('div');d.className='lb';d.innerHTML='<img src="'+a.querySelector('img').src+'">';d.onclick=()=>d.remove();document.body.append(d)});
"""


def build() -> None:
    body, nav = convert(SRC.read_text(encoding="utf-8"))

    def short(t: str) -> str:
        return re.sub(r"^Part ([ABC]) — ", r"\1 · ", t).split(":")[0]
    links = "".join(f"<a class='{'part' if k == 'part' else ''}' href='#{sid}'>{html.escape(short(t))}</a>"
                    for k, t, sid in nav)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Briefing · SlopeSense for APSAC</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Sora:wght@600;700&display=swap">
<style>{CSS}</style></head>
<body>
<div class="bar"><div class="bar-in">
<div class="row1"><input id="q" type="search" placeholder="Search every answer, table row and figure  ( / )" autocomplete="off">
<span id="n"></span><button class="btn" id="x">Clear</button><button class="btn" id="qs">Questions only</button></div>
<nav class="nav">{links}</nav></div></div>
<main class="wrap">
{body}
</main>
<script>{JS}</script>
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(page) / 1e6:.2f} MB, {len(nav)} sections, "
          f"{body.count(chr(39) + 'q' + chr(39))} questions, "
          f"{sum(1 for v in PICTURES.values() for n, _ in v if (SHOTS / f'{n}.webp').exists())} pictures")


if __name__ == "__main__":
    build()
