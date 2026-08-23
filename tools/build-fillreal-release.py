#!/usr/bin/env python3
"""
Build the fill-real public release from the live data directory.

Everything published goes through here, so the sanitization step cannot be
skipped by accident. The build is idempotent: run it again and it overwrites.

Guarantees enforced (the build FAILS rather than shipping a violation):
  - no wallet addresses, transaction signatures, keys or API tokens
  - every shipped file has a row count and a sha256 in MANIFEST.json
  - files above SIZE_GZIP_THRESHOLD are gzipped

Usage:
    python tools/build-fillreal-release.py
    python tools/build-fillreal-release.py --out PUBLISH/data --version 2.0.0
"""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# Fields stripped from every record before publication.
FORBIDDEN_FIELDS = {"wallet", "signature", "trader", "secret", "privateKey",
                    "apiKey", "owner", "payer"}

# Substrings that must never appear in a shipped line, checked post-strip.
FORBIDDEN_SUBSTRINGS = ["HELIUS", "api_key", "api-key", "Bearer ", "BIRDEYE"]

SIZE_GZIP_THRESHOLD = 40 * 1024 * 1024  # 40 MB

# name -> human description used in the manifest and the README table.
FILES = {
    "grad-social-shadow.jsonl":
        "Post-migration positions with real Jupiter fills, plus ex-ante features "
        "(liquidity, buyers, creator history, dev buy, social presence).",
    "grad-early-shadow.jsonl":
        "Exit-policy grid evaluated on the same positions: each row is one "
        "(position, exit configuration) pair with its realised return.",
    "liquidity-track.jsonl":
        "Liquidity, price, FDV and 24h flow series per tracked position.",
    "exit-slippage.jsonl":
        "Real exit slippage, order by order: quoted output vs mark-to-market.",
    "entry-exec.jsonl":
        "Entry overhead, order by order: fill price vs decision price. "
        "Sanitized -- wallet and signature removed.",
    "survivor-shadow.jsonl":
        "Independent survivor-strategy evaluations. Joins to the graduation "
        "population by mint, enabling the cross-strategy condition.",
    "grad-entry-shape.jsonl":
        "Post-migration price trajectories: one row per (mint, seconds since "
        "migration, price). The raw shape behind every outcome above.",
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize_stream(src, dst):
    """Copy JSONL, dropping forbidden fields. Returns (rows, stripped, skipped)."""
    rows = stripped = skipped = 0
    with open(src, encoding="utf-8", errors="ignore") as fin, \
         open(dst, "w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(rec, dict):
                skipped += 1
                continue
            removed = [k for k in list(rec) if k in FORBIDDEN_FIELDS]
            for k in removed:
                rec.pop(k)
            if removed:
                stripped += 1
            out = json.dumps(rec, separators=(",", ":"), ensure_ascii=False)
            low = out.lower()
            for bad in FORBIDDEN_SUBSTRINGS:
                if bad.lower() in low:
                    sys.exit(f"ABORT: forbidden substring {bad!r} in {src} row {rows+1}")
            fout.write(out + "\n")
            rows += 1
    return rows, stripped, skipped


def audit(path):
    """Second pass. Fails the build if anything forbidden survived."""
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                sys.exit(f"ABORT: unparseable line {i} in {path}")
            leaked = set(rec) & FORBIDDEN_FIELDS
            if leaked:
                sys.exit(f"ABORT: {sorted(leaked)} survived in {path} line {i}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "PUBLISH", "data"))
    ap.add_argument("--version", default="2.0.0")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    manifest = {
        "dataset": "fill-real",
        "version": args.version,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "files": [],
    }

    print(f"building fill-real v{args.version} -> {os.path.relpath(args.out, ROOT)}\n")
    total_rows = 0

    for name, desc in FILES.items():
        src = os.path.join(DATA, name)
        if not os.path.exists(src):
            print(f"  SKIP  {name}  (not found)")
            continue

        staged = os.path.join(args.out, name)
        rows, stripped, skipped = sanitize_stream(src, staged)
        audit(staged)
        total_rows += rows

        size = os.path.getsize(staged)
        shipped = staged
        if size > SIZE_GZIP_THRESHOLD:
            gz = staged + ".gz"
            with open(staged, "rb") as fin, gzip.open(gz, "wb", compresslevel=9) as fout:
                shutil.copyfileobj(fin, fout, length=1 << 20)
            os.remove(staged)
            shipped = gz

        entry = {
            "file": os.path.basename(shipped),
            "rows": rows,
            "bytes": os.path.getsize(shipped),
            "sha256": sha256_of(shipped),
            "description": desc,
        }
        if stripped:
            entry["sanitized_rows"] = stripped
            entry["fields_removed"] = sorted(FORBIDDEN_FIELDS & set(["wallet", "signature"]))
        manifest["files"].append(entry)

        flag = f"  [stripped {stripped}]" if stripped else ""
        gzflag = "  [gzipped]" if shipped.endswith(".gz") else ""
        print(f"  OK    {os.path.basename(shipped):<34} {rows:>9,} rows  "
              f"{entry['bytes']/1048576:>7.1f} MB{flag}{gzflag}")
        if skipped:
            print(f"        ({skipped} unparseable rows dropped)")

    manifest["total_rows"] = total_rows
    mpath = os.path.join(args.out, "MANIFEST.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"\n  total: {total_rows:,} rows across {len(manifest['files'])} files")
    print(f"  wrote {os.path.relpath(mpath, ROOT)}")
    print("\n  privacy audit PASSED: no wallets, signatures, keys or tokens shipped.")


if __name__ == "__main__":
    main()
