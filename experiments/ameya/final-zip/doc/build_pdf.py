"""Documentation_template.md -> Documentation_template.pdf (A4, report style).

CommonMark via markdown-it (2-space nested lists render as on GitHub), GitHub-style heading ids so the contents
links match GitHub's, printed by headless Chrome, page numbers stamped with PyMuPDF.
Layout: a plain technical-report look (serif body, justified with hyphenation, about 80 characters per line,
generous space between paragraphs, ruled tables without grids, numbered captions), no coloured boxes.
"""
import re
import subprocess
import sys
from pathlib import Path

import fitz  # PyMuPDF
from markdown_it import MarkdownIt

HERE = Path(__file__).parent
MD, HTML, PDF = HERE / "Documentation_template.md", HERE / "Documentation_template.html", HERE / "Documentation_template.pdf"
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]

CSS = """
@page { size: A4; margin: 20mm 22mm 20mm 22mm; }
html { font-size: 11.5pt; }
body { font-family: "Times New Roman", Times, serif; line-height: 1.38; color: #111; margin: 0;
       text-align: justify; hyphens: auto; -webkit-hyphens: auto; }
h1 { font-size: 17pt; font-weight: 700; text-align: center; margin: 0 0 10pt; line-height: 1.25; }
p.meta { text-align: center; margin: 0 0 18pt; line-height: 1.6; }
h2 { font-size: 14pt; font-weight: 700; margin: 24pt 0 9pt; break-after: avoid; page-break-after: avoid; }
h3 { font-size: 12pt; font-weight: 700; margin: 16pt 0 7pt; break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 7.5pt; orphans: 3; widows: 3; }
strong { font-weight: 700; color: #111; }
ul, ol { margin: 0 0 10pt; padding-left: 20pt; }
li { margin: 0 0 3pt; }
ol > li { margin: 0 0 8pt; }
ul.toc { list-style: none; padding: 0; margin: 0 0 14pt; text-align: left; columns: 2; column-gap: 24pt; }
ul.toc li { margin: 0 0 2pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 14pt; font-size: 9.8pt; line-height: 1.35;
        border-top: 1.4px solid #111; border-bottom: 1.4px solid #111; text-align: left; }
tr { break-inside: avoid; page-break-inside: avoid; }
thead { display: table-header-group; }
th { font-weight: 700; border-bottom: 0.8px solid #111; padding: 5pt 8pt 4pt; vertical-align: bottom; }
td { padding: 4pt 8pt; vertical-align: top; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9.3pt; }
p.figure { text-align: center; margin: 8pt 0 4pt; break-inside: avoid; break-after: avoid; page-break-after: avoid; }
p.figure img { width: 90%; }
p.caption { font-size: 10pt; margin: 0 0 14pt; text-align: left; }
p.caption.fig { text-align: center; }
p.caption.tab { margin: 10pt 0 4pt; break-after: avoid; page-break-after: avoid; }
hr { display: none; }
a { color: #111; text-decoration: none; }
"""


def gh_slug(text: str) -> str:
    """GitHub's heading anchor: lower-case, drop punctuation except '-' and '_', each space becomes '-'."""
    t = re.sub(r"<[^>]+>", "", text).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def to_html(md_text: str) -> str:
    md = MarkdownIt("commonmark", {"html": False, "typographer": False}).enable("table")
    tokens = md.parse(md_text)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            tok.attrSet("id", gh_slug(tokens[i + 1].content))
    body = md.renderer.render(tokens, md.options, {})
    body = re.sub(r"(</h1>\s*)<p>", r'\1<p class="meta">', body, count=1)
    body = re.sub(r"<p><img ", '<p class="figure"><img ', body)
    body = re.sub(r"<p><strong>Figure", '<p class="caption fig"><strong>Figure', body)
    body = re.sub(r"<p><strong>Table", '<p class="caption tab"><strong>Table', body)
    body = re.sub(r'(<h3 id="contents">Contents</h3>\s*)<ul>', r'\1<ul class="toc">', body)
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Grenuke: Business Entity Resolution" \
           f"</title><style>{CSS}</style></head><body>{body}</body></html>"


def main() -> None:
    HTML.write_text(to_html(MD.read_text(encoding="utf-8")), encoding="utf-8")
    chrome = next(p for p in CHROME if Path(p).exists())
    raw = HERE / "_raw.pdf"
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--generate-pdf-document-outline", f"--print-to-pdf={raw}", HTML.resolve().as_uri()]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    doc = fitz.open(raw)
    n = doc.page_count
    for i, page in enumerate(doc, start=1):
        w, h = page.rect.width, page.rect.height
        label = f"{i}"
        tw = fitz.get_text_length(label, fontname="tiro", fontsize=9.5)
        page.insert_text(((w - tw) / 2, h - 28), label, fontname="tiro", fontsize=9.5, color=(0.25, 0.25, 0.25))
    doc.save(PDF, garbage=3, deflate=True)
    doc.close()
    raw.unlink()
    print(f"{PDF.name}: {n} pages, {PDF.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
