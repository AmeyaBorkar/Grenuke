# Sachi: sources

Summary: where the facts in this folder come from, and how fully each source was mined. Most of Sachi's work happened in
three long claude.ai web conversations, plus GitHub. Nothing here is copied from a transcript. The chats stay on claude.ai
and are cited by an alias, date and time (IST).

## 1. Chat sources (claude.ai, web)

The web transcripts expose no session id, so the citation form `[chat:sachi/<8 chars>]` uses an alias instead. The
date and time in a citation let Sachi find the message. Times from the chat are converted from UTC to IST.

| alias | covers (IST) | what it contains | mined |
|---|---|---|---|
| `web-1` | 2026-09-25 10:28 to 23:37 | problem framing, comparing approaches, repo setup, model v0 (issues #8, #9), gate G6, ownership fix, first sync with Ameya's agent | fully (text); tool output partly |
| `web-2` | 2026-09-25 23:45 to 2026-09-26 about 17:00 | package drafts, LOCO studies, France kit v1 analysis, first look at the Qwen idea | fully (text); tool output partly |
| `web-3` | 2026-09-26 about 17:04 to 2026-10-04 | e5-small vs e5-base, rented GPUs, Qwen LoRA cross-encoder, reproduce_v7sq.sh, final-day analyses, synthetic French, issue #66 checks, final_zip hash check | from the live conversation |

Times on rented machines are in UTC on the machine clock. Where a time below comes from such a clock it was converted
(+5:30) and is marked approximate.

## 2. Repo and GitHub sources

| source | used for |
|---|---|
| `experiments/sachi/` on `main` | scripts and their docstrings |
| issue #63 (GPU coordination, 27 Sep) | Ameya's findings on synthetic vs real French |
| issue #64 (final upload, 27 Sep) | leaderboard results, the estimator bias, the final choice |
| issue #66 (final ZIP, 28 to 29 Sep) | what each member had to put on git |
| issue #79, #81 (Grand Finale, 4 Oct) | this capture |
| PR #58, PR #62, PR #65, PR #67 | stacked rules, Bakshi's package, final-day record, my empty merge |
| docs/decisions, docs/handover, submissions/records | team records, cited where I used them |

## 3. Not mined, or only partly mined

- **My Mac shell history and local files.** File dates from `ls -l` were used for a few timestamps. Nothing else.
- **git history of my branches** (`git log --author`). I could only use the commit ids and messages pasted into the chat.
  Ids not pasted are marked unknown.
- **Messages in WhatsApp and calls.** None were mined. Anything decided there is missing.
- **The first answers I gave on 25 to 26 Sep** (e.g. what I sent Ameya on 26 Sep afternoon) are only known from my
  questions, not from the text I sent. Unknown.
- **Rented-machine logs.** Only the lines pasted into the chat. The machines are destroyed.
