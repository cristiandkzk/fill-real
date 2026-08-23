#!/usr/bin/env python3
"""
Exhaustive condition sweep over real-fill graduation outcomes.

This is the reproducible version of the result reported in HYPOTHESES.md 5:
across an exhaustive grid of entry conditions, ZERO give a positive mean return.

Why it matters: a sweep that returns zero positives needs no multiple-comparison
correction, because there is nothing to discount. That is the cleanest possible
evidence against the "there must be some filter that works" hypothesis.

Design decisions, stated so they can be audited:

  1. ONLY EX-ANTE FEATURES. A condition is a trading rule, so it may only use
     information available BEFORE the order is sent. Fields like `peakMult`,
     `holdMin`, `exitReason`, `exitImpactPct` and `screenMult` are outcomes and
     are deliberately excluded -- conditioning on them would manufacture edge.
     `entryImpactPct` IS included: it comes from the pre-trade quote.

  2. REAL FILLS ONLY (`realFill == true`). Screen-price rows are excluded; the
     whole point of this dataset is that the two differ enough to invert signs.

  3. MEAN, NOT MEDIAN, is the decision statistic. A strategy is paid its mean.
     Medians are reported alongside because several conditions lift the median
     while lowering the mean (see grad-liq-sweep-mediana-vs-media-trampa).

  4. MIN_N guards against conditions too rare to evaluate.

Usage:
    python tools/sweep-conditions-realfill.py
    python tools/sweep-conditions-realfill.py --json out.json --markdown out.md
"""

import argparse
import json
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

SHADOW = os.path.join(DATA, "grad-social-shadow.jsonl")
SURVIVOR = os.path.join(DATA, "survivor-shadow.jsonl")

# Percentile cuts applied to every numeric feature, in both directions.
PERCENTILES = [5, 10, 25, 50, 75, 90, 95]

# Ex-ante numeric features. See design decision 1.
NUMERIC_FEATURES = [
    "liqUsd",            # pool liquidity in USD at entry
    "bs5m",              # buy/sell ratio, 5 minute window
    "buys5m",
    "sells5m",
    "preBuyers",         # distinct buyers before entry
    "entryImpactPct",    # price impact of our own order, from the quote
    "devBuySol",         # SOL the creator bought of their own token
    "creatorPrior",      # creator's prior token count
    "creatorPriorGrad",  # creator's prior graduations
    "migrateDelayMin",   # minutes from launch to migration
]

# Social booleans, tested in both polarities.
BOOLEAN_FEATURES = ["tw", "tg", "web", "anySocial"]

MIN_N = 100
RUIN_THRESHOLD = -0.90  # netRet <= -90% counts as ruin


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_population():
    """Real-fill graduations with a realised return."""
    rows = load_jsonl(SHADOW)
    pop = [r for r in rows if r.get("realFill") and r.get("netRet") is not None]
    return rows, pop


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = min(len(sorted_vals) - 1, int(round(p / 100.0 * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def describe(returns):
    """Summary stats for a candidate condition's return population."""
    n = len(returns)
    ordered = sorted(returns)
    return {
        "n": n,
        "mean": st.mean(returns),
        "median": ordered[n // 2],
        "pct_positive": 100.0 * sum(1 for r in returns if r > 0) / n,
        "pct_ruin": 100.0 * sum(1 for r in returns if r <= RUIN_THRESHOLD) / n,
    }


def build_conditions(pop, survivor_mints):
    """Yield (label, predicate) for every condition in the grid."""
    conditions = []

    for feat in NUMERIC_FEATURES:
        vals = sorted(r[feat] for r in pop if isinstance(r.get(feat), (int, float)))
        if len(vals) < MIN_N:
            continue
        seen_cuts = set()
        for p in PERCENTILES:
            cut = percentile(vals, p)
            if cut is None or cut in seen_cuts:
                continue
            seen_cuts.add(cut)
            conditions.append((
                f"{feat} >= {cut:.6g}  (p{p})",
                lambda r, f=feat, c=cut: isinstance(r.get(f), (int, float)) and r[f] >= c,
            ))
            conditions.append((
                f"{feat} <  {cut:.6g}  (p{p})",
                lambda r, f=feat, c=cut: isinstance(r.get(f), (int, float)) and r[f] < c,
            ))

    for feat in BOOLEAN_FEATURES:
        conditions.append((f"{feat} == true",
                           lambda r, f=feat: bool(r.get(f)) is True))
        conditions.append((f"{feat} == false",
                           lambda r, f=feat: f in r and bool(r.get(f)) is False))

    if survivor_mints:
        conditions.append((
            "passed survivor gate  (cross-strategy)",
            lambda r: r.get("mint") in survivor_mints,
        ))

    return conditions


def temporal_holdout(rows):
    """Split a condition's rows in half by time. Confirmation must not be worse."""
    ordered = sorted(rows, key=lambda r: r.get("ts") or "")
    half = len(ordered) // 2
    old, new = ordered[:half], ordered[half:]
    if len(old) < 20 or len(new) < 20:
        return None
    return {
        "n_old": len(old), "mean_old": st.mean([r["netRet"] for r in old]),
        "n_new": len(new), "mean_new": st.mean([r["netRet"] for r in new]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full results as JSON")
    ap.add_argument("--markdown", help="write a markdown report")
    ap.add_argument("--min-n", type=int, default=MIN_N)
    args = ap.parse_args()

    all_rows, pop = load_population()
    if not pop:
        sys.exit(f"no real-fill rows found in {SHADOW}")

    survivor_mints = set()
    if os.path.exists(SURVIVOR):
        survivor_mints = {r["mint"] for r in load_jsonl(SURVIVOR) if r.get("mint")}

    base = describe([r["netRet"] for r in pop])

    print(f"source          : {os.path.relpath(SHADOW, ROOT)}")
    print(f"rows total      : {len(all_rows)}")
    print(f"real-fill rows  : {base['n']}")
    print(f"survivor mints  : {len(survivor_mints)}")
    print()
    print("BASELINE (every real-fill graduation)")
    print(f"  n={base['n']}  mean={base['mean']*100:+.2f}%  median={base['median']*100:+.2f}%"
          f"  win={base['pct_positive']:.1f}%  ruin={base['pct_ruin']:.1f}%")
    print()

    conditions = build_conditions(pop, survivor_mints)
    results = []
    skipped = 0

    for label, pred in conditions:
        rows = [r for r in pop if pred(r)]
        if len(rows) < args.min_n:
            skipped += 1
            continue
        stats = describe([r["netRet"] for r in rows])
        stats["label"] = label
        stats["lift_pp"] = (stats["mean"] - base["mean"]) * 100
        if stats["mean"] > 0:
            stats["holdout"] = temporal_holdout(rows)
        results.append(stats)

    results.sort(key=lambda s: s["mean"], reverse=True)
    positives = [s for s in results if s["mean"] > 0]

    print(f"conditions evaluated : {len(results)}   (skipped for n<{args.min_n}: {skipped})")
    print()
    print(f"{'condition':<44}{'n':>7}{'mean':>10}{'median':>10}{'win%':>8}{'ruin%':>8}{'lift pp':>9}")
    print("-" * 96)
    for s in results[:15]:
        print(f"{s['label']:<44}{s['n']:>7}{s['mean']*100:>9.2f}%{s['median']*100:>9.2f}%"
              f"{s['pct_positive']:>8.1f}{s['pct_ruin']:>8.1f}{s['lift_pp']:>9.2f}")
    print("  ...")
    for s in results[-3:]:
        print(f"{s['label']:<44}{s['n']:>7}{s['mean']*100:>9.2f}%{s['median']*100:>9.2f}%"
              f"{s['pct_positive']:>8.1f}{s['pct_ruin']:>8.1f}{s['lift_pp']:>9.2f}")

    print()
    print("=" * 96)
    print(f">>> CONDITIONS WITH POSITIVE MEAN: {len(positives)} of {len(results)}")
    print("=" * 96)
    if positives:
        print("\nEach positive needs a multiple-comparison discount and a temporal holdout:")
        for s in positives:
            print(f"  {s['label']}  n={s['n']}  mean={s['mean']*100:+.2f}%")
            if s.get("holdout"):
                h = s["holdout"]
                print(f"     holdout  old n={h['n_old']} {h['mean_old']*100:+.2f}%"
                      f"  ->  new n={h['n_new']} {h['mean_new']*100:+.2f}%")
    else:
        print("\nNo multiple-comparison correction is required: there is no positive")
        print("to discount. The best condition is the one closest to zero from below.")
        print(f"\n  best: {results[0]['label']}")
        print(f"        n={results[0]['n']}  mean={results[0]['mean']*100:+.2f}%"
              f"  (baseline {base['mean']*100:+.2f}%, lift {results[0]['lift_pp']:+.2f} pp)")

    payload = {
        "source": os.path.relpath(SHADOW, ROOT),
        "rows_total": len(all_rows),
        "baseline": base,
        "min_n": args.min_n,
        "percentiles": PERCENTILES,
        "numeric_features": NUMERIC_FEATURES,
        "boolean_features": BOOLEAN_FEATURES,
        "conditions_evaluated": len(results),
        "conditions_skipped_low_n": skipped,
        "positive_mean_count": len(positives),
        "results": results,
    }

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\nwrote {args.json}")

    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write("# Exhaustive condition sweep - real fills\n\n")
            fh.write(f"- Source: `{payload['source']}`\n")
            fh.write(f"- Real-fill rows: **{base['n']}**\n")
            fh.write(f"- Conditions evaluated: **{len(results)}** (min n = {args.min_n})\n")
            fh.write(f"- Conditions with positive mean: **{len(positives)}**\n\n")
            fh.write(f"Baseline: n={base['n']}, mean **{base['mean']*100:+.2f}%**, "
                     f"median {base['median']*100:+.2f}%, win {base['pct_positive']:.1f}%, "
                     f"ruin {base['pct_ruin']:.1f}%\n\n")
            fh.write("| condition | n | mean | median | win% | ruin% | lift pp |\n")
            fh.write("|---|---:|---:|---:|---:|---:|---:|\n")
            for s in results:
                fh.write(f"| `{s['label']}` | {s['n']} | {s['mean']*100:+.2f}% | "
                         f"{s['median']*100:+.2f}% | {s['pct_positive']:.1f} | "
                         f"{s['pct_ruin']:.1f} | {s['lift_pp']:+.2f} |\n")
        print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
