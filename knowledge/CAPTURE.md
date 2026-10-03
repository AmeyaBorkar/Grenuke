# Capture kit: get everything you know into the knowledge base

Each of us worked with AI agents on our own machine, so a lot of what we decided and why lives only in our chat histories. Use this kit to turn your chats, notes and memory into standard records in `knowledge/people/<you>/`. It takes about 1–2 hours, mostly agent time.

**Due: Sun 4 Oct, 12:00 IST** (see `finale/README.md`). A partial capture on time beats a perfect one late.

---

## Step 1. Set up (5 minutes)

```bash
git fetch origin
git switch -c <you>/kb-capture origin/main          # e.g. bakshi/kb-capture
python scripts/new_doc.py person --member <you>     # creates knowledge/people/<you>/ from the templates
```

## Step 2. Find your sources (10 minutes)

List them all in `knowledge/people/<you>/sources.md`, even the ones you cannot mine.

| source | where to look |
|---|---|
| **Claude Code** | `~/.claude/projects/<folder named after your repo path>/*.jsonl`, plus `<session>/subagents/*.jsonl` for sub-agents. On Windows `~` is `C:\Users\<you>`. Also any other folders where you worked on Grenuke, e.g. rented-GPU-box checkouts copied back |
| **Claude Code memory** | `~/.claude/projects/<folder>/memory/*.md` (already-summarised facts) |
| **Codex CLI** | `~/.codex/sessions/**/rollout-*.jsonl` |
| **ChatGPT / Claude.ai / Gemini (web)** | export the relevant conversations as text or Markdown (copy-paste is fine) into a local folder **outside the repo** |
| **Cursor / Copilot chat** | export or copy the relevant chats to text |
| notes, screenshots, WhatsApp | copy the project-related parts to text, outside the repo |
| your branches, PRs, scripts | `git log --author=<you>`, your `experiments/<you>/` folder, your PRs and issues |

## Step 3. Make digests (5 minutes)

```bash
# Claude Code / Codex logs → short, redacted, time-stamped Markdown in work/kb_digest/ (git-ignored)
python scripts/kb/digest_transcripts.py ~/.claude/projects/<folder> --member <you>
python scripts/kb/digest_transcripts.py ~/.claude/projects/<folder> --member <you> --mode brief --out work/kb_digest/briefs
python scripts/kb/digest_transcripts.py ~/.claude/projects/<folder> --member <you> --mode full  --out work/kb_digest/full --max-chars 2000000
```

- **narrative** (the default) is what your agent reads.
- **full** keeps long tool outputs, for finding exact numbers.
- **brief** keeps only each sub-agent's task and final report.
- Web-chat exports need no digest; give them to your agent as they are.

**Never commit digests, transcripts or exports.** Hooks and CI block `*.jsonl` and `work/`.

## Step 4. Run your agent (30–90 minutes)

Start a fresh agent session in your branch checkout and paste the prompt below, after filling in the `<…>` parts.

```text
You are helping <Name> (<member>) of team Grenuke capture everything they know about our Amazon ML
Challenge 2026 solution, for the Grand Finale jury on 7 Oct. Read AGENTS.md, knowledge/STANDARD.md and
knowledge/CAPTURE.md first and follow them exactly.

Sources, in time order: the digests in work/kb_digest/ (INDEX.md lists them), the sub-agent briefs in
work/kb_digest/briefs/, <other exports, e.g. ~/grenuke-chats/*.md>, my memory files <path>, and my work in
the repo (git log --author=<github handle>, experiments/<member>/, my PRs and issues). Read every digest
part completely; do not skim. Use work/kb_digest/full/ to recover exact numbers.

Write, in knowledge/people/<member>/ (the files already exist as templates):
- sources.md: every source, and whether it was mined fully, partly or not at all
- journal.md: one entry per working session (when, goal, what was done, results with numbers, decisions,
  problems, next)
- decisions.md: every decision I made or influenced, in the standard decision format, with local IDs
  <initial>-D-NN; include options rejected and the reasoning at the time
- experiments.md: every experiment I ran, kept or not, with local IDs <initial>-X-NN
- contributions.md: what I built, owned, reviewed and originated, with links (for accurate credit)
- numbers.md: every number worth quoting, with scope, evidence level (M/E/R/U) and source
- open-questions.md: anything unclear or conflicting, and facts only I can confirm

Cite chat sources as [chat:<member>/<first 8 chars of session id> YYYY-MM-DD HH:MM] using the digest
headers. Mark every number's evidence level. Redact IPs, ports, host names, keys, tokens, e-mails, phone
numbers and personal paths. Do not invent anything; write "unknown" and add it to open-questions.md.
Do not edit any file outside knowledge/people/<member>/. Do not commit. When done, list the 15 facts you
are least sure of so that <Name> can confirm them.
```

## Step 5. Review, add what only you know, and open a PR (20 minutes)

1. **Check your agent's work.** Read `contributions.md` and `decisions.md` first, and fix anything wrong.
2. **Answer the agent's "least sure" list.**
3. **Add what never went through a chat:** reasons you had in your head, decisions made on calls or WhatsApp, things you tried by hand. Cite them as `[memory:<you>]` (level R), or `[call:<who> date]` / `[whatsapp date]`.
4. **Grep for anything sensitive** before committing:

   ```bash
   grep -rnE '([0-9]{1,3}\.){3}[0-9]{1,3}|ssh |@gmail|Users\\|/home/|BEGIN .*KEY|hf_|ghp_' knowledge/people/<you>/
   ```

5. **Commit and open a PR:**

   ```bash
   git add knowledge/people/<you>/
   git commit -m "docs(kb): <you> knowledge capture"
   git push -u origin <you>/kb-capture && gh pr create --base main --fill
   ```

The curator (Ameya) merges your records into the shared knowledge base. Afterwards, check that your parts are credited and correct in `knowledge/`, and comment on the PR if not.

## What a good capture looks like

- Every decision has **options, a reason and a number**, in the shape "we kept <X> over <Y> because <analysis> showed <number> [source], and the gate gave <Δ> on the holdout [source]".
- **Dead ends are in.** "Tried X, lost 0.0003, dropped" is as useful to the jury as a win.
- **Credit is precise:** what you originated, and what you built from someone else's idea.
- **Unsure things are marked**, not smoothed over.
