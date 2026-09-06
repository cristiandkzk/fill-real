# fill-real

**The same population of Solana tokens returns +36% when measured on quoted
prices and −69% when measured on the orders that actually executed.** This
repository publishes 1.75 million real fills, the measurement, and the code to
reproduce it.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21830479.svg)](https://doi.org/10.5281/zenodo.21830479)
[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-green.svg)](LICENSE-DATA)

🔗 **[Dune dashboard](https://dune.com/crdkzk1748/execution-cost-on-solana-the-median-pays-nothing-the-tail-pays-858x)** · **[Hugging Face dataset](https://huggingface.co/datasets/crdkzk/fill-real)** · **[Full report](REPORT.md)** · **[cristiandkzk@gmail.com](mailto:cristiandkzk@gmail.com)**

**An execution-grounded dataset for evaluating Solana trading strategies — and
evidence that screen-price backtests are systematically biased.**

Almost every publicly shared backtest of Solana token strategies is computed on
*screen price*: the value an aggregator reports on a polling interval. It is what
is available, and it looks reasonable.

The price at which an order **actually executes** is different. The difference is
not symmetric noise that averages out — it is a directional bias, and it is large
enough to invert conclusions.

Three results, each with a reproducible script and the raw data behind it:

- **Quoted prices distort returns by up to 105 percentage points, in both
  directions.** They made a ruinous entry rule look profitable, and separately
  made sound exit policies look far worse than they are.
- **An exhaustive sweep of 114 entry conditions over 36,736 real fills returned
  zero with a positive mean.** Not "the best one was marginal" — zero.
- **Round-trip friction is 10.7%, while the median token moves 8.3%** in its best
  15-minute window. When friction exceeds the asset's own movement, no
  exit-timing policy can rescue it.

> **[Known limitations](#read-before-using)** — four of them, including one
> that weakens the truncation result below. They are part of the finding, not a
> disclaimer appended to it.

> **v2.0 — August 2026.** 1.75 million rows, 25× the v1 release. See
> [CHANGELOG](CHANGELOG.md).

---

## The finding

The same population of tokens, measured both ways:

| Measurement | Screen price | Real fill |
|---|---:|---:|
| Migration-speed "ladder" (n≈24k / 21k) | **+36%** | **−69%** |
| Live entry gate cross-check | −42.8% | **−1.1%** |
| Live exit policy calibration | −29.8% | **−10.9%** |

**The bias runs in both directions, which is what makes it dangerous.** Screen
price made a ruinous entry rule look profitable. Separately, it made reactive exit
policies (stops, trailing stops) look far worse than they are — a snapshot grid
fires stops on transient dips that a real order would never have paid.

> Screen price penalizes reactive policies and rewards illusory ones.

**Pool liquidity does not lead price.** Across 150 collapses, the median lead
between a liquidity-drop threshold and a −25% price drop is **0 seconds**, and at
thresholds ≥15%, *zero* cases had any warning at all. Price is a function of pool
reserves — they are the same variable, not two signals. Median single-interval
gap: **97.2 percentage points**. This closes a whole family of "watch liquidity to
exit before the rug" designs.

**Real round-trip friction is 10.7%** (7.79% entry overhead, n=164; 2.91% exit
slippage, n=922), while the median token moves only **+8.3%** in the best
15-minute window. When friction exceeds the asset's median move, no exit-timing
policy can help.

📄 **[Full report →](REPORT.md)**

---

## New in v2

### 1. An exhaustive condition sweep: 0 of 114 have a positive mean

The obvious response to a negative result is *"you just haven't found the right
filter yet."* This tests that claim exhaustively rather than anecdotally.

Over **36,736 real-fill positions**, every combination of 10 ex-ante features ×
7 percentile cuts × 2 directions, plus 4 social booleans and one cross-strategy
condition — **114 distinct conditions** with n ≥ 100 each:

```
>>> CONDITIONS WITH POSITIVE MEAN: 0 of 114
```

| best conditions | n | median | **mean** | win% | ruin% |
|---|---:|---:|---:|---:|---:|
| baseline (all real fills) | 36,736 | −51.19% | **−33.59%** | 24.4 | 24.5 |
| `preBuyers >= 326` | 207 | −19.82% | **−3.25%** | 34.3 | 1.9 |
| `liqUsd >= 204,183` | 1,833 | +12.53% | **−7.33%** | 67.1 | 28.8 |
| `devBuySol < 0.0395` | 2,774 | −12.78% | **−8.14%** | 45.2 | 25.7 |

**A sweep that returns zero positives requires no multiple-comparison
correction, because there is nothing to discount.** Had one condition in 114
come back positive, the honest move would have been to treat it as noise. None
did. Reproduce it with
[`tools/sweep-conditions-realfill.py`](tools/sweep-conditions-realfill.py);
full table in [`results/sweep-conditions.md`](results/sweep-conditions.md).

**Two sub-results worth more than the headline:**

**Win rate and median are actively misleading here.** Three conditions win *more
than half* the time and every one of them loses money. `liqUsd >= 204,183` wins
**67.1%** of the time with a **+12.53% median** — and a **−7.33% mean**. The left
tail is fat enough that a two-thirds win rate is not enough. Report means.

**Ruin is predictable; profit is not.** `preBuyers >= 326` cuts the ruin rate
from 24.5% to **1.9%** — a genuine, large, reproducible effect. Its mean is still
−3.25%. The predictable set and the profitable set are disjoint.

### 2. The horizon-truncation bias, now bounded

v1 shipped a warning it could not quantify: price series truncate near 36
minutes, so *"any gate-level figure computed from this data is biased optimistic
by an amount that is not yet bounded."*

v2 ships **1,728 tokens with a full 190-minute horizon**, which bounds it:

| horizon | trimmed mean mult | median | share above 1× |
|---|---:|---:|---:|
| 36 min (the v1 cutoff) | 0.9143 | 0.2915 | 34.4% |
| 190 min | **0.5970** | **0.1017** | 19.3% |

**The same tokens lose a further 31.7 percentage points between minute 36 and
minute 190.** 66.3% keep falling after the cutoff.

*Read this as a paired estimate, not a universal constant.* The comparison is
**within-token** — the same 1,728 mints measured at two horizons — so the drift
cannot be a composition artifact. But this subsample was collected 16–21 Aug,
and that window is a **worse regime than the full population: −19.5 pp at the
shared 36-minute mark**. The direction and the existence of a large negative
drift are established on paired data; the magnitude is a point estimate from one
six-day window. Both figures are published so you can judge it yourself.

---

## Who this is for

- **Researchers backtesting Solana/memecoin strategies** who need real execution
  prices instead of screen prices to trust their results.
- **Quant teams and DeFi tooling builders** evaluating whether screen-price bias
  affects their own pipeline — the method here is reusable on any dataset.
- **Anyone citing a Solana backtest** who wants to sanity-check it against paired
  screen-vs-fill numbers before relying on it.

Not what this is: a trading strategy, a signal, or a multi-chain dataset. It is
measurement of one execution channel (Jupiter, Solana) — scoped and stated as such.

---

## The data

| File | Rows | Contents |
|---|---:|---|
| `grad-entry-shape.jsonl.gz` | 1,602,508 | **New in v2.** Post-migration price trajectories: one row per (mint, seconds since migration, price) across 40,427 mints. The raw shape behind every outcome below. |
| `liquidity-track.jsonl` | 65,861 | Liquidity, price, FDV and 24h flow series per position |
| `grad-early-shadow.jsonl` | 38,503 | **New in v2.** Exit-policy grid: one row per (position, exit configuration) with its realised return |
| `grad-social-shadow.jsonl` | 37,401 | Post-migration positions with real Jupiter fills and ex-ante features |
| `exit-slippage.jsonl` | 922 | Real exit slippage, order by order |
| `entry-exec.jsonl` | 759 | Entry overhead: fill vs. decision price |
| `survivor-shadow.jsonl` | 597 | **New in v2.** Independent survivor-strategy evaluations; joins by mint to enable cross-strategy conditions |

**1,746,551 rows total, ~74 MB.** Collected June–August 2026 from a live system
on Solana mainnet. Row counts and SHA-256 for every file are in
[`data/MANIFEST.json`](data/MANIFEST.json).

**Privacy:** the dataset contains no wallets, no keys and no transaction
signatures. The release is built by
[`tools/build-fillreal-release.py`](tools/build-fillreal-release.py), which strips
those fields, re-audits the output, and **fails the build** rather than shipping a
violation. Token mints and creator addresses are public on-chain data.

### Read before using

**1. Most price series still truncate at ~36 minutes.** v2 bounds this bias (see
above) but does not remove it: 83.5% of mints truncate near 36 min, only 4.3%
reach 190 min. Use the 190-minute subsample to correct, not to replace.

**2. The schema changes over time.** Older rows lack `screenMult` and
`exitImpactPct`; newer rows lack `devBuySol`, `migrateDelayMin` and the
`adaptive*` fields. Any loader must tolerate missing keys. Do not assume a fixed
column set.

**3. Single-operator data.** Execution telemetry comes from one wallet's order
flow. Fill quality may differ at other order sizes. Order sizes and observed price
impact are published so you can judge transferability.

**4. `posSol` in `exit-slippage.jsonl` is mark-to-market value at exit, not entry
size.** It satisfies `slipPct = jupOutSol / posSol − 1`. Grouping returns by it
measures causation backwards — a position that fell 99% is small *because* it
lost. Join to `entry-exec.jsonl` (`requestedSol`, `spentReal`) for entry size.

---

## Method

The obvious risk in two months of analysis over the same datasets is **data
fishing**: test sixty ideas, keep the one that looks good, never correct for the
fifty-nine you discarded. This was treated as a process problem, not a
good-intentions problem.

- **Pre-registration.** Every hypothesis is recorded with its prediction and a
  timestamp *before* the analysis runs. Only data after that mark counts as
  validation.
- **Negative results are recorded.** ~60 hypotheses closed or refuted, with their
  numbers. These are what close research lines and prevent repeated work.
- **Artifacts are recorded.** One calculation produced means of +19,216% before
  the reference price was found to be misspecified. It is written down, with cause
  and correction.
- **Caveats against each verdict are recorded**, not just the supporting evidence.
  The regime caveat on the truncation bound above is an example: it weakens the
  headline, and it is in the headline.

The pre-registration ledger pattern is included in this repository so it can be
reused.

---

## Status

Published as a public good. Released: the report, the dataset, and the analysis
tooling that reproduces the headline results.

**In progress:**
- Extended-horizon collection beyond 4.3% coverage, to turn the paired bound on
  limitation #1 into a population estimate.
- Open-source evaluation toolkit — run a candidate strategy against real Jupiter
  fills instead of screen prices, with paired comparison against a baseline.

---

## Where to get it

- **Hugging Face** (loader in two lines): https://huggingface.co/datasets/crdkzk/fill-real
- **Zenodo** (archived, citable): https://doi.org/10.5281/zenodo.21830480

---

## Citing

Cite the concept DOI unless you need to pin a specific release:

```
Díaz, Cristian Gonzalo. fill-real: an execution-grounded dataset for evaluating
Solana trading strategies. Zenodo. https://doi.org/10.5281/zenodo.21830479
```

The concept DOI [`10.5281/zenodo.21830479`](https://doi.org/10.5281/zenodo.21830479)
always resolves to the newest version. To cite exactly what you used, take the
version DOI from the release you downloaded.

---

## License

- **Code:** [MIT](LICENSE)
- **Data:** [CC BY 4.0](LICENSE-DATA) — use it freely, credit the source.

---

## Author

**Cristian Gonzalo Díaz** — [@cristiandkzk](https://github.com/cristiandkzk) ·
[cristiandkzk@gmail.com](mailto:cristiandkzk@gmail.com)

If you measure execution on Solana — at a venue, an aggregator or a desk — and
this method is useful to you, or wrong, write to me. Both are worth the email.

Built and operated the instrumented system this data comes from: live Solana
trading infrastructure with parallel shadow evaluation and real-fill measurement
via Jupiter.

The methodological discipline is the substance here: this work exists because the
measurement kept contradicting the analysis, and the contradictions were recorded
instead of discarded.
