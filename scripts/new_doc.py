#!/usr/bin/env python3
"""Create team coordination documents from their templates, with IST timestamps and the agreed names.

Usage:
    python scripts/new_doc.py handover   --member ameya --topic blocking-v1
    python scripts/new_doc.py status     --member ameya            # add --force to reset your own status file
    python scripts/new_doc.py decision   --member ameya --topic plan-selection
    python scripts/new_doc.py submission --member ameya --num 1
    python scripts/new_doc.py person     --member bakshi           # knowledge/people/bakshi/ from the templates

It prints the created path. It never overwrites an existing file, except `status` with --force.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# kind -> (template path, output path pattern)
KINDS = {
    "handover": ("docs/handover/TEMPLATE.md", "docs/handover/{date}_{hm}_{member}_{topic}.md"),
    "status": ("docs/status/TEMPLATE.md", "docs/status/{member}.md"),
    "decision": ("docs/decisions/TEMPLATE.md", "docs/decisions/{date}_{hm}_{topic}.md"),
    "submission": ("submissions/records/TEMPLATE.md", "submissions/records/{date}_sub{num}.md"),
    "person": ("knowledge/templates/person", "knowledge/people/{member}"),  # a folder: knowledge/CAPTURE.md
}


def new_person(member: str) -> int:
    """Create knowledge/people/<member>/ from the person templates; never overwrite an existing file."""
    src, dst = ROOT / "knowledge/templates/person", ROOT / "knowledge/people" / member
    dst.mkdir(parents=True, exist_ok=True)
    for tpl in sorted(src.glob("*.md")):
        out = dst / tpl.name
        if out.exists():
            print(f"exists, kept: {out.relative_to(ROOT).as_posix()}")
            continue
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(tpl.read_text(encoding="utf-8").replace("{{MEMBER}}", member))
        print(out.relative_to(ROOT).as_posix())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=sorted(KINDS))
    parser.add_argument("--member", required=True, help="your lowercase member name (branch prefix)")
    parser.add_argument("--topic", help="kebab-case topic (handover, decision)")
    parser.add_argument("--num", help="submission number of the day (submission)")
    parser.add_argument("--force", action="store_true", help="overwrite your own status file")
    args = parser.parse_args()

    member = args.member.strip().lower()
    if not SLUG.match(member):
        parser.error("--member must be lowercase letters/digits/hyphens, e.g. 'ameya'")
    if args.kind == "person":
        return new_person(member)
    topic = (args.topic or "").strip().lower()
    if args.kind in ("handover", "decision"):
        if not topic or not SLUG.match(topic):
            parser.error("--topic is required and must be kebab-case, e.g. 'blocking-v1'")
    num = ""
    if args.kind == "submission":
        if not args.num or not args.num.isdigit():
            parser.error("--num is required for submission records, e.g. --num 1")
        num = f"{int(args.num):02d}"

    now = dt.datetime.now(IST)
    template_rel, out_pattern = KINDS[args.kind]
    out = ROOT / out_pattern.format(
        date=now.strftime("%Y-%m-%d"), hm=now.strftime("%H%M"), member=member, topic=topic, num=num
    )
    if out.exists() and not (args.kind == "status" and args.force):
        print(f"refusing to overwrite existing file: {out.relative_to(ROOT).as_posix()}", file=sys.stderr)
        return 1

    text = (ROOT / template_rel).read_text(encoding="utf-8")
    for key, value in {
        "{{MEMBER}}": member,
        "{{TOPIC}}": topic,
        "{{DATETIME}}": now.strftime("%Y-%m-%d %H:%M"),
        "{{DATE}}": now.strftime("%Y-%m-%d"),
        "{{NUM}}": num,
    }.items():
        text = text.replace(key, value)

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(out.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
