"""
generate_data.py — Measurement Maturity in Marketing Analytics

Single dataset: trend_shift
  Flat trend through Jun 2025, then +0.4%/day growth from Jul 1, 2025.
  By Nov pre-BF, Paid Search baseline is ~$1,871/day (+54% vs hypothetical flat).

  This single dataset drives the full maturity ladder:
  - Level 1 (Before/After): overstates because it cannot separate trend from lift
  - Level 2 (BSTS/Prophet): fail because they extrapolate flat pre-period into elevated Nov
  - Level 3 (BSTS+SC): robust because SC donors share the trend shift

REAL OBSERVED VALUES (seed=42, trend_shift):
  PS BF 2025 lift vs Nov 1-26 baseline:  126.7%  (planted 150% — noise shrinks it)
  Organic donor lift avg (observed):       55.0%  (Organic 72.9%, Direct 54.2%, Referral 34.6%, Social 58.5%)
  True paid increment:                     71.6%  = $1,340/day
  Nov pre-BF baseline:                    $1,871/day  (+54% above hypothetical flat)
  Full pre-period mean (Jan 2024-Nov 26): $1,243/day  (lower — includes flat 2024)
  BF window mean:                         $4,241/day

Ground truth always computed from actual generated data, never from planted parameters.
"""

import numpy as np
import pandas as pd
from pathlib import Path

BF2025_START = pd.Timestamp("2025-11-27")
BF2025_END   = pd.Timestamp("2025-12-02")

# Promotional calendar — (name, start, end, PS, Organic, Direct, Referral, Social, Email)
PROMO_EVENTS = [
    ("Valentine's 2024",  "2024-02-12","2024-02-14", 0.30,0.15,0.12,0.18,0.16,0.35),
    ("Spring Sale 2024",  "2024-03-18","2024-03-24", 0.35,0.18,0.15,0.20,0.18,0.40),
    ("Mother's Day 2024", "2024-05-10","2024-05-12", 0.28,0.14,0.11,0.16,0.15,0.32),
    ("BTS 2024",          "2024-08-05","2024-08-18", 0.35,0.20,0.16,0.22,0.20,0.38),
    ("Black Friday 2024", "2024-11-28","2024-12-03", 0.90,0.40,0.32,0.28,0.32,0.52),
    ("Holiday 2024",      "2024-12-16","2024-12-24", 0.32,0.16,0.13,0.18,0.17,0.38),
    ("Valentine's 2025",  "2025-02-11","2025-02-13", 0.30,0.15,0.12,0.18,0.16,0.35),
    ("Spring Sale 2025",  "2025-03-17","2025-03-23", 0.35,0.18,0.15,0.20,0.18,0.40),
    ("Mother's Day 2025", "2025-05-09","2025-05-11", 0.28,0.14,0.11,0.16,0.15,0.32),
    ("BTS 2025",          "2025-08-04","2025-08-17", 0.35,0.20,0.16,0.22,0.20,0.38),
    ("Holiday 2025",      "2025-12-16","2025-12-24", 0.32,0.16,0.13,0.18,0.17,0.38),
]

CHANNELS = {
    "Paid Search":    {"base":1200,"noise_cv":0.08,"weekly_dip":0.22,"q4_amp":0.20,"promo_idx":0,"bf_lift":1.50,"donor":False},
    "Organic Search": {"base": 900,"noise_cv":0.09,"weekly_dip":0.18,"q4_amp":0.15,"promo_idx":1,"bf_lift":0.65,"donor":True},
    "Direct":         {"base": 700,"noise_cv":0.08,"weekly_dip":0.20,"q4_amp":0.18,"promo_idx":2,"bf_lift":0.55,"donor":True},
    "Referral":       {"base": 400,"noise_cv":0.12,"weekly_dip":0.28,"q4_amp":0.12,"promo_idx":3,"bf_lift":0.45,"donor":True},
    "Social":         {"base": 250,"noise_cv":0.14,"weekly_dip":0.08,"q4_amp":0.14,"promo_idx":4,"bf_lift":0.55,"donor":True},
    "Email":          {"base": 350,"noise_cv":0.14,"weekly_dip":0.12,"q4_amp":0.22,"promo_idx":5,"bf_lift":0.85,"donor":False},
}

DONOR_CHANNELS   = [ch for ch,p in CHANNELS.items() if p["donor"]]
TREATED_CHANNEL  = "Paid Search"
EXCLUDED_CHANNEL = "Email"


def _q4_seasonal(date, amp):
    return amp * np.sin(2 * np.pi * (date.day_of_year - 150) / 365)

def _weekly_dip(date, dip):
    return -dip if date.dayofweek >= 5 else 0.0

def _promo_lift(date, promo_idx):
    total = 0.0
    for ev in PROMO_EVENTS:
        if pd.Timestamp(ev[1]) <= date <= pd.Timestamp(ev[2]):
            total += ev[3 + promo_idx]
    return total

def _trend(date):
    """
    Flat through Jun 30, 2025. From Jul 1, 2025: +0.4%/day compound growth.
    By Nov 26, 2025 (148 days later): multiplier = 1 + 0.004*148 = 1.592
    This creates a ~54% higher Nov baseline than hypothetical flat.
    BSTS/Prophet extrapolate the pre-period (mostly flat 2024) and under-forecast Nov.
    SC is robust: donors share the same trend, so their co-movement with PS
    in the SC pre-period (May-Nov 2025) already reflects the growth.
    """
    shift = pd.Timestamp("2025-07-01")
    return 1.0 + 0.004 * max((date - shift).days, 0)


def _make_series(params, dates, rng):
    out = np.zeros(len(dates))
    for i, d in enumerate(dates):
        lvl  = params["base"] * _trend(d)
        lvl *= (1 + _q4_seasonal(d, params["q4_amp"]))
        lvl *= (1 + _weekly_dip(d, params["weekly_dip"]))
        lvl  = max(lvl, 30)
        lvl *= (1 + _promo_lift(d, params["promo_idx"]))
        if BF2025_START <= d <= BF2025_END:
            lvl *= (1 + params["bf_lift"])
        noise = rng.normal(0, lvl * params["noise_cv"])
        if rng.random() < 0.015:
            noise = -lvl * rng.uniform(0.4, 0.7)
        out[i] = max(lvl + noise, 0)
    return out


def compute_ground_truth(df):
    """
    Compute ground truth from actual generated data.
    Baseline = Nov 1-26 (immediate pre-BF window).
    True increment = PS observed lift - average organic donor lift.
    """
    dates     = df["date"]
    bf_mask   = (dates >= BF2025_START) & (dates <= BF2025_END)
    pre_mask  = (dates >= "2025-11-01") & (dates < BF2025_START)
    full_pre  = dates < BF2025_START

    def mean(ch, mask):
        return df.loc[(df.channel==ch) & mask, "revenue_usd"].mean()

    ps_full  = mean(TREATED_CHANNEL, full_pre)
    ps_imm   = mean(TREATED_CHANNEL, pre_mask)
    ps_bf    = mean(TREATED_CHANNEL, bf_mask)
    ps_lift  = (ps_bf / ps_imm) - 1

    donor_lifts = {}
    for ch in DONOR_CHANNELS:
        donor_lifts[ch] = round(((mean(ch, bf_mask) / mean(ch, pre_mask)) - 1) * 100, 1)

    org_lift   = np.mean(list(donor_lifts.values())) / 100
    true_pct   = ps_lift - org_lift
    true_usd   = ps_imm * true_pct

    return {
        "ps_full_pre_mean_usd": round(ps_full, 2),
        "ps_imm_pre_mean_usd":  round(ps_imm,  2),
        "ps_bf_mean_usd":       round(ps_bf,   2),
        "ps_lift_observed_pct": round(ps_lift * 100, 1),
        "ps_lift_planted_pct":  150.0,
        "organic_lift_obs_pct": round(org_lift * 100, 1),
        "donor_lifts_obs_pct":  donor_lifts,
        "true_increment_pct":   round(true_pct * 100, 1),
        "true_increment_usd":   round(true_usd, 2),
    }


def generate_dataset(seed=42, data_dir=None):
    """
    Generate the trend-shift dataset.
    Returns (df, ground_truth dict).
    """
    rng   = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")

    rows = []
    for ch, params in CHANNELS.items():
        rev = _make_series(params, dates, rng)
        for d, r in zip(dates, rev):
            rows.append({"date": d, "channel": ch, "revenue_usd": round(r, 2)})

    df = pd.DataFrame(rows).sort_values(["date","channel"]).reset_index(drop=True)
    gt = compute_ground_truth(df)

    ground_truth = {
        "dataset":             "trend_shift",
        "trend_description":   "Flat Jan 2024 - Jun 2025, then +0.4%/day from Jul 1, 2025",
        "intervention":        "Black Friday 2025: Nov 27-Dec 2 (6 days)",
        "treated":             TREATED_CHANNEL,
        "donors":              ", ".join(DONOR_CHANNELS),
        "excluded":            f"{EXCLUDED_CHANNEL} (runs own BF campaigns)",
        **gt,
        "note": (
            f"Planted {gt['ps_lift_planted_pct']:.0f}% PS lift -> observed "
            f"{gt['ps_lift_observed_pct']}% (noise + Q4 baseline effects). "
            f"True increment = {gt['ps_lift_observed_pct']}% PS - "
            f"{gt['organic_lift_obs_pct']}% organic = "
            f"{gt['true_increment_pct']}% = ${gt['true_increment_usd']:,.0f}/day. "
            f"BSTS/Prophet overstate because they extrapolate flat pre-period into +54% Nov baseline."
        ),
    }

    if data_dir is not None:
        out = Path(data_dir)
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "dataset.csv", index=False)
        pd.DataFrame([{"k": k, "v": str(v)}
                      for k, v in ground_truth.items()]).to_csv(
            out / "ground_truth.csv", index=False)
        print(f"Saved: dataset.csv  ({len(df):,} rows)")

    return df, ground_truth


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent.parent / "data"
    df, gt = generate_dataset(seed=42, data_dir=data_dir)
    print(f"PS lift observed:   {gt['ps_lift_observed_pct']}%  (planted {gt['ps_lift_planted_pct']:.0f}%)")
    print(f"Organic lift obs:   {gt['organic_lift_obs_pct']}%")
    print(f"True increment:     {gt['true_increment_pct']}% = ${gt['true_increment_usd']:,.0f}/day")
    print(f"Donor lifts:        {gt['donor_lifts_obs_pct']}")
    print(f"Nov pre-BF base:    ${gt['ps_imm_pre_mean_usd']:,.0f}/day")
    print(f"Full pre mean:      ${gt['ps_full_pre_mean_usd']:,.0f}/day")
