# Changelog

## v2.0.0 — 2026-08-21

**1,746,551 rows across 7 files (~74 MB), up from ~70,000 rows across 4 files in v1.**

### New results

- **Exhaustive condition sweep: 0 of 114 conditions have a positive mean.**
  10 ex-ante features × 7 percentile cuts × 2 directions, plus 4 social booleans
  and one cross-strategy condition, over 36,736 real-fill positions (n ≥ 100
  each). No multiple-comparison correction is required, because there is no
  positive to discount. Reproducible via `tools/sweep-conditions-realfill.py`.

- **The horizon-truncation bias of v1 is now bounded.** v1 flagged that series
  truncate near 36 minutes and called the resulting optimism "not yet bounded."
  On 1,728 tokens with a full 190-minute horizon, the *same tokens* lose a
  further **31.7 percentage points** of trimmed-mean multiple between minute 36
  and minute 190 (0.9143 → 0.5970); 66.3% keep falling past the cutoff.
  Stated as a paired estimate: that subsample's window (16–21 Aug) is a worse
  regime than the full population by −19.5 pp at the shared 36-minute mark, so
  the direction is established on within-token data while the magnitude is a
  point estimate from one six-day window.

- **Win rate and median are actively misleading in this asset class.** Three
  conditions win more than half the time and all lose money; `liqUsd >= 204,183`
  wins 67.1% with a +12.53% median and a −7.33% mean.

- **Ruin is predictable, profit is not.** `preBuyers >= 326` cuts ruin from
  24.5% to 1.9% with a mean still at −3.25%. The predictable set and the
  profitable set are disjoint.

### New data

- `grad-entry-shape.jsonl.gz` — 1,602,508 rows. Post-migration price
  trajectories across 40,427 mints. The raw shape behind every outcome in the
  dataset, and the basis for the truncation bound above.
- `grad-early-shadow.jsonl` — 38,503 rows. Exit-policy grid: one row per
  (position, exit configuration) with its realised return.
- `survivor-shadow.jsonl` — 597 rows. Independent survivor-strategy
  evaluations, joinable by mint to build cross-strategy conditions.

### Updated data

| file | v1 | v2 |
|---|---:|---:|
| `grad-social-shadow.jsonl` | 23,265 | 37,401 |
| `liquidity-track.jsonl` | 45,826 | 65,861 |
| `exit-slippage.jsonl` | 705 | 922 |
| `entry-exec.jsonl` | 547 | 759 |

### New tooling

- `tools/sweep-conditions-realfill.py` — reproduces the condition sweep. The v1
  release reported analyses that had no committed script; this closes that gap
  for the headline result.
- `tools/build-fillreal-release.py` — builds the release from the live data
  directory. Strips wallet/signature/key fields, re-audits the output, and fails
  the build rather than shipping a violation. Emits `MANIFEST.json` with row
  counts and SHA-256 per file.

### Corrections to v1

- **Round-trip friction restated: 10.7%**, from 11.4% in v1, on ~40% more data
  (7.79% entry overhead n=164 + 2.91% exit slippage n=922).
- **New caveat on `posSol` in `exit-slippage.jsonl`.** It is mark-to-market
  value *at exit*, not entry size — it satisfies `slipPct = jupOutSol/posSol − 1`.
  Any analysis grouping returns by it measures causation backwards, because a
  position that fell 99% is small *because* it lost. Entry size lives in
  `entry-exec.jsonl` (`requestedSol`, `spentReal`). Documented in the README
  limitations.

## v1.0.0 — 2026-08-06

Initial release. DOI [10.5281/zenodo.21830480](https://doi.org/10.5281/zenodo.21830480).
