# Plans: how we choose the approach

Each member writes a plan independently. We then pick one as the base and take the best ideas from the others. The shared contracts (`docs/CONTRACTS.md`) keep the parts compatible.

## Submitting a plan

- Put it at `plans/<member>/PLAN.md`. A PDF export is optional: `plans/<member>/PLAN.pdf`.
- Only you edit your folder. Comment on others' plans in the PR or in chat.
- Cover at least the following:
  - the key data insights;
  - blocking (candidate generation) and its expected recall;
  - matching model and features;
  - the decision rule for F0.5;
  - validation;
  - France (test-only country);
  - compute and time budget;
  - risks;
  - timeline to the first submission.

## Current plans

> **Decided on Fri 25 Sep, 14:15 IST.** The plan we build is **`plans/FINAL_PLAN.md`**: Plan A as the base, with grafts from Plan B. The reasons, grafts and rejected ideas are in `plans/DECISION.md`. The candidate plans below are kept unchanged for the record.

| plan | author | file | status |
|---|---|---|---|
| A | Ameya | `plans/ameya/PLAN.md` (+ `PLAN.pdf`) | submitted; **base** |
| B | Sachi | `plans/sachi/PLAN.md` | submitted; **grafts taken** |
| C | Member 3 | none | not submitted |
| **Final** | coordinator | **`plans/FINAL_PLAN.md`** | **accepted, v1.0** |

## Decision meeting (about 45 minutes, chaired by the coordinator)

1. **Pitch:** each author gets 5 minutes. Say what's different, the biggest risk, and the time to the first valid submission.
2. **Score** each plan on the rubric below. Everyone scores independently, and we take the average.
3. **Choose the base plan:** the highest weighted score, unless it fails a hard gate.
4. **Choose grafts:** components from the other plans that are compatible with `docs/CONTRACTS.md` and clearly better for one stage.
5. **Record it** in `plans/DECISION.md`: the base, the grafts, the rejected ideas with reasons, and the owner per area.
6. The coordinator updates `docs/TEAM.md` (owners), `docs/ROADMAP.md` (tasks) and, if needed, `docs/CONTRACTS.md`.

### Hard gates (a plan failing any of these can't be the base)

- It can produce a valid submission by **Friday 23:30 IST**.
- It uses only the provided data, and models that are MIT or Apache-2.0 with at most 8B parameters.
- It runs on our hardware within the time budget, including test inference on about 10M records.
- It has no hard-coded {US, India} assumptions. France must work.

### Rubric (score 1 to 5, then weight)

| criterion | weight |
|---|---|
| Expected F0.5, i.e. how well it handles what the data showed: multi-match clusters, sibling distractors, scripts, empty addresses | 30% |
| Blocking recall ceiling and how it is measured | 15% |
| Robustness: France, more distractors in test, calibration | 15% |
| Time to first submission, and incremental value after that | 15% |
| Compute and memory feasibility on team machines | 10% |
| Clarity of the validation protocol (shared holdout, metrics) | 10% |
| Parallelizability across three people | 5% |
