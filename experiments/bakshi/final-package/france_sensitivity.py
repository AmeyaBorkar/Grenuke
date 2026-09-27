#!/usr/bin/env python3
"""How much does the "France is the whole gap" diagnosis depend on one unverified assumption?

Every French figure the team quotes comes from

    LB = w_ui * F_ui + w_fr * F_fr

with w_fr = 0.1497523 (France's share of test S1, measured) and w_ui = 1 - w_fr. That is ONE equation with
TWO unknowns. It is resolved by assuming F_ui equals the shared-holdout macro F0.5 re-weighted, giving
F_ui = 0.991742 and hence F_fr = 0.9813.

**That assumption is the linchpin of the entire diagnosis, and it is the one number most likely to be
optimistic.** The holdout is not an untouched test set: the pipeline was developed against it for days, and
the final `--all` fit uses it as a fourth out-of-fold group. If the true US/India figure is lower than the
holdout says, then France is *higher* than 0.981 and the leaders' advantage is less French than we think.

This script does not resolve it -- only an fr0 probe (submitting with France emptied) measures F_ui directly,
and that costs an upload slot without improving the score. It quantifies what is at stake, so the conclusion
is stated with the right confidence.

    python france_sensitivity.py [--lb 0.990179] [--leader 0.991483]
"""

from __future__ import annotations

import argparse

W_FR = 0.1497523          # 259,452 / 1,732,544, measured from test_source1.tsv
W_UI = 1.0 - W_FR
HOLDOUT_UI = 0.843226 / W_UI   # the team's assumed F_ui, from the re-weighted holdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lb", type=float, default=0.990179, help="our measured public score")
    ap.add_argument("--leader", type=float, default=0.991483, help="the current leader")
    a = ap.parse_args()

    print(f"measured public score : {a.lb:.6f}")
    print(f"leader                : {a.leader:.6f}   gap {a.leader - a.lb:+.6f}")
    print(f"France share of test S1: {W_FR:.7f}  (US/India {W_UI:.7f})")
    print(f"team's assumed F_ui    : {HOLDOUT_UI:.6f}  (from the re-weighted holdout)\n")

    print("If our true US/India F0.5 is X, then our France F0.5 is implied, and the leader's advantage")
    print("splits differently. Leader's France assumes their US/India equals ours.\n")
    print(f"{'assumed F_ui':>13} {'vs holdout':>11} {'implied F_fr':>13} {'leader F_fr*':>13} "
          f"{'French gap':>11} {'reading':<38}")
    for delta in (+0.0005, 0.0, -0.0003, -0.0007, -0.0015, -0.0030):
        f_ui = HOLDOUT_UI + delta
        f_fr = (a.lb - W_UI * f_ui) / W_FR
        lead_fr = (a.leader - W_UI * f_ui) / W_FR
        gap = lead_fr - f_fr
        if f_fr > 0.995:
            read = "implausible: France above US/India"
        elif delta == 0.0:
            read = "the team's working assumption"
        elif delta > 0:
            read = "holdout pessimistic (unlikely)"
        elif gap > 0.008:
            read = "gap is overwhelmingly French"
        else:
            read = "a real share of the gap is US/India"
        print(f"{f_ui:>13.6f} {delta:>+11.4f} {f_fr:>13.6f} {lead_fr:>13.6f} {gap:>+11.6f} {read:<38}")

    print("\n* The leader's French figure is only meaningful if their US/India really does equal ours.")
    print("  The alternative decomposition, for completeness:")
    need_ui = (a.leader - W_FR * ((a.lb - W_UI * HOLDOUT_UI) / W_FR)) / W_UI
    print(f"  if the leader's FRANCE equalled ours, their US/India would have to be {need_ui:.6f}, "
          f"{need_ui - HOLDOUT_UI:+.6f} above our assumed {HOLDOUT_UI:.6f}.")
    print("  Our own analysis puts about +0.0003 of headroom left on US/India, so that branch is the less")
    print("  likely of the two -- which is why 'the gap is French' remains the best reading. But it is a")
    print("  reading, not a measurement.")

    print("\nWhat would settle it: an fr0 probe (submit with France emptied) measures W_UI * F_ui directly.")
    print("It costs one upload slot and cannot improve the score, so it is only worth it if a DECISION")
    print("depends on the answer. Today none does -- the gap is unreachable either way -- so it should not")
    print("be spent. Worth recording as the one clean experiment we chose not to run, and why.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
