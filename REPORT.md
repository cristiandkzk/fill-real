# The screen-price bias

> **v2.0 — August 2026.** Two results added: an exhaustive condition sweep that
> returns zero positives, and a paired bound on the horizon-truncation bias that
> v1 could only flag. Round-trip friction restated at 10.7%. See `CHANGELOG.md`.

**Two months measuring Solana memecoin strategies with real execution prices.**

The finding is not which strategy works. It is that **screen price overstates
systematically**, by a margin the same size as the edges people believe they have
found.

| | |
|---|---|
| **22,628** | graduations with real Jupiter fills |
| **18–40pp** | screen-vs-fill gap, three measurements |
| **11.4%** | real round-trip friction |

---

## The gap

A memecoin backtest is almost always computed on screen price: the value an
aggregator reports every 30 seconds. It is what is available and it looks
reasonable. But the price at which an order **actually executes** is different,
and the difference is not symmetric noise that averages out — it is a bias with a
fixed direction.

The same thing, measured both ways, three times, in independent contexts:

| Measurement | Screen price | Real fill |
|---|---:|---:|
| Migration-speed "ladder" (n≈24k / 21k) | **+36%** | **−69%** |
| Live graduation gate cross-check | −42.8% | **−1.1%** |
| Live exit policy calibration | −29.8% | **−10.9%** |

**The bias does not have a single sign, and that is what makes it dangerous.**
The ladder looked profitable on screen and was ruinous in execution. Reactive
policies looked ruinous on screen and were tolerable in execution: a grid of
snapshots fires stops and trailing stops on transient dips that a real order would
never have paid.

> Screen price penalizes reactive policies and rewards illusory ones.

---

## What real execution leaves

With 22,628 graduations measured at Jupiter fills, the full population returns
**−36.23%** per position (95% CI −37.71 to −34.75; hit rate 21.1%). Quality
filters recover a large part of that:

| Cumulative filter | n | mean | 95% CI | hit rate |
|---|---:|---:|---|---:|
| no filter | 22,628 | −36.23% | −37.7 / −34.8 | 21.1% |
| + creator with no history | 11,140 | −21.87% | −24.2 / −19.5 | 29.7% |
| + dev buy ≤ 0.5 SOL | 8,933 | −24.63% | −27.5 / −21.8 | 26.9% |
| + liquidity ≥ $15,000 | 2,915 | −4.61% | −9.9 / +0.7 | 43.9% |
| **+ buy/sell ratio ≥ 1.3** | **2,789** | **−3.79%** | **−9.3 / +1.7** | 44.8% |

Thirty-two percentage points recovered. The final result is not distinguishable
from zero — but it is not the disaster of the base population either.

### Tightening the filter makes the result worse and the feeling better

Raising the liquidity cut to 20k / 30k / 50k / 100k USD, the mean falls
(−7.04% → −7.89% → −9.53% → −10.34%) while the hit rate climbs from 43.9% to
58.2%.

**Anyone optimizing on percentage of winning trades will tighten the filter and
lose more money, convinced they are improving.** Ask for the raw mean.

---

## Friction is larger than the asset

Measured on live orders: entry costs **8.20%** in mean overhead (n=134) and exit
**3.17%** (n=705). Round trip: **11.4%**. Against that, how much does the token
actually move?

| Sell at minute | median net | winsorized mean | hit rate |
|---:|---:|---:|---:|
| 2 | −9.70% | −9.76% | 18.4% |
| 5 | −6.20% | −11.45% | 27.8% |
| 10 | −3.51% | −18.38% | 41.9% |
| **15 · best** | **−3.08%** | −20.39% | 45.5% |
| 20 | −4.60% | −22.32% | 45.2% |
| 30 | −26.06% | −27.39% | 42.3% |
| 35 | −59.69% | −30.12% | 40.2% |

No horizon between 2 and 35 minutes is profitable. And the best point explains
why: at minute 15 the median token **rises 8.3%** and friction takes **11.4%**.

> **Friction is larger than the asset's median move across the entire window.**
> No exit policy fixes that, because it is not a question of when to sell.

**v2 restatement.** On roughly 40% more orders the round trip measures **10.7%**
(7.79% entry overhead, n=164; 2.91% exit slippage, n=922), against 11.4% in v1.
The conclusion is unchanged and the margin is narrower: friction still exceeds
the 8.3% median move at the best exit point, by 2.4 points instead of 3.1.

---

## Rugs cannot be dodged on the way out

Intuition says pool liquidity should fall before price, and that watching it buys
time to exit. The lead between both signals was measured across 333 positions,
150 of which collapsed.

| Liquidity threshold | cases | median lead | with any warning |
|---|---:|---:|---:|
| 10% | 150 | 0 s | 30 |
| **15%** | 136 | 0 s | **0** |
| **20%** | 111 | 0 s | **0** |
| **30%** | 101 | 0 s | **0** |

Zero warning. At the last tick with price still healthy, liquidity had fallen a
**median of 0.0%**. The reason is mechanical: price **is** a function of pool
reserves. They are not two signals, they are the same variable — the lead is zero
by construction, not for lack of resolution.

The collapse, when it arrives, is total: **median jump of 97.2 percentage
points** between two consecutive readings, and 71.3% of cases jump more than 25
points at once. Verified in raw data — liquidity from $387,000 to $3,300 in under
a minute, with volume rising in the same window.

> **A −25% stop that realizes −69% is not badly calibrated: it never existed.**
> Price does not pass through −25%. And an event-driven guard would not save it
> either: if the pool empties in one transaction, there is no counterparty at any
> price.

---

## Why believe this

The obvious risk in two months of analysis over the same datasets is **data
fishing**: test sixty ideas, keep the one that stands out, never correct for the
fifty-nine discarded. This was treated as a process problem, not a
good-intentions problem.

- **Pre-registration.** Every hypothesis is recorded with its prediction and a
  timestamp *before* the analysis runs. Data after that mark is the only real
  validation set.
- **Negative results are recorded.** Around sixty hypotheses closed or refuted,
  with their numbers. These are the ones that close research lines and prevent
  repeated work.
- **Artifacts are recorded.** One calculation produced means of +19,216% before
  the reference price was found to be misspecified. It is written down, with
  cause and correction.
- **Caveats against each verdict are recorded**, not only supporting evidence.

> **Known and unresolved limitation:** all historical price series in this project
> end at ~36 minutes. The hard stop — which accounts for 31 of the percentage
> points lost — partly lives past that cutoff. The gate figures are therefore
> **biased optimistic by an amount not yet bounded**. The instrument to measure it
> exists and has started recording; the numbers above should be read with that
> caveat.

---

## The search is over: 0 of 114 conditions

Everything above invites one response: *you just haven't found the right filter
yet.* That is a testable claim, and testing it anecdotally is what produces
false discoveries. So it was tested exhaustively.

Over **36,736 real-fill positions**, an entry condition was built from every
combination of 10 ex-ante features, 7 percentile cuts and 2 directions, plus 4
social booleans and one cross-strategy condition. Conditions with fewer than 100
observations were discarded. **114 distinct conditions survived that filter.**

Only *ex-ante* features are eligible. A condition is a trading rule, so it may
use only what is known before the order is sent. Outcome fields — realised hold
time, peak multiple, exit reason — are excluded by construction. Conditioning on
them manufactures edge that cannot be traded.

| | n | median | **mean** | win% | ruin% |
|---|---:|---:|---:|---:|---:|
| baseline — all real fills | 36,736 | −51.19% | **−33.59%** | 24.4 | 24.5 |
| `preBuyers >= 326` | 207 | −19.82% | **−3.25%** | 34.3 | 1.9 |
| `liqUsd >= 204,183` | 1,833 | +12.53% | **−7.33%** | 67.1 | 28.8 |
| `devBuySol < 0.0395` | 2,774 | −12.78% | **−8.14%** | 45.2 | 25.7 |
| `liqUsd >= 14,823` | 9,163 | −4.37% | **−9.09%** | 48.2 | 18.0 |
| … | | | | | |
| `liqUsd < 29` | 9,073 | −89.85% | **−76.78%** | 3.3 | 49.5 |

```
>>> CONDITIONS WITH POSITIVE MEAN: 0 of 114
```

**This is the cleanest possible result with respect to fishing.** A sweep that
returns zero positives needs no multiple-comparison correction, because there is
nothing to discount. Had exactly one of 114 come back positive, the honest
reading would have been noise — that is roughly what a null grid of this size
produces by chance. None did.

The best condition, `preBuyers >= 326`, recovers **30.4 percentage points** over
the baseline and still sits at −3.25% on n=207. It is the same shape as every
other result in this report: large, real, reproducible improvements that do not
reach zero.

### The two sub-results are worth more than the headline

**Win rate and median are actively misleading here.** Three of the 114
conditions win *more than half* their trades. All three lose money.
`liqUsd >= 204,183` wins **67.1%** of the time with a **+12.53% median** — and
a **−7.33% mean**. Two thirds of trades profitable is not enough, because the
left tail is fat enough to pay for all of them. This is the same trap as
*"tightening the filter makes the result worse and the feeling better"*, now
measured on the widest possible grid. **Report means.**

**Ruin is predictable. Profit is not.** `preBuyers >= 326` cuts the rate of
total loss from 24.5% to **1.9%** — a thirteen-fold reduction, on a population
whose mean is still negative. The same holds for `preBuyers >= 484` (1.0% ruin,
−9.10% mean). It is genuinely possible to know which tokens will not go to zero.
It is not possible to turn that into money, because those same populations have
medians near −20%. **The predictable set and the profitable set are disjoint** —
and that dissociation, not the negative mean, is the finding a strategy designer
should take away.

Reproduce with `tools/sweep-conditions-realfill.py`; the full 114-row table is in
`results/sweep-conditions.md`.

---

## How much the 36-minute cutoff was hiding

v1 shipped a limitation it could not quantify: price series truncate near 36
minutes, so any figure computed from them is biased optimistic *by an amount
that is not yet bounded.* Extended collection now bounds it.

**1,728 tokens have a full 190-minute horizon.** Measured at both cutoffs:

| horizon | trimmed mean multiple | median | share above 1× |
|---|---:|---:|---:|
| 36 min — the v1 cutoff | 0.9143 | 0.2915 | 34.4% |
| 190 min | **0.5970** | **0.1017** | 19.3% |

**The same tokens lose a further 31.7 percentage points between minute 36 and
minute 190.** 66.3% of them keep falling past the cutoff. The share still above
water nearly halves.

**Read this as a paired estimate, not a universal constant.** Two things must be
said against it:

1. The comparison is **within-token** — the same 1,728 mints at two horizons —
   so the drift cannot be a composition artifact. This is what makes the
   direction trustworthy.
2. That subsample was collected 16–21 August, and **that window is a worse
   regime than the full population: −19.5 pp at the shared 36-minute mark**
   (trimmed mean 0.9143 vs 1.1089 across all 40,426 mints). The magnitude is
   therefore a point estimate from one six-day window, not a constant to apply
   elsewhere.

Coverage is the remaining gap: 83.5% of mints still truncate near 36 minutes and
only 4.3% reach 190. Use the long subsample to *correct* an estimate, not to
replace the population.

The practical consequence for anyone reusing this dataset — or any dataset built
the same way — is that **a truncated horizon flatters every strategy that holds
through the cutoff**, and by an amount comparable to the entire edge such
strategies claim to have.

---

## What a reader can take away

- A memecoin backtest on screen price is not a noisy version of reality: it is a
  biased version, and the bias is the size of the edge being sought.
- Hit rate and median move opposite to the mean when a filter is tightened.
  Optimizing for hit rate leads to losing more.
- Pool liquidity does not lead price. Any defense based on watching it is,
  mechanically, late.
- Before looking for an edge, measure real friction and compare it against the
  asset's median move. If friction is larger, the rest of the search is idle.
- When a filter search is run exhaustively rather than anecdotally, it can come
  back empty — 0 of 114 here. An empty sweep is a stronger result than a
  marginal positive, and it needs no correction for multiple comparisons.
- Being able to predict *ruin* is not the same as being able to predict *profit*.
  Here the two sets are disjoint, and only one of them was ever tradeable.
- Check what your data's horizon truncates. Cutting these series at 36 minutes
  instead of 190 flatters the same tokens by 31.7 percentage points.

---

## Data and reproducibility

- **Dataset:** https://huggingface.co/datasets/crdkzk/fill-real
- **Archived, citable:** https://doi.org/10.5281/zenodo.21830479 (concept DOI — always the newest version)
- **Code:** https://github.com/cristiandkzk/fill-real

Measurements on own orders and executions on Solana, June–August 2026. Real fills
via Jupiter. Confidence intervals at 95% by bootstrap. The migration-ladder and
simulation cross-check figures come from earlier runs of the same project and were
not recomputed for this report.

**Author:** Cristian Gonzalo Díaz — [@cristiandkzk](https://github.com/cristiandkzk)
