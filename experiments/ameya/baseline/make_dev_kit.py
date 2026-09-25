"""Assemble the dev kit for small machines: one folder to upload to the team drive (CONTRIBUTING section 7).

python experiments/ameya/baseline/make_dev_kit.py --cands ameya-block-v0-dev --features ameya-baseline-v0-dev

Copies, under the same relative paths as work/ (so teammates unzip it into their repo root):
- work/records/{train,test,truth}.parquet (only if --with-records; everyone can rebuild them in ~75 s),
- work/candidates/<cands>/train.parquet (dev-sample candidates, C4),
- work/features/<features>/train.parquet (dev-sample pair signals in the C8 layout, for model development),
- any --extra work-relative files (e.g. dev-sample scores) and a --doc markdown file at the kit root,
and writes MANIFEST.txt with sha256, size, git commit and the command recorded in each artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from ber.artifacts import git_commit, read_meta
from ber.paths import work_dir


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--with-records", action="store_true")
    ap.add_argument("--extra", nargs="*", default=[], help="more work-relative files, e.g. scores/<tag>/train.parquet")
    ap.add_argument("--doc", default=None, help="a markdown file copied to the kit root")
    ap.add_argument("--out", default=None, help="default: <work>/dev_kit")
    args = ap.parse_args()
    work = work_dir()
    out = (work / "dev_kit") if args.out is None else __import__("pathlib").Path(args.out)
    files = [f"candidates/{args.cands}/train.parquet", f"features/{args.features}/train.parquet"] + list(args.extra)
    if args.with_records:
        files += ["records/train.parquet", "records/test.parquet", "records/truth.parquet"]
    lines = [f"# Grenuke dev kit, built from commit {git_commit()}", "# unzip into the repo root: files land in work/",
             "# sha256  bytes  path  |  command that produced it", ""]
    for rel in files:
        src = work / rel
        dst = out / "work" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        meta = read_meta(src)
        lines.append(f"{sha256(dst)}  {dst.stat().st_size}  work/{rel}  |  {meta.get('command', '?')} "
                     f"(commit {meta.get('git_commit', '?')})")
    if args.doc:
        doc = out / Path(args.doc).name
        shutil.copy2(args.doc, doc)
        lines.append(f"{sha256(doc)}  {doc.stat().st_size}  {doc.name}  |  documentation")
    (out / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"dev_kit": str(out), "files": files}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
