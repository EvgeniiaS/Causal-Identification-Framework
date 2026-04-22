# Measurement Maturity in Marketing Analytics
### Case study for Decision Intelligence — Pillar II: Causal Inference

*"Did that actually work?"*

This project is a companion to the Decision Intelligence framework, Pillar II. It works through the campaign measurement problem using synthetic data with a known ground truth — making it possible to measure exactly how wrong each method is, which is impossible with real data.

---

## The Problem

A Black Friday Paid Search campaign ran. Revenue spiked. How much of that spike came from the campaigns, and how much would have happened from organic consumer demand anyway?

This is not a Black Friday question. It is the standard campaign measurement question, made concrete by an example where the failure modes are easy to see.

---

## Ground Truth (seed=42, from actual generated data)

| | |
|---|---|
| True paid increment | **1,340 USD/day = 71.6% of Nov baseline** |
| PS BF lift observed | 126.7% vs Nov 1-26 |
| Organic donor lift avg | 55.0% |
| Nov 1-26 baseline | 1,871 USD/day |
| BF window mean | 4,241 USD/day |

*Ground truth is defined as PS lift minus organic donor lift. This definition is aligned with SC logic and therefore favors donor-based methods; see writeup for discussion.*

---

## How Each Method Performs

| Level | Method | Estimate | Overstatement |
|---|---|---|---|
| 1 | Before/After (vs full pre) | 2,998 USD/day | +124% |
| 1 | Before/After (vs Nov base) | 2,370 USD/day | +77% |
| 1.5 | YoY (BF 2025 vs BF 2024) | 2,187 USD/day | +63% |
| 2 | BSTS (CausalImpact) | 2,348 USD/day | +75% |
| 3 | BSTS+SC v01 (23 months) | ~1,340 USD/day | ~0% |
| 3 | BSTS+SC v02 (7 months) | ~1,340 USD/day | ~0% |
| 4 | Randomized holdout | — | Gold standard |

---

## Method Implementation

### Level 2 — BSTS (CausalImpact)

- Model: local level + weekly + annual seasonality
- Trained on full pre-period (includes prior BF)
- No explicit holiday/event term for Black Friday

**Limitation**

- Cannot model demand spikes that are not predictable from historical seasonal structure
- Attributes unexplained spikes to treatment

---

### Level 3 — BSTS + SC (Regression-based Synthetic Control)

Implemented as:

> **BSTS with contemporaneous covariates (organic channels)**

**Important**

- This is **not classical Abadie-style Synthetic Control**
- It is a **Bayesian regression with time-series structure**

**Covariates (donor channels)**

- Organic Search  
- Direct  
- Referral  
- Social  

**Excluded**

- Email (campaign-driven; violates exogeneity)

---

## Key Assumptions

1. **Donor exogeneity**  
   Donor channels are not affected by Paid Search

2. **No interference (SUTVA)**  
   No spillover effects between treated and donor channels

3. **Contemporaneous relationships**  
   Donor signals align in time with Paid Search (no strong lag effects)

4. **Stable relationships**  
   Pre-period relationships hold in the post-period

5. **Sufficient pre-period fit**  
   Counterfactual must accurately track pre-period behavior

6. **Donor independence**  
   Multicollinearity may affect stability of estimates

---

## Validation Approach

A causal estimate is only credible if it passes:

- **Pre-period fit diagnostics**  
  (MAPE + residual checks)

- **Placebo test**  
  Apply pseudo-intervention in pre-period

- **Sensitivity analysis**  
  Re-run excluding each donor

---

## Failure Modes

The method may fail when:

- Donors are contaminated by treatment
- Channels are weakly correlated
- Structural breaks occur
- Lagged effects are ignored
- Donors are highly collinear
- Intervention timing is unclear

---

## Interpretation

- Standard approaches (Before/After, YoY, BSTS) **overestimate impact by 60–120%** in this scenario  
- BSTS fails because it cannot separate demand shocks from treatment  
- Regression-based SC improves estimates by conditioning on observed demand signals  

---

## Relationship to Other Methods

- **Experiments** → ground truth  
- **BSTS + SC** → short-term causal estimate  
- **MMM** → long-term budget allocation  

These methods are complementary.

---


## Dataset

Single trend-shift scenario: flat through Jun 2025, then +0.4%/day from Jul 1, 2025. Nov 2025 pre-BF baseline is 61% above the prior year. This growth acceleration is what exposes the failure mode of every observational method.

---

## Channel Roles

| Channel | BF lift | Role |
|---|---|---|
| Paid Search | 126.7% | Treated |
| Organic Search | 72.9% | Donor channel |
| Direct | 54.2% | Donor channel |
| Referral | 34.6% | Donor channel |
| Social | 58.5% | Donor channel |
| Email | 95.0% | Excluded — runs own BF campaigns |

---

## Structure

```
measurement-maturity/
├── data/
│   ├── dataset.csv
│   └── ground_truth.csv
├── notebooks/
│   ├── 00_data_generation.ipynb     ← dataset and ground truth
│   ├── 01_before_after.ipynb        ← Level 1 & 1.5
│   ├── 02_time_series_models.ipynb  ← Level 2: BSTS
│   ├── 03_bsts_synthetic_control.ipynb  ← Level 3: BSTS+SC
│   └── 04_maturity_ladder.ipynb     ← all methods vs ground truth
├── src/
│   ├── generate_data.py
│   ├── utils.py
│   └── causal_impact_wrapper.R
└── writeup/
    └── measurement_maturity.md      ← full case study narrative
```

---

## Setup

```bash
pip install -r requirements.txt
jupyter lab
```

R required for notebooks 02–03: https://cran.r-project.org/bin/macosx/  
R packages install automatically on first run.  
Run in order: `00` → `01` → `02` → `03` → `04`


