#!/usr/bin/env python3
"""Compile the knowledge base into one textbook PDF: the Grenuke study book.

    python scripts/build_book.py            # -> work/book/Grenuke_Study_Book.pdf (git-ignored)

Markdown (CommonMark + tables, raw HTML for the answer blocks) is rendered with markdown-it, maths with KaTeX
(loaded from cdn.jsdelivr.net), printed by headless Chrome, then PyMuPDF adds page numbers, running heads and
bookmarks. Two passes: the second fills the contents page numbers measured in the first.
Cross-references between included pages become links inside the book; links to other repo files point to GitHub.
"""
from __future__ import annotations

import datetime as dt
import html
import re
import subprocess
import sys
from pathlib import Path

import fitz  # PyMuPDF
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"
OUT = ROOT / "work" / "book"
REPO_URL = "https://github.com/AmeyaBorkar/Grenuke/blob/main/"
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
          "/usr/bin/google-chrome", "/usr/bin/chromium"]
FONT = Path(r"C:\Windows\Fonts\times.ttf")

F = "theory/foundations/"
PARTS = [
    ("Part I", "Foundations", "The theory from scratch, from reading the data to production ML.",
     [F + "README.md"] + sorted(p.relative_to(KB).as_posix() for p in (KB / F).glob("F*.md"))),
    ("Part II", "Advanced theory", "The techniques behind our pipeline, tied to our numbers, with jury questions.",
     ["theory/README.md"] + sorted(p.relative_to(KB).as_posix() for p in (KB / "theory").glob("[0-9][0-9]-*.md"))),
    ("Part III", "Our solution", "What we built, why, and how each part works.",
     ["story.md", "components/README.md"] + [f"components/{n}.md" for n in (
         "data-and-problem", "evaluation", "normalisation", "blocking", "features", "model-stages", "cross-encoders",
         "decision-layer", "rules", "france", "llm-recheck", "submission-strategy", "packaging", "process-and-infra")]),
    ("Part IV", "For the finale", "The questions to expect, the lessons, and the numbers to quote.",
     ["qa.md", "lessons.md", "numbers.md"]),
    ("Appendix", "Glossary", "Every term used in this book.", ["theory/glossary.md"]),
]

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
html { font-size: 10.8pt; }
body { font-family: "Times New Roman", Times, serif; line-height: 1.42; color: #111; margin: 0;
       text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
.chapter { break-before: page; }
.part { break-before: page; height: 230mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.part .label { font-size: 15pt; text-transform: uppercase; color: #555; }
.part .title { font-size: 30pt; font-weight: 700; margin: 8pt 0 14pt; }
.part .blurb { font-size: 12pt; color: #333; }
.title-page { height: 245mm; display: flex; flex-direction: column; justify-content: center; text-align: center; }
.title-page .t1 { font-size: 34pt; font-weight: 700; line-height: 1.15; }
.title-page .t2 { font-size: 15pt; margin: 14pt 0 40pt; color: #333; }
.title-page .t3 { font-size: 12.5pt; line-height: 1.7; }
.title-page .t4 { font-size: 10pt; color: #555; margin-top: 50pt; }
h1 { font-size: 21pt; font-weight: 700; margin: 0 0 14pt; line-height: 1.2; text-align: left; }
h1 .chapno { display: block; font-size: 11pt; font-weight: 400; text-transform: uppercase; color: #666; margin-bottom: 6pt; }
h2 { font-size: 14.5pt; font-weight: 700; margin: 18pt 0 7pt; break-after: avoid; text-align: left; }
h3 { font-size: 12.2pt; font-weight: 700; margin: 14pt 0 6pt; break-after: avoid; text-align: left; }
h4, h5 { font-size: 11pt; font-weight: 700; margin: 10pt 0 5pt; break-after: avoid; }
p { margin: 0 0 7pt; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 9pt; padding-left: 20pt; }
li { margin: 0 0 3pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 12pt; font-size: 8.9pt; line-height: 1.3;
        border-top: 1.3px solid #111; border-bottom: 1.3px solid #111; text-align: left; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
th { font-weight: 700; border-bottom: 0.8px solid #111; padding: 4pt 5pt 3pt; vertical-align: bottom; }
td { padding: 3pt 5pt; vertical-align: top; border-top: 0.3px solid #ccc; overflow-wrap: break-word; }
td:first-child, th:first-child { min-width: 62pt; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 8.8pt; overflow-wrap: anywhere; }
pre { background: #f5f5f5; padding: 6pt 8pt; font-size: 8.5pt; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { font-size: 8.5pt; }
blockquote { margin: 6pt 0 10pt; padding: 2pt 0 2pt 10pt; border-left: 2px solid #999; color: #333; }
.answer { margin: 4pt 0 10pt 12pt; padding: 5pt 9pt; background: #f4f4f4; border-radius: 3pt; font-size: 10pt; }
.answer .alabel { font-weight: 700; font-size: 9.5pt; color: #444; margin-bottom: 3pt; }
a { color: #123c7a; text-decoration: none; }
hr { border: 0; border-top: 0.6px solid #999; margin: 12pt 0; }
.toc h1 { margin-bottom: 18pt; }
.toc .tpart { font-weight: 700; font-size: 12pt; margin: 12pt 0 4pt; display: flex; }
.toc .tch { display: flex; margin: 0 0 2pt 14pt; font-size: 10.5pt; }
.toc .fill { flex: 1; border-bottom: 1px dotted #888; margin: 0 4pt 3pt; }
.toc .pg { width: 26pt; text-align: right; }
.katex { font-size: 1.02em; }
.katex-display { margin: 6pt 0; overflow-wrap: normal; }
"""

KATEX = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
         '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'
         '<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>'
         '<script>document.addEventListener("DOMContentLoaded",function(){renderMathInElement(document.body,'
         '{delimiters:[{left:"\\\\[",right:"\\\\]",display:true},{left:"\\\\(",right:"\\\\)",display:false}],'
         'throwOnError:false});});</script>')


def slug(text: str) -> str:
    t = re.sub(r"<[^>]+>", "", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", t).replace(" ", "-")


def chap_id(rel: str) -> str:
    return "c-" + re.sub(r"[^a-z0-9]+", "-", rel.lower().removesuffix(".md")).strip("-")


def protect_math(text: str):
    store = []

    def keep(m, display):
        store.append(("\\[" if display else "\\(") + html.escape(m.group(1)) + ("\\]" if display else "\\)"))
        return f"MATHSPAN{len(store) - 1}X"
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: keep(m, True), text, flags=re.S)
    text = re.sub(r"(?<![\\$\w])\$(?=\S)([^$\n]+?)(?<=\S)\$(?![\d$])", lambda m: keep(m, False), text)
    return text, store


def prep_answers(text: str) -> str:
    text = re.sub(r"<details>\s*<summary>(.*?)</summary>", r'<div class="answer"><p class="alabel">\1</p>\n\n', text)
    return re.sub(r"\s*</details>", "\n\n</div>\n", text)


def render_chapter(rel: str, number: str, included: set[str]) -> tuple[str, str]:
    src = (KB / rel).read_text(encoding="utf-8")
    src, maths = protect_math(prep_answers(src))
    md = MarkdownIt("commonmark", {"html": True, "typographer": False}).enable("table")
    tokens = md.parse(src)
    cid, base = chap_id(rel), (KB / rel).parent
    title = "?"
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            text = tokens[i + 1].content
            if tok.tag == "h1" and title == "?":
                title = re.sub(r"[*`]", "", text)
                tok.attrSet("id", cid)
            else:
                tok.attrSet("id", f"{cid}--{slug(text)}")
        if tok.type == "inline" and tok.children:
            for ch in tok.children:
                if ch.type == "link_open":
                    ch.attrSet("href", fix_link(ch.attrGet("href") or "", base, cid, included))
                if ch.type == "image":
                    s = ch.attrGet("src") or ""
                    if not s.startswith(("http", "data:")):
                        ch.attrSet("src", (base / s).resolve().as_uri())
    body = md.renderer.render(tokens, md.options, {})
    body = re.sub(r"MATHSPAN(\d+)X", lambda m: maths[int(m.group(1))], body)
    body = re.sub(r"(<h1 id=\"[^\"]+\">)", rf'\1<span class="chapno">{number}</span>', body, count=1)
    return title, f'<section class="chapter">{body}</section>'


def fix_link(href: str, base: Path, cid: str, included: set[str]) -> str:
    if href.startswith(("http://", "https://", "mailto:")):
        return href
    if href.startswith("#"):
        return f"#{cid}--{href[1:]}"
    path, _, frag = href.partition("#")
    target = (base / path).resolve()
    try:
        rel_kb = target.relative_to(KB.resolve()).as_posix()
    except ValueError:
        rel_kb = None
    if rel_kb in included:
        return f"#{chap_id(rel_kb)}" + (f"--{frag}" if frag else "")
    if rel_kb and target.is_dir() and f"{rel_kb}/README.md" in included:
        return f"#{chap_id(rel_kb + '/README.md')}"
    try:
        return REPO_URL + target.relative_to(ROOT.resolve()).as_posix() + (f"#{frag}" if frag else "")
    except ValueError:
        return href


def build_html(pages: dict[str, int] | None, commit: str) -> tuple[str, list]:
    included = {rel for _, _, _, rels in PARTS for rel in rels}
    today = dt.date.today().strftime("%d %B %Y")
    parts_html, toc, outline = [], [], []
    for pi, (plabel, ptitle, blurb, rels) in enumerate(PARTS):
        pid = f"part-{pi}"
        parts_html.append(f'<section class="part" id="{pid}"><div class="label">{plabel}</div>'
                          f'<div class="title">{ptitle}</div><div class="blurb">{blurb}</div></section>')
        toc.append(("part", f"{plabel}. {ptitle}", pid))
        outline.append((1, f"{plabel}. {ptitle}", pid, f"{plabel} {ptitle}"))
        for ci, rel in enumerate(rels, 1):
            number = f"{plabel} · chapter {ci}" if plabel != "Appendix" else "Appendix"
            title, sec = render_chapter(rel, number, included)
            parts_html.append(sec)
            toc.append(("ch", title, chap_id(rel)))
            outline.append((2, title, chap_id(rel), number))

    def pg(anchor):
        return str(pages.get(anchor, "")) if pages else "000"
    toc_html = ['<section class="toc chapter" id="toc"><h1>Contents</h1>']
    for kind, title, anchor in toc:
        cls = "tpart" if kind == "part" else "tch"
        toc_html.append(f'<div class="{cls}"><a href="#{anchor}">{html.escape(title)}</a><span class="fill"></span>'
                        f'<span class="pg">{pg(anchor)}</span></div>')
    toc_html.append("</section>")
    preface = f"""<section class="chapter" id="preface"><h1>How to use this book</h1>
<p>This book compiles team Grenuke's knowledge base for the Amazon ML Challenge 2026 Grand Finale. It has four parts.</p>
<ul><li><strong>Part I, Foundations,</strong> teaches the theory from scratch. Its first chapter is the curriculum: priority tiers, study paths for each Q&amp;A lead, and a self-assessment checklist.</li>
<li><strong>Part II, Advanced theory,</strong> goes deeper into each technique we used, ties it to our numbers, and ends every chapter with jury questions and a self-test.</li>
<li><strong>Part III, Our solution,</strong> tells the story of the project and explains each pipeline component: how it works, why it was built that way, its alternatives, its limits and how it scales.</li>
<li><strong>Part IV, For the finale,</strong> holds the Q&amp;A bank, the lessons and the fact sheet. The fact sheet marks the numbers to quote with ★ and lists the numbers not to quote.</li></ul>
<p><strong>Conventions.</strong> Times are IST. Every number carries an evidence level: <strong>M</strong> measured, <strong>E</strong> estimated, <strong>R</strong> reported, <strong>U</strong> uncertain. Every score names its evaluation:</p>
<ul><li>the <strong>local holdout</strong>: 25% of the labelled US/India S1, with no France;</li>
<li>the <strong>public leaderboard</strong>;</li>
<li>the <strong>private leaderboard</strong>, which publishes rankings only.</li></ul>
<p>Answers to the exercises appear in grey boxes after each question. Cover them while you test yourself.</p>
<p><strong>Not in the book.</strong> The full ledgers stay in the repository under <code>knowledge/</code>:</p>
<ul><li>247 decision records;</li>
<li>329 experiments;</li>
<li>the timeline;</li>
<li>failures, conflicts and sources;</li>
<li>each member's own capture.</li></ul>
<p>Links into them point to GitHub.</p></section>"""
    title = f"""<section class="title-page"><div class="t1">Business Entity Resolution<br>at Scale</div>
<div class="t2">The Grenuke study book: theory, methods and our solution</div>
<div class="t3">Team Grenuke<br>Ameya Borkar · Aarush Bakshi · Sachi Dhoka<br><br>Amazon ML Challenge 2026 · Grand Finale, 7 October 2026</div>
<div class="t4">Compiled from the knowledge base at commit {commit} on {today}.</div></section>"""
    doc = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Grenuke Study Book</title>{KATEX}"
           f"<style>{CSS}</style></head><body>{title}{''.join(toc_html)}{preface}{''.join(parts_html)}</body></html>")
    return doc, outline


def print_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = next(p for p in CHROME if Path(p).exists())
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--virtual-time-budget=90000", "--run-all-compositor-stages-before-draw", f"--print-to-pdf={pdf_path}",
           html_path.resolve().as_uri()]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)


def anchor_pages(pdf_path: Path, outline: list) -> dict[str, int]:
    """Find each part and chapter start page by its heading text on the page tops."""
    def norm(s: str) -> str:
        return " ".join(re.sub(r"[^\w ]+", " ", s.lower()).split())
    doc = fitz.open(pdf_path)
    tops = [norm(p.get_text("text"))[:260] for p in doc]
    # Skip the title page and the contents: start at the preface.
    start = next((i for i, t in enumerate(tops) if t.startswith("how to use this book")), 0)
    pages = {}
    for level, title, anchor, prefix in outline:
        key, pre = norm(title)[:45], norm(prefix)
        for i in range(start, len(tops)):
            if tops[i].startswith(pre) and key in tops[i]:
                pages[anchor] = i + 1
                start = i
                break
    doc.close()
    return pages


def finish(raw: Path, final: Path, outline: list, pages: dict[str, int]) -> int:
    doc = fitz.open(raw)
    n = doc.page_count
    starts = sorted((pages[a], t) for lvl, t, a, _ in outline if lvl == 2 and a in pages)
    part_pages = {pages[a] for lvl, t, a, _ in outline if lvl == 1 and a in pages}
    font_kw = {"fontname": "TNR", "fontfile": str(FONT)} if FONT.exists() else {"fontname": "tiro"}
    for i, page in enumerate(doc, start=1):
        if i <= 2 or i in part_pages:
            continue
        w, h = page.rect.width, page.rect.height
        page.insert_text((w / 2 - 6, h - 26), str(i), fontsize=9, color=(0.3, 0.3, 0.3), **font_kw)
        head = next((t for p, t in reversed(starts) if p <= i), "")
        if head and not any(p == i for p, _ in starts):
            head = head if len(head) < 90 else head[:87] + "…"
            page.insert_text((57, 38), head, fontsize=8.5, color=(0.4, 0.4, 0.4), **font_kw)
    toc = [[1, "Contents", 2]] + [[lvl, t, pages[a]] for lvl, t, a, _ in outline if a in pages]
    doc.set_toc(toc)
    doc.save(final, garbage=3, deflate=True)
    doc.close()
    return n


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    html_path, raw = OUT / "book.html", OUT / "_raw.pdf"
    doc, outline = build_html(None, commit)
    html_path.write_text(doc, encoding="utf-8")
    print_pdf(html_path, raw)
    pages = anchor_pages(raw, outline)
    missing = [t for _, t, a, _ in outline if a not in pages]
    doc, outline = build_html(pages, commit)
    html_path.write_text(doc, encoding="utf-8")
    print_pdf(html_path, raw)
    pages2 = anchor_pages(raw, outline)
    final = OUT / "Grenuke_Study_Book.pdf"
    n = finish(raw, final, outline, pages2)
    raw.unlink()
    shifted = sum(1 for a in pages if pages2.get(a) != pages[a])
    print(f"{final}: {n} pages, {final.stat().st_size / 1e6:.1f} MB; chapters located {len(pages2)}/{len(outline)};"
          f" contents shift after pass 2: {shifted}; not located: {missing[:5]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
