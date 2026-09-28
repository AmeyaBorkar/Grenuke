"""Documentation_template.md -> Documentation_template.pdf (A4, 11 pt body, working contents links, page numbers).

CommonMark via markdown-it (2-space nested lists render as on GitHub), GitHub-style heading ids so the contents
links match GitHub's, printed by headless Chrome, page numbers stamped with PyMuPDF.
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
@page { size: A4; margin: 16mm 16mm 17mm 16mm; }
html { font-size: 11pt; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; line-height: 1.45; color: #1b1f24; margin: 0; }
h1 { font-size: 20pt; color: #0b2e59; margin: 0 0 8pt; line-height: 1.2; }
h2 { font-size: 15.5pt; color: #0b2e59; border-bottom: 2px solid #0b4f9c; padding-bottom: 3pt; margin: 20pt 0 8pt;
     break-after: avoid; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #0b2e59; margin: 14pt 0 5pt; break-after: avoid; page-break-after: avoid; }
p { margin: 5pt 0; orphans: 3; widows: 3; }
ul, ol { margin: 3pt 0 6pt; padding-left: 17pt; }
li { margin: 2pt 0; }
li > ul, li > ol { margin: 1pt 0 2pt; }
strong { color: #10151b; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 10pt; }
tr { break-inside: avoid; page-break-inside: avoid; }
thead { display: table-header-group; }
th { background: #e6edf7; text-align: left; font-weight: 600; }
th, td { border: 1px solid #c5cfdc; padding: 3.5pt 6pt; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 9.5pt; background: #eef1f5; padding: 0 2pt;
       border-radius: 2pt; }
pre { background: #eef1f5; padding: 7pt 9pt; border-radius: 4pt; font-size: 9pt; line-height: 1.35;
      white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 9pt; }
p.figure { text-align: center; margin: 10pt 0 2pt; break-inside: avoid; }
p.figure img { max-width: 97%; }
p.caption { text-align: center; font-size: 9.5pt; color: #3d4650; margin: 2pt 0 12pt; }
hr { display: none; }
a { color: #0b4f9c; text-decoration: none; }
.meta { margin-bottom: 4pt; }
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
    body = re.sub(r"<p><em>Figure", '<p class="caption"><em>Figure', body)
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
        page.insert_text(((w - tw) / 2, h - 22), label, fontname="helv", fontsize=8.5, color=(0.45, 0.48, 0.52))
    doc.save(PDF, garbage=3, deflate=True)
    doc.close()
    raw.unlink()
    print(f"{PDF.name}: {n} pages, {PDF.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    sys.exit(main())
