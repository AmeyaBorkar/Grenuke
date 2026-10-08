# Recovery audit and bounded attempt toward 0.991

27 September 2026, about 10:00 IST. For Claude Opus taking over for Aarush Bakshi.
Fetched main: `1dd5a71f0a1aac9fa8dae91f09f40ea28c9fe6cd`.
Reviewed PR56 head `aeecf765cbae26f65c0e78e4e591a187267038f6`, PR58 head
`304ab01ddc44d9b3b3b0eed0b5b6b375f952a1cc`, and issue45 comments through 04:09 UTC.

## Decision

**0.991 is not demonstrated reachable, but the report does not prove it impossible.**
Keep packaging and the two planned measured comparisons moving. Spend the remaining experiment
window on one narrow audit of missing candidates, with a targeted audit outside the encoder band
only if candidate recovery fails its early screen. No new rentals or broad training sweeps.

The baseline remains **v7nst, measured public 0.990179**. The reported rank is now 15;
the reported leader is 0.991483. Neither rank was independently read from the portal here.
**v7sq-dpc at approximately 0.990295 is an estimate, not a measured result.** The user
will supply the new scores later. Do not advance the best-file pointer before then.

This supersedes the experiment schedule in `CLAUDE_OPUS_TAKEOVER.md`: family blending is
already done, round-two self-training drifted, and old threshold probes were withdrawn.
Do not rebuild those experiments simply because an older handoff lists them as pending.

## Why the impossibility argument needs correction

1. **The leader's France score is unknown.** In
   `delta_LB = w_ui * delta_UI + w_fr * delta_FR`, setting `delta_UI=0` gives a
   conditional French gap. Subtracting two scores after assigning both teams the SAME
   UI score makes that gap invariant by construction. It does not establish that their
   UI scores are equal. The bound inferred from the leader's French score being <=1 is
   conditional too. Public-subset weights need not exactly equal full-test weights.
2. **Confident accepted predictions do not measure recall.** The fact that 97% of accepted
   French pairs have pc>=0.99 neither counts missing true pairs nor establishes that the
   remaining errors are all substitutions. Similar prediction counts likewise do not
   establish similar recall: false positives can replace false negatives.
3. **The disagreement result rejects a particular blind deletion rule, not every verifier.**
   Its 17.76% rate is on rule-derived positives, and 8.74% is on an unknown-label mixture.
   Neither measures disagreement among actual French false positives. The populations are
   selected differently, and the rule labels are proxies. This is a strong reason NOT to
   delete on `bge<0`, but not a proof that disagreement is globally anti-correlated with
   wrongness. Raw logit signs also need domain-specific calibration.
4. **The 8,111 figure is an excess-rate estimate, not a list of proven errors.** Multiplying
   it by 0.18 is an illustrative gain scenario, not an exact upper bound. Per-S1 F0.5 changes
   depend on the entire predicted and true sets; pairs are not independent score units.
5. **An empty-France upload does not isolate UI directly.** Truly singleton French S1s
   still score 1 under an empty prediction. It leaves the French singleton contribution.
   Do not spend a slot on fr0 based on the incorrect zero-contribution assumption.
6. **COPY is a diagnostic population, not ground truth.** Not being overridden by a rule
   makes it less circular as a model comparison, but does not make same-name, empty-address
   pairs unambiguous. The reported 97.7% rate itself is below 100% and is from another domain.

These corrections remove unjustified certainty. They do not create an improvement or justify
shipping a risky rule. Existing negative experiments remain negative.

## What has actually been inspected

- `experiments/ameya/model-v1/cluster.py`: computes similarity to confident sibling records
  **for existing candidate rows**. It does not generate missing `(s1,r)` pairs.
- `stage3.py`: considers rivals in its existing candidate graph and calibrates empty-address
  records. This is not a search over previously unseen S2/S3 links.
- `s2.py`: stage 2 scores rows passing stage 0 with p1>=0.002; its coverage is NOT the same
  as the narrower cross-encoder band. Do not claim all high-confidence rows bypass stage 2.
- PR56's `confident_disagree.py`: encoder logits cover **9.2% of accepted French pairs**,
  5.5% overall. Its analysis is restricted to that band. It does not test the other 90.8%
  of accepted French pairs or rejected/never-retrieved pairs.
- Research 6.12's candidate-cut check found only two French pairs with model pc>0.7 outside
  the final cut. That is useful, but testing with the same model does not measure its false
  negatives or candidates never generated.
- Research 6.14's operation checks condition heavily on same-house-number populations.
  They do not establish coverage of missing-address or heavily altered-address pairs.
- PR58 already implements exact-address COPY additions, cross-commune drops and the
  labelled-country decision improvements. Do not count these as new ideas.

## One primary attempt: retrieve through trusted alternate records

Hypothesis: an S1's official name can differ substantially from a true S2/S3 alias, while
two copies of that alias remain similar to each other. A matched record can therefore find
another copy that direct S1-to-record retrieval missed. This was previously deprioritized
using US/India headroom; its incremental French candidate coverage has not been demonstrated
in the reviewed reports. It may still turn out too small.

Example, illustrative only: an S1 has the registered name, a securely matched S2 uses its
abbreviated trading name with a full address, and an unassigned S3 uses a damaged version
of that trading name. Search from the S2 alias, then evaluate the proposed S1-S3 pair.

### First 30-45 minutes: candidate audit, no prediction edits

Implement under `experiments/bakshi/recovery/`; new tags only. Do not modify another
session's worktree or the final-package builder.

Inputs: records/norm tables, current protected final matches, original blocking candidates,
final candidates, stage-1/stage-2 scores where present, source/country mapping, and training
truth plus genuine OOF baseline predictions for evaluation. If full artifacts are on the
integration machine, run the audit there serially, respecting its memory guard.

1. Build an anchor table `(owner_s1, anchor_r, source, country, name, address, provenance)`.
   Confidence alone is insufficient. Initially require an unambiguous owner, nonempty
   consistent full address, meaningful name evidence and no known generator-negative
   contradiction. Separate anchors added by rules from model-supported anchors. Do not
   use target ground truth to select anchors.
2. Use anchor names as additional queries into S2/S3 records of the same country. Start
   with indexed exact/normalized alias plus full-address keys and rare character/token
   keys; cap very common keys. Retrieve a bounded top-K, with K fixed before evaluation.
   Do not join on a house number plus a common first name such as Jean. No all-pairs scan.
3. First search unassigned records. Keep currently owned records as a separate later audit;
   do not steal owners or invoke transitive closure. Preserve independent S2/S3 evidence
   where available; two near-duplicate witnesses are not two independent votes.
4. Project anchor hits to `(owner_s1, candidate_r)`. Exclude self links and deduplicate.
   Reject cross-country pairs and explicit full-address conflicts. Missing address is
   missing evidence, not an agreement. Broad generic-name/empty-address collisions are
   an excluded stratum in the first pass.
5. Classify each proposed pair by where the old pipeline lost it: never blocked; stage 0;
   stage-2/CE coverage; final candidate cut; decision; or already owned. Report incremental
   counts and affected S1s, not raw retrieval hits or repeatedly counted pairs.
6. Write a proposal parquet and CSV audit with anchor IDs, old/new ownership, feature
   evidence, retrieval key, old scores if any and the death-stage classification. Existing
   matched and candidate files stay untouched.

**Required output at 45 minutes:** actual novel pairs/S1s by country and stratum, sampled
ambiguous examples, measured retrieval time/RAM, and whether the coverage is large enough
to justify evaluating a correction. Stop if all it finds are already-blocked pairs or a
few hundred weak additions. Do not silently turn this into general retriever development.

### Next 45-60 minutes: evaluate exact decisions before touching France

- Replay the same anchor selection and retrieval on labelled US/India using OOF predictions,
  not truth-selected anchors. Do not mix genuine held-out models with final `--all` outputs
  while describing the result as independent. All variants share the same evaluation route.
- Evaluate the incremental proposal pool, not all historical easy pairs. Include difficult
  negatives sharing name/address and a breakdown by anchor type, crowding, source, missing
  address and edit severity. Reserve evaluation entities before tuning the recovery rule.
- Compute actual per-S1 F0.5 before/after with `ber.eval.metric`, then paired entity bootstrap.
  Where entities share a contested record, also report a component-blocked uncertainty
  check if feasible. Report each country's delta and the absolute corrected error counts.
- Existing models may score new pairs only after all their required context/retrieval
  features are computed correctly. Do not replace missing context with zero or inject
  unseen logits into a classifier trained on NaNs outside the encoder band.
- If a small, strict structural rule is supported, test it as a separate bounded correction.
  If it needs a large retrain to work, drop it for today. Transfer to France remains a
  hypothesis even with a positive US/India gate; check French coverage and ambiguity.
- The first correction should add verified high-precision unowned matches only. Do not
  simultaneously change ownership, thresholds, pseudo-label teachers and post-ops. That
  would make the result uninterpretable and greatly increase integration time.

### How much room is enough?

From the measured baseline, 0.991 needs **+0.000821**. On the whole-test S1 count
1,732,544, that is **1,422.42 units of summed per-S1 F0.5 improvement**. This is a scale
check, not an exact public-subset requirement.

For an entity with four true matches and three correctly predicted, recovering the last
true match improves its score from 0.9375 to 1: **+0.0625**. Adding a false one instead
changes 0.9375 to 0.75: **-0.1875**. At that particular state break-even precision is 75%.
At perfect precision it would take about **22,759** such recovered matches on distinct S1s
to close the entire gap. At lower precision it takes more. Singleton rescue/drop cases
have different effects; do not extrapolate a universal gain per pair.

Compute estimated room from the actual distribution of affected entity states on labelled
data, with uncertainty and a clear domain-transfer caveat. `affected_S1 / total_S1` is only
a loose whole-test ceiling; it is not an exact public-score ceiling.

## Secondary audit only if the first attempt stops early

Audit accepted French pairs **outside the CE band**, selected by evidence independent of
pc: conflicting full addresses, rare-token incompatibility, competing-owner evidence,
or inconsistent trusted sibling records. Exclude contradictions already fixed by PR58.

This differs from the rejected `bge<0` deletion rule: it targets a population the old
encoder audit did not observe. First run the same selection on genuine labelled OOF
predictions and measure error enrichment over matched controls (same source, address
availability and name crowding). A different domain's raw disagreement rate is not a label.

Only if enrichment and affected-entity headroom are substantial should an existing local
checkpoint score a small timed batch. No new rental. No claim that old cached logits exist
outside the old band. Any resulting verifier needs evaluation on held-out selected examples;
do not use uncalibrated logit sign as a delete decision. If missing checkpoints, features or
runtime make a validated correction impossible by 13:00, stop. This is a contingency audit,
not permission to reopen an unbounded disagreement-inference project.

## Schedule and decision rules

Use the actual clock; the model cutoff stays **13:00 IST**, freeze **15:00**, final-best
upload target **19:00**, reported portal close **21:00**, all on 27 September.

1. Now: keep the prepared v7sq-dpc / v7nst-dpc public comparisons and packaging moving.
   Those estimates need measurement; don't hold them hostage to a new experiment.
2. In parallel with their human upload/transfer: run only the bounded candidate audit above.
   No more than one memory-heavy process on the integration machine.
3. Within 45 minutes: kill the attempt or select one specific correction stratum based on
   measured coverage. If it cannot plausibly help much, say so without claiming all routes
   are mathematically impossible.
4. By 12:15: finish labelled evaluation and estimate whether producing a full valid pair of
   TSVs plus tests fits before 13:00. If not, abandon the new variant.
5. By 13:00: new variant must be built, gated, audited and reproducible. Preserve the best
   observed baseline independently. After cutoff, concentrate on existing candidates and
   a complete final archive.
6. With the captain's confirmed remaining quota, reserve one slot to restore the best
   measured output last. No pure information probe or untested combination in that slot.

One deterministic public score does not fluctuate on re-upload; uncertainty concerns
generalization to the private subset. Do not call a fixed 0.00005 gap universally
significant/insignificant without the paired affected-entity distribution and sampling setup.
F0.5 here is a matching metric, not ordinary classification accuracy.

## Files and machine access

Workspace: `$HOME/Documents/Codex/2026-09-25/in`.

| purpose | location |
|---|---|
| this isolated review checkout | `work/GrenukeRecoveryAudit` |
| existing active execution checkout; read, do not edit | `work/GrenukeOpusExec` |
| scientific Python | `work/GrenukeGit2/.venv/Scripts/python.exe` |
| cached records/norm and old dev artifacts | `work/GrenukeGit2/work` |
| raw data | `$HOME/Downloads/New folder/6ab10eb3b23ba_student_resource/student_resource/dataset` |
| protected matching file | `$HOME/Downloads/New folder/matching_resultsv7nst.tsv` |
| current execution ledger | `work/GrenukeOpusExec/experiments/bakshi/final-package/ledger.json` |
| current packaging scripts | `work/GrenukeOpusExec/experiments/bakshi/final-package/` |
| updated GitHub snapshot | `work/github_snapshot.json` |

Paths starting with `work/` are relative to the workspace above. Set PYTHONPATH to the
active checkout's `code/business_entity_resolution/src` when using the shared venv.
The integration machine's actual absolute roots and full artifacts remain to be resolved
from its configured environment; do not claim they are present on this laptop.

Protected v7nst matching SHA256:
`659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533`.
Paired candidates: `510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa`.
Latest **reported** runnable fallback ZIP:
`d9eb4388409a9d17af483213fbaa88c6b8a475ab501b3c88d62e1980e34f0cd2`.
Older ZIP hashes including `4bd6c7a1...` were invalidated by a missing-source-file bug.

Pending v7sq-dpc matching/candidate hashes:
`cdda9a2da0147c06039d83b673e26d8bfc71c5171915148c1dcd24979ea0e85c` /
`55b766efbe7473e17985d06810d27f5d758951b1ce42832a0dd9081a76af5331`.
Pending v7nst-dpc matching:
`f349012516cdd239106cc88f53e4f5ccaf8b5531d30a9345e82f0584783494a2`;
its candidate file is the protected v7nst candidate file above.

## Completion and reporting

Record proposed, tested, rejected and measured separately. A corrected reasoning error is
not an ML gain. No new model, recovery audit result or 0.991 outcome is claimed by this
document. This session read the code/reports and prepared the execution plan; it did not
run the new candidate search or alter submission predictions.

Keep GitHub updates in Bakshi-owned paths and a focused PR. Do not edit another session's
files, merge its PR, contact teammates or use a leaderboard slot without the appropriate
user authorization. Existing package rules and access permissions continue to apply.

Any new candidates must be included in the pipeline's actual candidate artifact and final
candidate TSV, with provenance. Validate both files, all S1 rows, ownership, IDs, country
consistency and matches-subset-candidates. Extract the ZIP and run imports/tests from its
own source; source-tree tests alone previously missed a broken archive.

The useful final report is: actual public scores, one clearly defined correction with
measured holdout evidence and French coverage (or the reason it was rejected), exact
selected output hashes, actual spend, remaining blockers and the validated final package.
Do not promise a rank or recommend financial commitments contingent on winning.
