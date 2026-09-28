"""Documentation_template.md -> Documentation_template.pdf (A4, 11 pt, ~80 characters per line, contents links,
page numbers).

CommonMark via markdown-it (2-space nested lists render as on GitHub), GitHub-style heading ids so the contents
links match GitHub's, printed by headless Chrome, page numbers stamped with PyMuPDF.
Styling follows the readability guidance we used: a 45-80 character measure, 1.5 line spacing, white space between
groups, bold keywords as a scannable skeleton, a lead sentence per section, captions on every figure and table.
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
@page { size: A4; margin: 17mm 24mm 18mm 24mm; }
html { font-size: 11pt; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; line-height: 1.5; color: #1f2329; margin: 0; }
h1 { font-size: 19pt; color: #0b2e59; margin: 0 0 8pt; line-height: 1.2; }
h2 { font-size: 15pt; color: #0b2e59; border-bottom: 1.5px solid #0b4f9c; padding-bottom: 3pt; margin: 22pt 0 6pt;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 12pt; color: #0b2e59; margin: 14pt 0 4pt; break-after: avoid; page-break-after: avoid; }
p { margin: 0 0 7pt; orphans: 3; widows: 3; }
strong { color: #0b3d7a; }
em { color: inherit; }
ul, ol { margin: 0 0 7pt; padding-left: 17pt; }
li { margin: 1.5pt 0; }
ol > li { margin: 0 0 6pt; }
p.lead { font-size: 11pt; color: #34495e; border-left: 3px solid #9dbbe0; padding: 1pt 0 1pt 9pt; margin: 2pt 0 10pt; }
p.lead strong { color: #34495e; }
blockquote { background: #eef4fb; border-left: 4px solid #0b4f9c; margin: 8pt 0 12pt; padding: 7pt 12pt;
             border-radius: 3pt; }
blockquote p { margin: 0; }
ul.toc { columns: 2; column-gap: 18pt; list-style: none; padding: 0; margin: 2pt 0 8pt; font-size: 10.5pt; }
ul.toc li { margin: 0 0 3pt; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 2pt 0 12pt; font-size: 9.8pt; line-height: 1.4; }
tr { break-inside: avoid; page-break-inside: avoid; }
thead { display: table-header-group; }
th { background: #e6edf7; text-align: left; font-weight: 600; color: #0b2e59; }
th, td { border: 1px solid #c5cfdc; padding: 4pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #f7f9fc; }
td strong { color: #0b2e59; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9.3pt; background: #eef1f5; padding: 0 2pt;
       border-radius: 2pt; }
p.figure { text-align: center; margin: 4pt 0 2pt; break-inside: avoid; break-after: avoid; page-break-after: avoid; }
p.figure img { width: 90%; }
p.caption { font-size: 9.5pt; color: #46505b; margin: 0 0 12pt; }
p.caption.fig { text-align: center; margin-bottom: 6pt; }
p.caption.tab { margin: 8pt 0 3pt; break-after: avoid; page-break-after: avoid; }
p.caption em { font-style: italic; }
hr { display: none; }
a { color: #0b4f9c; text-decoration: none; }
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
    body = re.sub(r"<p><img ", '<p class="figure"><img ', body)
    body = re.sub(r"<p><em>Figure", '<p class="caption fig"><em>Figure', body)
    body = re.sub(r"<p><em>Table", '<p class="caption tab"><em>Table', body)
    body = re.sub(r"(</h2>\s*)<p><em>", r'\1<p class="lead"><em>', body)
    body = re.sub(r'(<h3 id="contents">Contents</h3>\s*)<ul>', r'\1<ul class="toc">', body)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Grenuke: Business Entity Resolution</title>" \
           f"<style>{CSS}</style></head><body>{body}</body></html>"


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
        label = f"Team Grenuke  ·  Business Entity Resolution  ·  page {i} of {n}"
        tw = fitz.get_text_length(label, fontname="helv", fontsize=8.5)
        page.insert_text(((w - tw) / 2, h - 24), label, fontname="helv", fontsize=8.5, color=(0.45, 0.48, 0.52))
    doc.save(PDF, garbage=3, deflate=True)
    doc.close()
    raw.unlink()
    print(f"{PDF.name}: {n} pages, {PDF.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
