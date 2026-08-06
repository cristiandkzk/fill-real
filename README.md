# fill-real

**An execution-grounded dataset for evaluating Solana trading strategies — and
evidence that screen-price backtests are systematically biased.**

Almost every publicly shared backtest of Solana token strategies is computed on
*screen price*: the value an aggregator reports on a polling interval. It is what
is available, and it looks reasonable.

The price at which an order **actually executes** is different. The difference is
not symmetric noise that averages out — it is a directional bias, and it is large
enough to invert conclusions.

This repository publishes the measurement, the data behind it, and the tooling to
reproduce it on your own strategy.

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

Two further results from the same data:

**Pool liquidity does not lead price.** Across 150 collapses, the median lead
between a liquidity-drop threshold and a −25% price drop is **0 seconds**, and at
thresholds ≥15%, *zero* cases had any warning at all. Price is a function of pool
reserves — they are the same variable, not two signals. Median single-interval
gap: **97.2 percentage points**. This closes a whole family of "watch liquidity to
exit before the rug" designs.

**Real round-trip friction is 11.4%** (8.20% entry overhead, n=134; 3.17% exit
slippage, n=705), while the median token moves only **+8.3%** in the best
15-minute window. When friction exceeds the asset's median move, no exit-timing
policy can help.

📄 **[Full report →](https://claude.ai/code/artifact/4ceac26b-5bce-4977-b5a4-e87f240366a9)**

---

## The data

| File | Rows | Contents |
|---|---:|---|
| `grad-social-shadow.jsonl` | 23,265 | Post-migration positions with real Jupiter fills |
| `liquidity-track.jsonl` | 45,826 | Liquidity and price series per position |
| `exit-slippage.jsonl` | 705 | Real exit slippage, order by order |
| `entry-exec.jsonl` | 547 | Entry overhead: fill vs. decision price |

Total ~14 MB. Collected June–August 2026 from a live system on Solana mainnet.

**Privacy:** the dataset contains no wallets, no keys and no transaction
signatures — the `wallet` and `signature` fields present in the raw collection
were stripped from `entry-exec.jsonl` before release. Token mints and creator
addresses are public on-chain data.

### ⚠️ Read before using: two limitations that will bite you

**1. Price series truncate at ~36 minutes.** Median series length is 36 min, p90
is 36 min, and **0% reach 60 min**. The hard-stop exit — which accounts for −31 of
the −36 percentage points lost in the base population — partly lives past that
cutoff. **Any gate-level figure computed from this data is biased optimistic by an
amount that is not yet bounded.** Extended-horizon collection is in progress.

**2. The schema changes over time.** Older rows lack `screenMult` and
`exitImpactPct`; newer rows lack `devBuySol`, `migrateDelayMin` and the
`adaptive*` fields. Any loader must tolerate missing keys. Do not assume a fixed
column set.

A third caveat worth stating: execution telemetry comes from a single wallet's
order flow. Fill quality may differ at other sizes. Order sizes and observed price
impact are published so you can judge transferability.

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

The pre-registration ledger pattern is included in this repository so it can be
reused.

---

## Status

Published as a public good. Currently released: the report and the dataset.

**In progress:**
- Open-source evaluation toolkit — run a candidate strategy against real Jupiter
  fills instead of screen prices, with paired comparison against a baseline.
- Extended-horizon trajectory collection to close limitation #1 above.

---

## Citing

If you use this dataset, please cite the Zenodo record: `[DOI PENDIENTE]`

---

## License

- **Code:** [MIT](LICENSE)
- **Data:** [CC BY 4.0](LICENSE-DATA) — use it freely, credit the source.

---

## Author

**Cristian Gonzalo Díaz** — [@cristiandkzk](https://github.com/cristiandkzk)

Built and operated the instrumented system this data comes from: live Solana
trading infrastructure with parallel shadow evaluation and real-fill measurement
via Jupiter.

The methodological discipline is the substance here: this work exists because the
measurement kept contradicting the analysis, and the contradictions were recorded
instead of discarded.
