#!/usr/bin/env python3
"""Turn AI-chat transcripts into short, redacted, time-stamped Markdown digests for knowledge capture.

The digests are working material for `knowledge/CAPTURE.md`: you (or your agent) read them and write
the standard records into `knowledge/people/<member>/`. **Never commit a digest or a transcript.**
They stay on your machine (default output: `work/kb_digest/`, git-ignored).

Supported inputs (the format is detected per file):
  - Claude Code session logs: ~/.claude/projects/<project-dir>/*.jsonl (and <session>/subagents/*.jsonl)
  - Codex CLI session logs: ~/.codex/sessions/**/rollout-*.jsonl (best effort)
  - anything else: export it to .md/.txt and give that to your agent directly

Usage:
    python scripts/kb/digest_transcripts.py ~/.claude/projects/<project-dir> --member bakshi
    python scripts/kb/digest_transcripts.py a.jsonl b.jsonl --mode full --max-chars 400000

Modes:
  narrative (default)  user + assistant text, one line per tool call, a short head/tail of each tool result
  full                 the same with long tool results (for finding numbers)
  brief                only the task and the final report of each transcript (for sub-agent logs)

Redaction (always on): IPv4 addresses, ssh ports and user@host, e-mails, phone numbers, API tokens,
private-key blocks and home-directory paths. Check the output before sharing anything anyway.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

REDACTIONS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "<private-key>"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{20,}|"
                r"sk-ant-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9]{24,}|AKIA[0-9A-Z]{16})"), "<token>"),
    (re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)*\.(com|in|org|net|io|edu|ai|dev)\b"), "<email>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip>"),
    (re.compile(r"(ssh\s+(?:-\S+\s+)*)-p\s*\d+"), r"\1-p <port>"),
    (re.compile(r"\b[a-z_][a-z0-9_-]*@<ip>"), "<user>@<ip>"),
    (re.compile(r"\+\d{1,3}[ -]?\d{4,5}[ -]?\d{5}\b"), "<phone>"),
    (re.compile(r"/[a-z]/Users/[^/\s'\"]+"), "~"),
    (re.compile(r"(?i)\b([A-Z]:)?[\\/]+Users[\\/]+[^\\/\s'\"]+"), "~"),
    (re.compile(r"/home/[^/\s'\"]+"), "~"),
]
SYSTEM_BLOCK = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
NOTIFICATION = re.compile(r"<task-notification>.*?<summary>(.*?)</summary>.*?</task-notification>", re.S)
TAG_NOISE = re.compile(r"</?(local-command-caveat|command-message|command-args)>")


def redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def clip(text: str, limit: int) -> str:
    text = text.strip()
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    tail = limit - head
    return f"{text[:head]}\n… [{len(text) - limit} chars omitted] …\n{text[-tail:]}"


def ist(ts: str | None) -> str:
    if not ts:
        return "????-??-?? ??:??"
    try:
        t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return t.astimezone(IST).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16]


def tool_line(name: str, inp: dict, prompt_limit: int) -> str:
    """One readable line for a tool call."""
    def g(k: str, n: int = 300) -> str:
        v = inp.get(k)
        return clip(str(v), n).replace("\n", " ⏎ ") if v not in (None, "") else ""

    if name == "Bash" or name == "PowerShell":
        return f"[{name}] {g('description', 160)} | `{g('command', 500)}`"
    if name in ("Read", "NotebookRead"):
        return f"[Read] {g('file_path')} {g('offset', 20)} {g('limit', 20)}".rstrip()
    if name == "Write":
        return f"[Write] {g('file_path')} ({len(str(inp.get('content', '')))} chars): {g('content', 300)}"
    if name in ("Edit", "MultiEdit"):
        return f"[Edit] {g('file_path')}: `{g('old_string', 160)}` → `{g('new_string', 240)}`"
    if name in ("Grep", "Glob"):
        return f"[{name}] {g('pattern', 200)} in {g('path', 200) or '.'}"
    if name in ("Agent", "Task"):
        return f"[Agent] {g('description', 160)} ({g('subagent_type', 40)}): {g('prompt', prompt_limit)}"
    if name in ("WebSearch", "WebFetch"):
        return f"[{name}] {g('query', 200) or g('url', 300)}"
    return f"[{name}] {clip(json.dumps(inp, ensure_ascii=False), 300)}"


def result_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for item in content or []:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif item.get("type") == "image":
                parts.append("[image]")
    return "\n".join(parts)


def claude_entries(lines, result_limit: int, prompt_limit: int):
    """Yield (ist_time, role, text) from a Claude Code session log."""
    for d in lines:
        kind = d.get("type")
        msg = d.get("message")
        if kind not in ("user", "assistant") or not isinstance(msg, dict) or d.get("isMeta"):
            continue
        when = ist(d.get("timestamp"))
        content = msg.get("content")
        if d.get("isCompactSummary"):
            yield when, "COMPACTION SUMMARY (the tool's own summary of the conversation so far)", result_text(content)
            continue
        if isinstance(content, str):
            if content.lstrip().startswith("<task-notification>"):
                m = NOTIFICATION.search(content)
                yield when, "tool result", "[background notification] " + (m.group(1).strip() if m else "")
                continue
            text = TAG_NOISE.sub("", SYSTEM_BLOCK.sub("", content)).strip()
            if text:
                yield when, kind, text
            continue
        for block in content or []:
            bt = block.get("type")
            if bt == "text":
                text = TAG_NOISE.sub("", SYSTEM_BLOCK.sub("", block.get("text", ""))).strip()
                if text:
                    yield when, kind, text
            elif bt == "thinking" and block.get("thinking", "").strip():
                yield when, "assistant (thinking)", clip(block["thinking"], 1500)
            elif bt == "tool_use":
                yield when, "tool call", tool_line(block.get("name", "?"), block.get("input") or {}, prompt_limit)
            elif bt == "tool_result":
                text = SYSTEM_BLOCK.sub("", result_text(block.get("content")))
                if result_limit > 0 and text.strip():
                    tag = "tool error" if block.get("is_error") else "tool result"
                    yield when, tag, clip(text, result_limit)
            elif bt == "image":
                yield when, kind, "[image]"


def codex_entries(lines, result_limit: int, prompt_limit: int):
    """Yield (ist_time, role, text) from a Codex CLI rollout log (best effort)."""
    for d in lines:
        p = d.get("payload") if isinstance(d.get("payload"), dict) else d
        when = ist(d.get("timestamp"))
        t = p.get("type")
        if t == "message":
            text = "\n".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
            text = SYSTEM_BLOCK.sub("", text).strip()
            if text and not text.startswith("<environment_context>"):
                yield when, p.get("role", "?"), text
        elif t in ("function_call", "custom_tool_call", "local_shell_call"):
            args = p.get("arguments") or p.get("input") or p.get("action") or ""
            yield when, "tool call", f"[{p.get('name', t)}] {clip(str(args), 500)}"
        elif t in ("function_call_output", "custom_tool_call_output") and result_limit > 0:
            out = p.get("output")
            if isinstance(out, dict):
                out = out.get("content") or json.dumps(out)
            yield when, "tool result", clip(str(out), result_limit)
        elif t == "reasoning":
            summ = " ".join(s.get("text", "") for s in p.get("summary", []) if isinstance(s, dict))
            if summ.strip():
                yield when, "assistant (thinking)", clip(summ, 1500)


def load(path: Path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def digest_file(path: Path, mode: str) -> tuple[str, list[str]]:
    rows = load(path)
    result_limit = {"narrative": 300, "full": 2500, "brief": 0}[mode]
    prompt_limit = 1500 if mode == "narrative" else 6000
    is_codex = any(isinstance(r.get("payload"), dict) for r in rows[:50])
    entries = (codex_entries if is_codex else claude_entries)(rows, result_limit, prompt_limit)
    if mode == "brief":
        # A sub-agent's task and its final report: the first user message and the assistant text after its last tool call.
        entries = list(entries)
        first = next((e for e in entries if e[1] == "user"), None)
        last_tool = max((i for i, e in enumerate(entries) if e[1] == "tool call"), default=-1)
        report = [e for e in entries[last_tool + 1:] if e[1] == "assistant"]
        meta = path.with_suffix(".meta.json")
        desc = json.loads(meta.read_text(encoding="utf-8")).get("description", "") if meta.exists() else ""
        entries = ([(first[0], "task" + (f" ({desc})" if desc else ""), clip(first[2], 8000))] if first else []) + \
                  [(e[0], "final report", e[2]) for e in report]
    blocks, last_head = [], None
    for when, role, text in entries:
        text = redact(text)
        if role in ("tool call", "tool result", "tool error"):
            blocks.append(f"    {role}: " + text.replace("\n", "\n    "))
            continue
        head = f"### {when} IST · {role}"
        blocks.append(f"\n{head}\n\n{text}" if head != last_head else text)
        last_head = head
    label = ("subagent " if "subagents" in path.parts else "") + path.stem
    return label, blocks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="transcript files or folders (searched recursively for *.jsonl)")
    ap.add_argument("--member", default="me", help="your member name, used in the output file names")
    ap.add_argument("--out", default="work/kb_digest", help="output folder (default: work/kb_digest, git-ignored)")
    ap.add_argument("--mode", choices=["narrative", "full", "brief"], default="narrative",
                    help="brief: only each transcript's task and final report (good for sub-agent logs)")
    ap.add_argument("--max-chars", type=int, default=300_000, help="split each digest into parts of about this size")
    args = ap.parse_args()

    files: list[Path] = []
    for raw in args.inputs:
        p = Path(raw).expanduser()
        files += sorted(p.rglob("*.jsonl")) if p.is_dir() else [p]
    if not files:
        print("no .jsonl transcripts found", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for f in files:
        label, blocks = digest_file(f, args.mode)
        if not blocks:
            continue
        parts, cur, size = [], [], 0
        for b in blocks:
            if size + len(b) > args.max_chars and cur:
                parts.append(cur)
                cur, size = [], 0
            cur.append(b)
            size += len(b) + 1
        parts.append(cur)
        for i, part in enumerate(parts, 1):
            times = re.findall(r"^### (\d{4}-\d\d-\d\d \d\d:\d\d) IST", "\n".join(part), re.M)
            span = f"{times[0]} → {times[-1]}" if times else "?"
            name = f"{args.member}_{args.mode}_{label.replace(' ', '-')[:40]}_p{i:02d}.md"
            body = f"# Digest: {label} (part {i}/{len(parts)}, {args.mode})\n\n- span (IST): {span}\n- source: {f.name}\n" + "\n".join(part) + "\n"
            (out / name).write_text(body, encoding="utf-8", newline="\n")
            index.append(f"| {name} | {span} | {len(body):,} |")
    (out / "INDEX.md").write_text("| digest part | span (IST) | chars |\n|---|---|---|\n" + "\n".join(index) + "\n", encoding="utf-8")
    print(f"{len(index)} digest parts in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
