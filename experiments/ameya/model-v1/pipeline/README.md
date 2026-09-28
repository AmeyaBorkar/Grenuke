# pipeline/: the drivers and as-run scripts behind the final submissions (27 Sep 2026)

These files were run from a session scratchpad and are kept here as-is, so the exact code that produced the final packages is in git. They are consolidated into `code/business_entity_resolution/src/` for the submission ZIP (issue #66).

| file | what it does |
|---|---|
| `env6.sh` | environment (PYTHONPATH, work dirs) for the laptop chain |
| `run_local_full.sh`, `run_local_full_w.sh` | the laptop chain after a box stage 2: decide → stage 3 → decide → post_ops → acr_join → package. The `_w` variant runs stage 2 with `s2w.py` |
| `s2w.py` | stage 2 with **weighted** French pseudo-labels (`--pseudo-weight 3`); built the round-2 France model v7sq7wg |
| `france_mixmdp.sh` | **the package's France block**: Composite B's French rows (mixmdp) from the v7sq chain, called by `src/box/compositeB.sh` step 7 with `FR_DIR` |
| `make_pseudo.py` | round-1 French pseudo-labels for the cross-encoders (`ce_box.py --pseudo`) |
| `stack_model.sh`, `stack_pkg.sh` | the stack: h2pc + the US/India combo DP (`asrun/agents/decide/apply_combo.py`), merged by `asrun/stack/merge_dpc.py` |
| `build_pkg.sh` | compose labelled-countries from one model and France from another (`asrun/novel/compose.py`), optional change list (`apply_changes.py`), package |
| `build_final.sh` | per-country compose with drop/add lists (`compose3.py`), package, validator + strict audit, sha256 |
| `package6.sh` | write both TSVs, validator, sha256 |
| `val_queue.sh`, `round3.sh`, `round4.sh`, `round5q.sh` | French valuations; round-3/4 label builders |
| `asrun/` | the exact versions that ran (`novel/`, `stack/`, `agents/decide/`, `agents/hunt/`). Some differ from the earlier copies in `../stack/` |
| `box_runs/` | the stage-2 and cross-encoder launch scripts run on the rented GPU boxes (a record of exact commands and flags), the 7B re-check tooling (`q7drop/`, `q7ens/`, `q7add/` scripts) and the detector experiments |

Composite B's France is `v7sq7wg`:
1. cross-encoders `qst`, `e5ls`, `e5ls2`, `bges`, `e5fr`, z-mean group `cmq7`;
2. `s2w.py` stage 2 with the guarded round-2 labels ×3;
3. `run_local_full_w.sh`;
4. `stack_model.sh` / `stack_pkg.sh`;
5. `build_pkg.sh` with the look-alike drop;
6. `stack/dp_france.py`.

Its US/India and the 7B re-check are Bakshi's (`experiments/bakshi/box/`).
