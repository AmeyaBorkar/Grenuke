# Leaderboard submissions protocol

The budget is **5 uploads per day for the whole team**, over 3 days (15 total). Only the **submissions captain** (`docs/TEAM.md`) uploads.

## Before any upload

1. The outputs come from a commit that is **pushed** (ideally on `main`).
2. `python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test` prints **PASS**.
3. You have holdout numbers (C2/C7 in `docs/CONTRACTS.md`) for the exact commit, plus a one-line hypothesis ("what this upload tests").
4. You requested a slot from the captain in the team chat.

## After the upload (the captain does this within 15 minutes)

1. Create the record: `python scripts/new_doc.py submission --member <captain> --num NN`.
2. Fill in the public score, holdout numbers, commit, file hash (`sha256sum output/matching_results.tsv`) and notes.
3. Tag the commit and push the tag: `git tag sub/<YYYY-MM-DD>-<NN> <commit> && git push origin sub/<YYYY-MM-DD>-<NN>`.
4. Commit the record on the captain's branch and open a small PR.
5. Archive the uploaded TSV locally in `submissions/files/<YYYY-MM-DD>-<NN>/`. It is git-ignored.

## Budget plan (the captain adjusts it)

| day | slots | intended use |
|---|---|---|
| Fri 25 | 5 | first valid baseline (1–2), a quick fix (1), keep 1–2 spare before midnight |
| Sat 26 | 5 | the main improvements (3), France and threshold probes (1), 1 spare |
| Sun 27 | 5 | final candidates (2–3), 1 spare; **the last upload must be the chosen final model** |

## Rules

- **Never** upload anything the validator hasn't passed.
- The public leaderboard covers only a subset of the test set, and the final rank uses the private part. Choose the final model on **holdout** (normal and stress test) plus leaderboard consistency, not the leaderboard alone.
- The day boundary is assumed to be 00:00 IST; the captain confirms it on the portal. Unused slots don't carry over.
