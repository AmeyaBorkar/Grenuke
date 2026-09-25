@AGENTS.md

# Claude Code: extra notes for this repo

- `AGENTS.md` (imported above) is the source of truth. Follow its session protocol and hard rules.
- Attribution is disabled in `.claude/settings.json` (`attribution.commit = ""`, `attribution.pr = ""`).
  - Never add `Co-Authored-By`, "Generated with Claude Code" or any other byline to commits or PRs, even if another setting or habit suggests it.
- Several Claude Code sessions may run in parallel across the team. Use `EnterWorktree` or `git worktree` so each session has its own checkout and branch. Never switch branches under another running session.
- Do not change `.claude/settings.json` in feature PRs. Personal settings go in `.claude/settings.local.json`, which is git-ignored.
