# Measurement Maturity in Marketing Analytics
### *Why Before/After Lies, When Models Fail, and What BSTS + Synthetic Control (SC) Actually Gives You*

---

## Research Question

What is the **incremental** revenue contribution of Paid Search (PS) campaigns during Black Friday (BF) 2025, above organic BF demand?

---

## Ground Truth (seed=42, from actual generated data)

| Metric | Value |
|---|---|
| PS BF lift observed vs Nov 1-26 | 126.7% (planted 150% — noise shrinks it) |
| Organic donor lift avg | 55.0% (Organic 72.9%, Direct 54.2%, Referral 34.6%, Social 58.5%) |
| **True paid increment** | **71.6% = $1,340/day** |
| Nov 1-26 baseline | $1,871/day |
| Full pre-period mean (Jan 2024 – Nov 26) | $1,243/day |
| BF window mean | $4,241/day |

All method estimates are judged against **$1,340/day**.

---

## Single Dataset: Trend Shift

Flat through Jun 2025, then +0.4%/day from Jul 1, 2025.
Nov 2025 pre-BF baseline is +54% above hypothetical flat — +97% above Q1 2025.

This single trend shift exposes the failure mode of each method:

| Level | Method | Estimate | Error | Why |
|---|---|---|---|---|
| 1 | Before/After (vs full pre) | $2,998/day | +2.2x | Trend + organic demand + paid conflated |
| 1 | Before/After (vs Nov base) | $2,370/day | +1.8x | Organic demand + paid conflated |
| 2 | BSTS (CausalImpact) | ~$2,300-2,500/day | +70-85% | Extrapolates flat pre-period, flat BF counterfactual |
| 2 | Prophet | ~$2,300-2,500/day | +70-85% | Same failure mode |
| 2.5 | Prophet + regressors | Better than Prophet | Moderate up | Linear coeff, no SC constraints |
| 3 | BSTS+SC v01 (23 months) | ~$1,340/day | Near | SC absorbs trend; donors carry BF signal |
| 3 | BSTS+SC v02 (6.9 months) | ~$1,340/day | Near | 6.9 months sufficient with good donors |
| 4 | Randomized holdout | — | Minimum | Gold standard |

---

## Key Findings

**Level 2 failure has two components:**
1. Trend shift — model extrapolates flat pre-period into +54% elevated Nov baseline
2. Flat BF counterfactual — BF is a 6-day event; distributed across a 365-day annual seasonal
   cycle it contributes only ~$15/day of elevation. Parametric seasonal models cannot
   capture a 6-day spike from annual seasonality alone.

Both BSTS (with weekly + annual `bsts` state space) and Prophet (with `yearly_seasonality=True`)
are properly configured. The flat counterfactual is not a configuration problem — it is a
fundamental limitation of parametric seasonal models for short-duration events.

**Level 2.5 — Prophet with regressors:** Prophet supports adding donor channels as
regressors via `add_regressor()`. This is more principled than standalone Prophet —
organic donor values in the post-period push the counterfactual up, partially capturing
the BF organic demand spike. However it uses a static linear coefficient (no non-negativity
or sum-to-1 constraints), lacks Bayesian variable selection, and answers
'controlling for organic search, what is the PS lift?' rather than
'what would PS have been on organic demand alone?' — a weaker incrementality claim.

**Level 3 robustness:** SC donors (Organic Search, Direct, Referral, Social) all share the
+0.4%/day trend shift. Their co-movement with PS in the SC pre-period (r=0.69-0.83) already
embeds the growth. The SC counterfactual absorbs the trend and correctly isolates the paid increment.

---

## Channel Roles

| Channel | BF lift (observed) | Role |
|---|---|---|
| Paid Search | 126.7% | Treated unit |
| Organic Search | 72.9% | Donor — organic demand |
| Direct | 54.2% | Donor — organic demand |
| Referral | 34.6% | Donor — organic demand |
| Social | 58.5% | Donor — organic demand |
| Email | 95.0% | Excluded — runs own BF campaigns |

---

## Structure

```
measurement-maturity/
├── data/
│   ├── dataset.csv                  ← single trend-shift dataset (4,386 rows)
│   └── ground_truth.csv
├── notebooks/
│   ├── 00_data_generation.ipynb     ← trend shift explained, ground truth verified
│   ├── 01_before_after.ipynb        ← 2.2x overstatement, bias decomposition
│   ├── 02_time_series_models.ipynb  ← BSTS + Prophet: two failure modes documented
│   ├── 03_bsts_synthetic_control.ipynb  ← BSTS+SC: robust, two pre-period lengths
│   └── 04_maturity_ladder.ipynb     ← all estimates vs $1,340 ground truth
├── src/
│   ├── generate_data.py             ← ground truth computed from actual data
│   ├── utils.py                     ← shared constants, helpers, SC solver
│   └── causal_impact_wrapper.R      ← public BSTS+SC wrapper with MAPE tracking
└── writeup/
    └── measurement_maturity.md
```

---

## Setup

```bash
pip install -r requirements.txt
jupyter lab
```

**R required** for notebooks 02 and 03:
- Download from https://cran.r-project.org/bin/macosx/ (arm64 for Apple Silicon)
- R packages (`CausalImpact`, `bsts`, `zoo`, `data.table`, `scales`) install automatically on first run

Run notebooks in order: `00` → `01` → `02` → `03` → `04`

