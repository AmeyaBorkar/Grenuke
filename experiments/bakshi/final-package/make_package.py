#!/usr/bin/env python3
"""Assemble, verify and hash Grenuke_submission.zip.

The archive layout the competition asks for::

    Grenuke_submission.zip
      output/matching_results.tsv          <- the exact submitted bytes, never regenerated
      output/candidate_pairs.tsv           <- its PAIRED candidate file
      code/business_entity_resolution/
        src/ber/...                        <- the team package
        src/model_v1/...                   <- the model chain, copied (not referenced)
        src/box/...                        <- the Qwen2.5-7B cross-encoder, the 7B re-check, Composite B's driver
        README.md  requirements.txt  reproduce.sh  pyproject.toml  tests/...
      Documentation_template.md
      MANIFEST.sha256                      <- extra, so the archive self-verifies

What this does beyond copying files:

* refuses to build if either output file's sha256 differs from ``--expect-*-sha`` (so a stale or
  half-written TSV can never be packaged as the winner);
* refuses to build if the two output files are not a valid pair -- run ``audit_matching.py`` first,
  or pass ``--audit`` to run it here;
* excludes datasets, artifacts, virtualenvs, caches and anything secret-shaped, and then greps the
  staged text files for credential patterns as a second net;
* writes the archive with sorted entries and a fixed timestamp, so the same inputs give the same
  zip bytes;
* extracts the finished archive to a scratch directory and re-hashes every member against the
  manifest, byte-compiles the Python, and checks the required paths are present.

Usage (Composite B, the team's best submission, public 0.990879)::

    python experiments/bakshi/final-package/make_package.py --repo-root . \
        --matching final_zip/output/matching_results.tsv --candidate final_zip/output/candidate_pairs.tsv \
        --expect-matching-sha df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8 \
        --expect-candidate-sha 58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5 \
        --variant compositeB --doc <the filled Documentation_template.md> \
        --out dist/ --audit --test-dir student_resource/dataset/test
"""

from __future__ import annotations

import argparse
import compileall
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(cmd: list[str], env: dict | None = None) -> int:
    """Run a child process with our own stdout flushed first.

    Without the flush our buffered prints land *after* the child's unbuffered output, so the log
    reads out of order and a child's failure can appear under the wrong heading.
    """
    sys.stdout.flush()
    rc = subprocess.call(cmd, env=env)
    sys.stdout.flush()
    return rc

# Everything the archive must contain, checked after extraction.
REQUIRED = [
    "output/matching_results.tsv",
    "output/candidate_pairs.tsv",
    "code/business_entity_resolution/README.md",
    "code/business_entity_resolution/requirements.txt",
    "code/business_entity_resolution/reproduce.sh",
    "code/business_entity_resolution/pyproject.toml",
    "code/business_entity_resolution/src/ber/__init__.py",
    "code/business_entity_resolution/src/ber/pipeline.py",
    "code/business_entity_resolution/src/model_v1/RECIPE.md",
    "code/business_entity_resolution/src/model_v1/s2.py",
    "code/business_entity_resolution/src/model_v1/pseudo_labels.py",
    "code/business_entity_resolution/src/model_v1/acr_join.py",
    "code/business_entity_resolution/tests/test_metric.py",
    "Documentation_template.md",
    "MANIFEST.sha256",
]

# What Composite B's reproduction needs on top of REQUIRED (checked when --variant compositeB).
REQUIRED_COMPOSITE_B = [
    "code/business_entity_resolution/src/box/compositeB.sh",
    "code/business_entity_resolution/src/box/compose_tsv.py",
    "code/business_entity_resolution/src/box/llm_group.py",
    "code/business_entity_resolution/src/box/llm_merge.py",
    "code/business_entity_resolution/src/box/score_pairs.py",
    "code/business_entity_resolution/src/box/rescore_export.py",
    "code/business_entity_resolution/src/box/rescore_eval.py",
    "code/business_entity_resolution/src/box/analysis/export_usin.py",
    "code/business_entity_resolution/src/model_v1/ce_llm_st.py",
    "code/business_entity_resolution/src/model_v1/ce_llm.py",
    "code/business_entity_resolution/src/model_v1/stack/stack.sh",
    "code/business_entity_resolution/src/model_v1/stack/apply_swapsim.py",
    "code/business_entity_resolution/src/model_v1/stack/dp_france.py",
]

# Never copy these, wherever they appear.
DENY_NAMES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ipynb_checkpoints",
              ".ssh", "node_modules", ".idea", ".vscode", "work", "output", "data_cache", "dataset"}
DENY_SUFFIX = {".parquet", ".npy", ".npz", ".pkl", ".pt", ".pth", ".bin", ".safetensors", ".zip", ".gz",
               ".pyc", ".pyo", ".so", ".dll", ".pem", ".key", ".ppk", ".crt", ".log"}
# Secret-shaped FILENAMES. These are matched only against non-source files -- see `denied()`.
# A previous version applied them to everything, and `*token*` silently ate `ber/features/tokens.py`,
# producing an archive that imported but could not run. Filenames are a weak signal for secrets anyway;
# the real defence is `scan_secrets()`, which reads the contents.
DENY_GLOB = ("id_rsa*", "id_ed25519*", "*.env", ".env*", "*.pem", "*.key",
             "secrets.*", "secret.*", "credentials.*", "credential.*", "*.token", "token.json")
# Files that are part of the solution and must never be dropped by a filename heuristic.
SOURCE_SUFFIX = {".py", ".md", ".toml", ".cfg", ".sh", ".yml", ".yaml", ".ini"}

# Second net: scan staged text for things that look like a live credential.
SECRET_PATTERNS = [
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"), "GitHub token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "API secret key"),
    (re.compile(r"x-access-token:[A-Za-z0-9_\-]{10,}"), "embedded access token"),
]
TEXT_SUFFIX = {".py", ".sh", ".md", ".txt", ".toml", ".cfg", ".json", ".yml", ".yaml", ""}


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def denied(p: Path) -> bool:
    if p.name in DENY_NAMES or p.suffix.lower() in DENY_SUFFIX:
        return True
    # Never let a filename heuristic drop source. `*token*` once removed ber/features/tokens.py.
    if p.suffix.lower() in SOURCE_SUFFIX:
        return False
    return any(p.match(g) for g in DENY_GLOB)


def copy_tree(src: Path, dst: Path, *, only_suffix: set[str] | None = None) -> None:
    """Copy src -> dst, skipping denied names/suffixes. Keeps the directory shape."""
    for item in sorted(src.rglob("*")):
        if any(denied(part) for part in [item, *item.relative_to(src).parents]):
            continue
        if denied(item):
            continue
        rel = item.relative_to(src)
        if item.is_dir():
            (dst / rel).mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            if only_suffix is not None and item.suffix.lower() not in only_suffix:
                continue
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst / rel)


def scan_secrets(root: Path) -> list[str]:
    hits = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIX:
            continue
        if p.stat().st_size > 4 << 20:  # the two TSVs; they are ID lists, not text to grep
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for rx, what in SECRET_PATTERNS:
            if rx.search(text):
                hits.append(f"{p.relative_to(root)}: looks like a {what}")
    return hits


def build(args: argparse.Namespace) -> int:
    root = args.repo_root.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stage = out_dir / "Grenuke_submission"
    if stage.exists():
        shutil.rmtree(stage)

    # ---- 1. the outputs, hash-gated -----------------------------------
    print("== outputs ==")
    pairs = [("matching_results.tsv", args.matching, args.expect_matching_sha),
             ("candidate_pairs.tsv", args.candidate, args.expect_candidate_sha)]
    for name, path, expect in pairs:
        if path is None or not path.is_file():
            print(f"FAIL: {name} not supplied or not found: {path}")
            return 1
        got = sha256(path)
        print(f"  {name}: {path.stat().st_size} bytes sha256={got}")
        if expect and got != expect.lower():
            print(f"FAIL: {name} sha256 mismatch\n  expected {expect.lower()}\n  got      {got}")
            print("  Refusing to package. This is the check that stops a stale file becoming the final submission.")
            return 1
        if not expect:
            print(f"  WARNING: no --expect-*-sha given for {name}; hash is recorded but not gated.")

    # ---- 2. the pairing audit -----------------------------------------
    if args.audit:
        if not args.test_dir:
            print("FAIL: --audit needs --test-dir")
            return 1
        print("== pairing audit ==")
        rc = run([sys.executable, str(Path(__file__).with_name("audit_matching.py")),
                  "--matching", str(args.matching), "--candidate", str(args.candidate),
                  "--test-dir", str(args.test_dir)])
        if rc != 0:
            print("FAIL: audit_matching.py reported hard issues. Not packaging.")
            return 1

    # ---- 3. stage the tree --------------------------------------------
    print("== staging ==")
    pkg = stage / "code/business_entity_resolution"
    (stage / "output").mkdir(parents=True)
    pkg.mkdir(parents=True)
    shutil.copy2(args.matching, stage / "output/matching_results.tsv")
    shutil.copy2(args.candidate, stage / "output/candidate_pairs.tsv")

    src_pkg = root / "code/business_entity_resolution"
    copy_tree(src_pkg / "src/ber", pkg / "src/ber")
    copy_tree(src_pkg / "tests", pkg / "tests")
    shutil.copy2(src_pkg / "pyproject.toml", pkg / "pyproject.toml")

    # the model chain: copied into the package, so the zip does not reference a developer path. Left out: the
    # research notes (*.md other than RECIPE.md) and pipeline/, the as-run records of the rented boxes and laptop
    # (machine paths, box addresses), except the two pipeline scripts the Composite B driver calls.
    copy_tree(root / "experiments/ameya/model-v1", pkg / "src/model_v1")
    for p in sorted((pkg / "src/model_v1").glob("*.md")):
        if p.name != "RECIPE.md":
            p.unlink()
    pipe = pkg / "src/model_v1/pipeline"
    shutil.rmtree(pipe, ignore_errors=True)
    pipe.mkdir(parents=True)
    for name in ("france_mixmdp.sh", "s2w.py"):
        shutil.copy2(root / "experiments/ameya/model-v1/pipeline" / name, pipe / name)
    here = Path(__file__).parent
    shutil.copy2(here / "audit_matching.py", pkg / "src/model_v1/audit_matching.py")
    # ce_llm_st.py imports Sachi's LoRA module `ce_llm` from experiments/sachi/ in the repository; in the package it
    # sits beside ce_llm_st.py, which is on PYTHONPATH (src/model_v1), so the import resolves without a sachi/ folder.
    shutil.copy2(root / "experiments/sachi/ce_llm.py", pkg / "src/model_v1/ce_llm.py")
    # Bakshi's 7B code and Composite B's driver: the top-level scripts of experiments/bakshi/box and the analysis
    # scripts the documentation cites. ops/ is left out: one-off orchestration of the rented boxes (fixed paths).
    box = root / "experiments/bakshi/box"
    (pkg / "src/box/analysis").mkdir(parents=True, exist_ok=True)
    # Shell scripts: only the driver; the others orchestrated the rented boxes and backups (machine paths).
    for f in sorted(box.glob("*.py")) + [box / "compositeB.sh"]:
        shutil.copy2(f, pkg / "src/box" / f.name)
    for f in sorted((box / "analysis").glob("*.py")):
        shutil.copy2(f, pkg / "src/box/analysis" / f.name)

    # the package's own docs: mine, not the v6 drafts
    shutil.copy2(here / "reproduce.sh", pkg / "reproduce.sh")
    shutil.copy2(here / "requirements.txt", pkg / "requirements.txt")
    shutil.copy2(here / "PACKAGE_README.md", pkg / "README.md")
    doc = args.doc or (here / "Documentation_template.md")
    shutil.copy2(doc, stage / "Documentation_template.md")
    # its typeset PDF and the figures the .md links to, when they sit beside it
    if (doc.parent / "Documentation_template.pdf").is_file():
        shutil.copy2(doc.parent / "Documentation_template.pdf", stage / "Documentation_template.pdf")
    if (doc.parent / "figures").is_dir():
        copy_tree(doc.parent / "figures", stage / "figures")

    # The organisers' validator is not ours to ship; the checks below run the repository's copy on the extracted outputs.
    validator = root / "student_resource/utils/validate_submission.py"

    n_files = sum(1 for p in stage.rglob("*") if p.is_file())
    print(f"  staged {n_files} files under {stage}")

    hits = scan_secrets(stage)
    if hits:
        print("FAIL: secret-shaped content in the staged tree:")
        for h in hits:
            print(f"  {h}")
        return 1
    print("  secret scan: clean")

    # ---- 4. manifest --------------------------------------------------
    members = sorted(p for p in stage.rglob("*") if p.is_file())
    lines = [f"{sha256(p)}  {p.relative_to(stage).as_posix()}" for p in members]
    (stage / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    members = sorted(p for p in stage.rglob("*") if p.is_file())  # now includes the manifest

    # ---- 5. zip (sorted entries, fixed timestamp -> stable bytes) ------
    zip_path = out_dir / "Grenuke_submission.zip"
    print("== zip ==")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in members:
            rel = p.relative_to(stage).as_posix()
            zi = zipfile.ZipInfo(rel, date_time=(2026, 9, 27, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            if rel.endswith(".sh"):
                zi.external_attr = 0o755 << 16
            z.writestr(zi, p.read_bytes())
    zip_sha = sha256(zip_path)
    print(f"  {zip_path}: {zip_path.stat().st_size} bytes sha256={zip_sha}")

    # ---- 6. extract elsewhere and verify ------------------------------
    print("== verify from the extracted archive ==")
    with tempfile.TemporaryDirectory(prefix="grenuke_zipcheck_") as td:
        ex = Path(td)
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            if bad:
                print(f"FAIL: corrupt archive member {bad}")
                return 1
            z.extractall(ex)
        manifest = {}
        for line in (ex / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
            if line.strip():
                digest, rel = line.split("  ", 1)
                manifest[rel] = digest
        mism = [rel for rel, d in manifest.items()
                if rel != "MANIFEST.sha256" and sha256(ex / rel) != d]
        if mism:
            print(f"FAIL: {len(mism)} extracted file(s) do not match the manifest: {mism[:5]}")
            return 1
        print(f"  manifest: {len(manifest)} entries, all extracted hashes match")

        required = REQUIRED + (REQUIRED_COMPOSITE_B if args.variant == "compositeB" else [])
        missing = [r for r in required if not (ex / r).is_file()]
        # Every 27 Sep final candidate is a "-dpc" package, i.e. it runs the stacked-rules pass after
        # acr_join. If the shipped model needs that pass, its scripts have to be IN the archive or the
        # reproduction is incomplete — so this is a hard check, not a warning.
        stack = ex / "code/business_entity_resolution/src/model_v1/stack/stack.sh"
        if args.stacked and not stack.is_file():
            missing.append("code/business_entity_resolution/src/model_v1/stack/stack.sh (--stacked was given)")
        if missing:
            print(f"FAIL: required path(s) missing from the archive: {missing}")
            return 1
        print(f"  required paths: all {len(required)} present"
              + (f"; stacked-rules pass shipped ({sum(1 for _ in stack.parent.glob('*.py'))} scripts)"
                 if args.stacked else ""))

        m_sha = sha256(ex / "output/matching_results.tsv")
        c_sha = sha256(ex / "output/candidate_pairs.tsv")
        print(f"  output/matching_results.tsv  sha256={m_sha}")
        print(f"  output/candidate_pairs.tsv   sha256={c_sha}")
        if args.expect_matching_sha and m_sha != args.expect_matching_sha.lower():
            print("FAIL: the archived matching file is not the expected bytes")
            return 1
        if args.expect_candidate_sha and c_sha != args.expect_candidate_sha.lower():
            print("FAIL: the archived candidate file is not the expected bytes")
            return 1

        ok = compileall.compile_dir(str(ex / "code"), quiet=2, force=True)
        print(f"  byte-compile of code/: {'ok' if ok else 'FAILED'}")
        if not ok:
            return 1

        # Byte-compiling is NOT enough: it compiles each file alone and never resolves an import, so a
        # MISSING module passes it. That is exactly how `*token*` once dropped ber/features/tokens.py and
        # produced an archive that compiled but could not run. These two checks are the ones that catch it,
        # and they run against the EXTRACTED tree with nothing on the path but the archive's own src.
        src = ex / "code/business_entity_resolution/src"
        env = {**os.environ, "PYTHONPATH": str(src), "PYTHONDONTWRITEBYTECODE": "1"}
        print("  import check (archive src only):")
        rc = subprocess.call(
            [sys.executable, "-c",
             "import importlib, pkgutil, sys\n"
             "import ber\n"
             "bad = []\n"
             "for m in pkgutil.walk_packages(ber.__path__, 'ber.'):\n"
             "    try:\n"
             "        importlib.import_module(m.name)\n"
             "    except Exception as e:\n"
             "        bad.append(f'{m.name}: {type(e).__name__}: {e}')\n"
             "print(f'    imported every ber submodule' if not bad else '    FAILED:')\n"
             "[print('     ', b) for b in bad]\n"
             "sys.exit(1 if bad else 0)"],
            env=env)
        if rc != 0:
            print("FAIL: the archived package does not import. A module is missing from the zip.")
            return 1

        print("  shipped tests against shipped src:")
        rc = run([sys.executable, "-m", "pytest", str(ex / "code/business_entity_resolution/tests"),
                  "-q", "--basetemp", str(ex / "_ptmp")], env=env)
        if rc != 0:
            print("FAIL: the archived tests do not pass against the archived source.")
            return 1
        shutil.rmtree(ex / "_ptmp", ignore_errors=True)

        if args.test_dir:
            # Both checks run on the EXTRACTED bytes, not on the staged inputs, so what is verified is
            # exactly what a grader would unzip.
            print("  [1/2] organiser validator on the extracted outputs:")
            rc = run([sys.executable, str(validator),
                      "--matching", str(ex / "output/matching_results.tsv"),
                      "--candidate", str(ex / "output/candidate_pairs.tsv"),
                      "--test-dir", str(args.test_dir)])
            if rc != 0:
                print("FAIL: the organiser validator rejected the extracted outputs")
                return 1
            # It is left without --check-ids on purpose: that check costs several GB, and the strict
            # audit below verifies ID existence far more cheaply. So the validator's "ID-existence
            # check is OFF" warning is covered, not ignored.
            print("  [2/2] strict audit on the extracted outputs:")
            rc = run([sys.executable, str(ex / "code/business_entity_resolution/src/model_v1/audit_matching.py"),
                      "--matching", str(ex / "output/matching_results.tsv"),
                      "--candidate", str(ex / "output/candidate_pairs.tsv"),
                      "--test-dir", str(args.test_dir)])
            if rc != 0:
                print("FAIL: the strict audit rejected the extracted outputs")
                return 1
        else:
            print("  WARNING: no --test-dir, so the archived outputs were NOT validated. "
                  "Do not ship a package built this way without running both checks separately.")

    summary = {
        "variant": args.variant,
        "stacked_rules": bool(args.stacked),
        "zip": {"path": str(zip_path), "bytes": zip_path.stat().st_size, "sha256": zip_sha},
        "output": {"matching_results.tsv": m_sha, "candidate_pairs.tsv": c_sha},
        "n_files": len(members),
        "required_paths_present": True,
    }
    (out_dir / "package_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print()
    print("PACKAGE OK")
    print(f"  zip sha256 {zip_sha}")
    print(f"  summary    {out_dir / 'package_manifest.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--matching", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--expect-matching-sha", default="")
    ap.add_argument("--expect-candidate-sha", default="")
    ap.add_argument("--out", type=Path, default=Path("dist"))
    ap.add_argument("--audit", action="store_true", help="run audit_matching.py before packaging")
    ap.add_argument("--test-dir", type=Path, default=None, help="dataset/test, for --audit and the validator")
    ap.add_argument("--doc", type=Path, default=None,
                    help="the filled Documentation_template.md for the zip root (default: the one in this folder); "
                         "a Documentation_template.pdf and a figures/ folder beside it are shipped too")
    ap.add_argument("--variant", default="compositeB",
                    help="which model these outputs came from, recorded in package_manifest.json so the "
                         "archive says what it ships (default: %(default)s)")
    ap.add_argument("--stacked", action="store_true",
                    help="the shipped model uses the stacked-rules ('-dpc') pass; requires stack/ in the archive")
    args = ap.parse_args()
    if args.variant == "compositeB":
        args.stacked = True   # both of Composite B's chains end in the stacked-rules pass
    if args.doc is not None and not args.doc.is_file():
        ap.error(f"--doc {args.doc} not found")
    return build(args)


if __name__ == "__main__":
    raise SystemExit(main())
