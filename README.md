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

*Ground truth is defined as PS lift minus organic donor lift — structurally aligned with SC logic. See writeup for discussion of this caveat.*

---

## How Each Method Performs

| Level | Method | Estimate | Overstatement |
|---|---|---|---|
| 1 | Before/After (vs full pre) | 2,998 USD/day | +124% |
| 1 | Before/After (vs Nov base) | 2,370 USD/day | +77% |
| 1.5 | YoY (BF 2025 vs BF 2024) | 2,187 USD/day | +63% |
| 2 | BSTS (CausalImpact) | ~2,400 USD/day | +79% |
| 3 | BSTS+SC v01 (23 months) | ~1,340 USD/day | ~0% |
| 3 | BSTS+SC v02 (3 months) | ~1,340 USD/day | ~0% |
| 4 | Randomized holdout | — | Gold standard |

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


