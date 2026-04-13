# Causal Identification Framework
### *Did Black Friday 2017 actually lift revenue — and how would we know?*

A practitioner's guide to causal inference for observational interventions, built on the [Google Analytics Sample Dataset](https://console.cloud.google.com/marketplace/product/obfuscated-ga360-data/obfuscated-ga360-data) (BigQuery public data). Three methods. One intervention. One honest answer about what we can and can't claim.

---

## The Problem

A campaign goes live. Revenue spikes. Someone in the meeting says: *"It worked."*

But did it? Revenue was already trending up. It's Q4. Black Friday was always going to be big. How much of that spike is the intervention — and how much would have happened anyway?

This is the **fundamental problem of causal inference**: we only observe one world. We see what happened *with* the intervention. We never see what would have happened *without* it. Every causal method is, at its core, a strategy for constructing that missing counterfactual.

This project walks through three strategies — from naive to rigorous — applied to a single real-world intervention: **Black Friday 2017** in the Google Merchandise Store.

---

## The Intervention

**Treated period:** November 24–27, 2017 (Black Friday through Cyber Monday)  
**Outcome:** Daily revenue (USD)  
**Data source:** `bigquery-public-data.google_analytics_sample.ga_sessions_*`  
**Pre-period:** January 1 – November 23, 2017  
**Post-period:** November 24 – December 31, 2017  

Black Friday is a clean natural experiment for methodological demonstration: it's a real, discrete, externally-timed event with a plausible effect on e-commerce revenue, and its timing is exogenous to the store's own actions.

---

## Three Methods, One Question

### Act 1 — Naive Before/After
[`notebooks/01_naive_before_after.ipynb`](notebooks/01_naive_before_after.ipynb)

The simplest possible approach: compare average daily revenue in the pre-period to the intervention window.

**What it gets right:** Fast. Intuitive. Easy to explain to a VP.  
**What it gets wrong:** Everything else. It ignores trend, seasonality, and the fact that Q4 revenue was already accelerating before Black Friday. We'll quantify the bias precisely — showing not just that naive is wrong, but *how wrong* and *in which direction*.

**Key output:** A bias decomposition showing how much of the naive "lift" estimate is attributable to pre-existing trend vs. the intervention itself.

---

### Act 2 — CausalImpact (Bayesian Structural Time Series)
[`notebooks/02_causal_impact_bsts.ipynb`](notebooks/02_causal_impact_bsts.ipynb)

Google's [CausalImpact](https://google.github.io/CausalImpact/) framework fits a Bayesian structural time series model on the pre-intervention period, then forecasts what revenue *would have been* without the intervention. The gap between forecast and actual is the causal estimate.

**What it gets right:** Handles trend and seasonality explicitly. Produces credible intervals, not just point estimates. Principled probabilistic framework.  
**What it gets wrong:** The counterfactual is model-dependent — if the BSTS model is misspecified, so is the estimate. Assumes no external shocks hit the post-period (other than the intervention). Black-box to non-technical stakeholders.

**Key output:** Counterfactual forecast with 95% credible intervals, cumulative impact estimate, posterior probability that the effect is real.

---

### Act 3 — Synthetic Control
[`notebooks/03_synthetic_control.ipynb`](notebooks/03_synthetic_control.ipynb)

Instead of a model-based counterfactual, Synthetic Control constructs a data-driven one: a weighted combination of "donor" control units (e.g., traffic channels or device types) whose pre-period trajectory matches the treated unit as closely as possible. Post-period divergence between treated and synthetic control = causal estimate.

**What it gets right:** Transparent. Assumption visible in the pre-period fit. No parametric model of the outcome process. Increasingly the preferred method in econometrics for single treated unit problems.  
**What it gets wrong:** Requires suitable donor units with good pre-period fit. Inference is non-standard (permutation-based). Can be sensitive to donor pool selection.

**Key output:** Synthetic control weights, pre-period fit quality, post-period gap plot, placebo tests for inference.

---

## Reconciliation: Which Estimate Do You Trust?

| | Naive B/A | CausalImpact | Synthetic Control |
|---|---|---|---|
| **Handles trend** | ✗ | ✓ | ✓ |
| **Handles seasonality** | ✗ | ✓ | Partial |
| **Transparent counterfactual** | ✗ | ✗ | ✓ |
| **Credible intervals** | ✗ | ✓ | Permutation |
| **Requires donor units** | ✗ | Optional | ✓ |
| **Explainable to non-technical stakeholders** | ✓ | Partial | ✓ |
| **Best for** | Never | Single series, long post-period | Single treated unit, good donors |

The three methods will produce different estimates. The reconciliation notebook section explains *why* — what each method is controlling for, what it's assuming away, and how to triangulate toward a defensible range rather than a single number.

**The practitioner's decision rule:**
- If you have good donor units → prefer Synthetic Control
- If you have no donors but a long, stable pre-period → CausalImpact
- If someone shows you a naive before/after → ask what the counterfactual is

---

## Repo Structure

```
causal-identification-framework/
├── README.md                          ← you are here
├── data/
│   └── bq_extract_instructions.md    ← how to pull the GA360 data from BigQuery
├── notebooks/
│   ├── 01_naive_before_after.ipynb
│   ├── 02_causal_impact_bsts.ipynb
│   └── 03_synthetic_control.ipynb
├── src/
│   └── utils.py                       ← shared data loading + plotting helpers
├── outputs/
│   └── figures/                       ← exported charts
└── writeup/
    └── causal_identification_framework.md   ← consultant-facing narrative
```

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/causal-identification-framework
cd causal-identification-framework
pip install -r requirements.txt
```

**Requirements:** Python 3.9+, `pandas`, `numpy`, `matplotlib`, `seaborn`, `causalimpact`, `pysyncon`, `google-cloud-bigquery` (for data extraction only)

See [`data/bq_extract_instructions.md`](data/bq_extract_instructions.md) for how to pull the dataset from BigQuery's free sandbox — no billing required for < 1TB/month queries.

---

## Why This Matters

This project exists because most "measurement" in marketing is naive before/after in a trench coat. Teams ship campaigns, draw vertical lines on revenue charts, and call it attribution. The methods here are not academic novelties — they are the difference between a defensible causal claim and a coincidence dressed up as a result.

If you're a data scientist working on growth, marketing, or product measurement, this framework gives you a reproducible template for any observational intervention where you can't run a randomized experiment.

---

## Author

Built as part of a practitioner portfolio in causal inference and marketing measurement.  
Questions, issues, or methodological disagreements welcome via GitHub Issues.
