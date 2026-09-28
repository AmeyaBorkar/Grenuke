"""Paired bootstrap: runner-up (cont_first, params from v7nst half A) minus winner (DP shift 0.2, lam 0.01), per model.
Also prints the candidates tag recorded in the v7nst final matches (for the apply check). Writes paired.json."""
from __future__ import annotations

import json
import os

import pyarrow.parquet as pq

from ber.eval.gates import paired_bootstrap
from ber.paths import artifact_path
from check_cont import cont_first
from core import D, Hold, expected_f_select, to_q


def main() -> int:
    md = pq.ParquetFile(artifact_path("matches", "ameya-model-v7nst-s3-ops3a", "test")).schema_arrow.metadata
    print("v7nst final provenance:", json.loads(md[b"ber"])["command"], flush=True)
    out = {}
    for tag in ("ameya-s3-v7nst", "ameya-s3-v7s"):
        H = Hold(tag)
        fw = H.per_entity(expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01))
        fc = H.per_entity(cont_first(H, 0.6, 0.575, 0.74, 0.02))
        r = {}
        for part in ("full", "A", "B", "US", "India"):
            m = H.masks[part]
            bs = paired_bootstrap(fw[m], fc[m])
            r[part] = {k: round(1e6 * bs[k], 1) for k in ("delta", "ci_low", "ci_high")}
            r[part]["p_better"] = bs["p_better"]
        out[tag] = r
        print(tag, "cont_first - winner:", r, flush=True)
        del H
    json.dump(out, open(os.path.join(D, "paired.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
