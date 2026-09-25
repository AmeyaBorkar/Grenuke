#!/usr/bin/env python3
"""Export a Markdown document (e.g. a plan) to a clean A4 PDF using a headless Chromium browser.

Usage:
    python scripts/md_to_pdf.py plans/<member>/PLAN.md                  # -> plans/<member>/PLAN.pdf
    python scripts/md_to_pdf.py plans/<member>/PLAN.md -o out.pdf --footer "Grenuke - Plan B"

Needs: markdown-it-py (or python-markdown as a fallback) and Chrome, Edge or Chromium.
Set BROWSER_PATH to point at a specific browser executable.
Headless Chromium handles every script in our data (Devanagari, Tamil, accents) and prints tables well.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CSS = """
@page { size: A4; margin: 16mm 15mm 17mm 15mm;
  @bottom-left  { content: "%(footer)s"; font: 7.5pt "Segoe UI", Arial, sans-serif; color: #8a94a3; }
  @bottom-right { content: "Page " counter(page) " / " counter(pages); font: 7.5pt "Segoe UI", Arial, sans-serif; color: #8a94a3; } }
:root { --ink:#1b2430; --muted:#5b6675; --accent:#e47911; --rule:#d9dee5; --soft:#f4f6f9; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", "Nirmala UI", "Segoe UI Symbol", "Helvetica Neue", Arial, "Noto Sans", sans-serif;
       font-size: 9.5pt; line-height: 1.42; color: var(--ink); margin: 0; }
h1 { font-size: 19pt; line-height: 1.2; margin: 0 0 6pt; padding-bottom: 6pt; border-bottom: 3px solid var(--accent); }
h2 { font-size: 13pt; margin: 15pt 0 5pt; padding-bottom: 3pt; border-bottom: 1px solid var(--rule); break-after: avoid; }
h3 { font-size: 10.8pt; margin: 11pt 0 4pt; color: #24344d; break-after: avoid; }
h4 { font-size: 9.8pt; margin: 9pt 0 3pt; break-after: avoid; }
p { margin: 4pt 0; orphans: 3; widows: 3; }
ul, ol { padding-left: 15pt; margin: 3pt 0 5pt; }
li { margin: 1.5pt 0; }
li > ul, li > ol { margin: 1pt 0 2pt; }
table { border-collapse: collapse; width: 100%%; margin: 5pt 0 9pt; font-size: 8.5pt; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td { border: 1px solid var(--rule); padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: var(--soft); font-weight: 600; }
code { font-family: Consolas, "Cascadia Mono", "DejaVu Sans Mono", monospace; font-size: 8.4pt;
       background: var(--soft); padding: 0 2pt; border-radius: 2px; }
pre { background: var(--soft); border: 1px solid var(--rule); border-radius: 4px; padding: 7pt 9pt;
      font-size: 7.7pt; line-height: 1.32; white-space: pre; overflow: hidden; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
hr { border: none; border-top: 1px solid var(--rule); margin: 9pt 0; }
blockquote { border-left: 3px solid var(--accent); margin: 6pt 0; padding: 2pt 8pt; color: var(--muted); }
a { color: #1a5fb4; text-decoration: none; }
"""


def render_markdown(text: str) -> str:
    try:
        from markdown_it import MarkdownIt

        return MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"]).render(text)
    except ImportError:
        import markdown

        # python-markdown needs 4-space nested lists; our docs use 2-space nesting.
        text = re.sub(r"(?m)^((?:  )+)(?=[-*] |\d+\. )", lambda m: m.group(1) * 2, text)
        return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def find_browser() -> str:
    env = os.environ.get("BROWSER_PATH")
    candidates = [env] if env else []
    candidates += [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Edge/Chromium found. Set BROWSER_PATH to the browser executable.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("-o", "--output", type=Path, help="output PDF (default: next to the input)")
    ap.add_argument("--footer", default="", help="footer text (default: file name)")
    args = ap.parse_args()

    src = args.markdown.resolve()
    out = (args.output or src.with_suffix(".pdf")).resolve()
    text = src.read_text(encoding="utf-8")
    title_match = re.search(r"(?m)^#\s+(.+)$", text)
    title = title_match.group(1).strip() if title_match else src.stem
    footer = (args.footer or src.name).replace("\\", "\\\\").replace('"', '\\"')

    body = render_markdown(text)
    page = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{html.escape(title)}</title><style>{CSS % {'footer': footer}}</style></head>"
        f"<body>{body}</body></html>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "doc.html"
        html_path.write_text(page, encoding="utf-8")
        cmd = [
            find_browser(),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--virtual-time-budget=5000",
            f"--print-to-pdf={out}",
            html_path.as_uri(),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    if not out.exists() or out.stat().st_size == 0:
        sys.exit("PDF was not produced")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
