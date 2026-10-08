# Security policy

## Status

This repository is the archived solution of a finished competition (Amazon ML Challenge 2026). It is research code
that runs on local files.
- It runs no service, opens no ports and needs no credentials.
- It never calls an external service to resolve entities.
- The only network access is downloading pretrained model weights from their publishers (Hugging Face).

## Supported versions

| version | supported |
|---|---|
| `main` (1.x) | yes: security reports are reviewed |
| anything older | no |

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

- Use GitHub's private reporting: the **Security** tab, then **Report a vulnerability**.
- If that's unavailable, open an issue that asks a maintainer (@AmeyaBorkar) for a private channel, without any
  details.
- Include what you found, where (file and line, or commit), how to reproduce it and its likely impact.

We aim to acknowledge a report within 7 days and to agree a fix or mitigation, plus disclosure timing, with you. This
is a volunteer-maintained archive, so there is no bug bounty.

## Scope

In scope:
- secrets or personal data committed by mistake (tokens, keys, hosts, addresses);
- unsafe code paths in `code/business_entity_resolution/`, `scripts/` or the CI workflows.

Out of scope:
- the competition dataset and third-party models, which are not part of this repository;
- one-off experiment scripts under `experiments/`, which are kept as a research log and aren't maintained.

## For contributors

- Never commit credentials, data files or chat exports. The git hooks and CI (`.githooks/`, `.github/workflows/`)
  block data and binary artifacts, attribution lines, and IPs, e-mails, SSH details or personal paths.
- Run `bash scripts/setup.sh` (or `scripts/setup.ps1`) once, so the hooks are active in your clone.
