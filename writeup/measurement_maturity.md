# Measurement Maturity in Marketing Analytics
## *Why Before/After Lies, When Models Fail, and What BSTS+SC Actually Gives You*

**Dataset:** Synthetic, single trend-shift scenario (seed=42)  
**Research question:** What is the incremental revenue contribution of Paid Search campaigns during Black Friday 2025, above organic BF demand?

---

## Ground Truth

All numbers are computed from the actual generated dataset, not from planted parameters.
Planted 150% PS lift → observed 126.7% due to noise and Q4 seasonality baseline effects.

| Metric | Value |
|---|---|
| PS BF lift observed vs Nov 1-26 | 126.7% |
| Organic donor lift avg | 55.0% (Organic 72.9%, Direct 54.2%, Referral 34.6%, Social 58.5%) |
| **True paid increment** | **71.6% = $1,340/day** |
| Nov 1-26 baseline | $1,871/day |
| Full pre-period mean | $1,243/day |
| BF window mean | $4,241/day |

True increment = PS observed lift (126.7%) minus average organic donor lift (55.0%) = 71.6% of the Nov 1-26 baseline. This is the number every method is trying to recover.

---

## Dataset Design

Revenue is flat through Jun 2025, then grows at +0.4%/day from Jul 1, 2025. By November, the Paid Search baseline is $1,871/day — +54% above the hypothetical flat level, +97% above Q1 2025.

**Why trend-shift, not flat:** A flat dataset is the easy case where all methods eventually work. The trend shift creates the realistic scenario any company with double-digit YoY growth faces, and exposes the failure modes at each level cleanly.

**Quarterly progression (Paid Search):**

| Period | Mean revenue | Notes |
|---|---|---|
| Q1 2025 | $950/day | Pre-shift baseline |
| Q2 2025 | $1,076/day | Pre-shift |
| Q3 2025 | $1,637/day | Shift underway (+72% above Q1) |
| Oct 2025 | $1,754/day | Still accelerating |
| Nov 1-26 | $1,871/day | Pre-BF baseline (+97% above Q1) |
| BF 2025 | $4,241/day | Intervention window |

---

## Why Randomization Is the Gold Standard

If you can run a geo holdout or user-level split before the campaign, do it. A randomized design creates the counterfactual by observation, not by modeling. No assumptions about trend stability, donor independence, or seasonal structure. The causal estimate is unbiased by construction.

Every observational method below exists for when randomization was not possible.

---

## The Maturity Ladder

### Level 1: Before/After

**Estimate:** $2,998/day vs full pre-period (+2.2x) | $2,370/day vs Nov baseline (+1.8x)

Before/after compares the BF window mean to a pre-period average. It cannot separate:
1. Trend growth that was already happening from Jul 1 onward
2. Organic BF consumer demand lifting all channels
3. Paid campaign increment

**Decomposition of $2,998 naive lift (vs full pre-period):**
- Trend growth: ~$628/day — Jul-Nov acceleration that would have happened anyway
- Organic BF demand: ~$1,030/day — consumers in BF mode across all touchpoints
- Paid increment (true): ~$1,340/day — what campaigns actually contributed

The estimate is 2.2x the true value. This overstatement is not random — it is structural and directional. Before/after always overstates paid effectiveness during seasonal events with growth.

**Window sensitivity:** Choosing full pre-period vs Nov baseline changes the reported lift from 241% to 127%. This is not measurement variability — it is arbitrary framing.

---

### Level 2: BSTS and Prophet

**Estimates:** ~$2,300-2,500/day — approximately +70-85% above $1,340 true

Both models are properly configured with weekly and annual seasonality:
- **CausalImpact:** `bsts` state space — local level + `AddSeasonal(nseasons=7)` (weekly) + `AddSeasonal(nseasons=52, season.duration=7)` (annual, 52-week cycle). Pre-period includes BF 2024.
- **Prophet:** `yearly_seasonality=True` (Fourier terms) + `weekly_seasonality=True`. BF 2024 in training data.

**Two failure modes — both present on this dataset:**

**Failure 1 — Trend shift:** Both models learn the pre-period dynamics (mostly flat through mid-2025) and extrapolate forward. The actual Nov 2025 baseline is $1,871/day; both models forecast ~$1,100-1,300/day. The counterfactual under-forecasts November, and the gap is attributed to BF when it is really trend growth.

**Failure 2 — Flat BF counterfactual:** The BF spike is a 6-day event. Distributed across a 365-day annual seasonal cycle, it contributes approximately $15/day of elevation to the annual seasonal component. The spike is too narrow relative to the cycle length to register meaningfully in parametric seasonal models. Both models show a flat-to-moderate counterfactual through the BF window — they correctly forecast "what PS would do without BF" but cannot anticipate that 6 days of organic BF consumer demand will materialize, because that demand is the event itself, not a seasonal regularity.

**This is not a configuration problem.** Annual seasonality is properly set up. The flat BF counterfactual is the correct behavior: the model says "without BF, revenue continues its learned trajectory." It has no mechanism to know that short-duration organic consumer behavior will spike because it is embedded in, not separable from, the intervention.

**What these models cannot do even when valid:** They estimate total BF impact vs seasonal baseline — organic demand + paid increment combined. They cannot isolate the paid-specific contribution without donor channels.

---

### Level 3: BSTS + Synthetic Control

**Estimates:** ~$1,340/day — near true value for both pre-period lengths

BSTS+SC is one model, not two. Organic demand channels (Organic Search, Direct, Referral, Social) are passed as covariates directly into the CausalImpact BSTS model. Spike-and-slab priors (Bayesian variable selection) learn which donors best explain Paid Search in the pre-period. The donor-weighted counterfactual represents what PS would have done on organic demand alone — without paid campaigns.

**Why SC is robust to the trend shift:**  
All donors share the same +0.4%/day growth from Jul 1. Their co-movement with Paid Search in the SC pre-period (May-Nov 2025) already embeds the growth — correlations are r=0.69-0.83. The model learns donor weights that track the elevated Nov level. The SC counterfactual correctly captures the $1,871 organic baseline, and only the excess above it is attributed to the intervention.

**Why SC does not have the flat BF counterfactual problem:**  
During the BF 2025 post-period window, donor channels are also spiking (organic demand: +34-73%). These elevated donor covariate values directly push the SC counterfactual up — it is not smoothed across 365 days, it is the actual donor signal at that specific moment. This is the fundamental advantage of the covariate approach over parametric seasonality for short-duration events.

**Why 6.9 months is sufficient:**  
Standalone BSTS needs ~2 full years to observe a Q4 seasonal cycle. With SC donors, the model borrows their seasonal history. The 6.9-month SC pre-period (May-Nov 2025) fully captures the trend-shift period; donor co-movement is strong (r=0.69-0.83), pre-period MAPE is validated before trusting the counterfactual.

**Implementation:** Uses `causal_impact_with_covariates()` from `src/causal_impact_wrapper.R` — a public wrapper that adds:
- MAPE/WMAPE tracking across model iterations (saved to `fit_metrics.csv`)
- Vacation period exclusion (anomalous periods removed from BSTS training)
- Reversion period monitoring (does effect persist or decay post-intervention?)
- Three trend model options: local level, local linear trend, semi-local linear trend

**Donor selection:**
- Email excluded: runs own BF promotional campaigns — not organic demand
- All other channels included: share organic BF consumer behavior, strong co-movement with PS

**Limitations:**
- 4 donors is a thin pool; production analyses use 10-30+ units for stable weights
- Donor organic BF lift slightly pulls counterfactual up → slight underestimate of paid increment
- Assumes donor channels are exogenous to paid campaigns

---

## Full Results Summary

| Level | Method | Estimate | vs $1,340 | Root cause |
|---|---|---|---|---|
| 1 | Before/After (vs full pre) | $2,998/day | +2.2x | Trend + organic demand conflated |
| 1 | Before/After (vs Nov) | $2,370/day | +1.8x | Organic demand + paid conflated |
| 2 | BSTS (annual seasonality) | ~$2,300-2,500/day | +70-85% | Trend confound + flat BF counterfactual |
| 2 | Prophet (annual seasonality) | ~$2,300-2,500/day | +70-85% | Same failure modes |
| 3 | BSTS+SC v01 (23 months) | ~$1,340/day | Near | SC absorbs trend; donors carry BF signal |
| 3 | BSTS+SC v02 (6.9 months) | ~$1,340/day | Near | 6.9 months sufficient with good donors |
| 4 | Randomized holdout | — | Minimum | Gold standard |

---

## Business Implication

The trend shift amplifies the Level 1 error to 2.2x — not unusual for channels with double-digit YoY growth. A team using before/after to evaluate BF Paid Search campaigns and reporting 2.2x the true paid contribution will over-invest in paid channels and under-credit organic, content, and brand — channels that before/after cannot see.

BSTS+SC recovers the true paid increment even under trend shift, enabling correct budget allocation. Level 2 methods fail here despite proper annual seasonality configuration — the trend shift is the primary driver, and the flat BF counterfactual compounds the error.

---

## Reproducibility

```bash
pip install -r requirements.txt
jupyter lab
```

R required for notebooks 02 and 03: https://cran.r-project.org/bin/macosx/  
R packages install automatically on first run.

Run in order: `00` → `01` → `02` → `03` → `04`
