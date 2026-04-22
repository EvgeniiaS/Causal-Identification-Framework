"""
utils.py — Shared utilities. All constants match actual generated data (seed=42, trend_shift).

Key observed values:
  PS BF 2025 lift vs Nov 1-26 baseline:  126.7%  (planted 150%)
  Organic donor lift avg:                 55.0%
  True paid increment:                    71.6%  = $1,340/day
  PS Nov 1-26 baseline:                  $1,871/day
  PS full pre-period mean:               $1,243/day
  BF window mean:                        $4,241/day
  Trend shift: flat through Jun 2025, then +0.4%/day from Jul 1
  Nov pre-BF is ~54% higher than hypothetical flat baseline
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

INTERVENTION_START = pd.Timestamp("2025-11-27")
INTERVENTION_END   = pd.Timestamp("2025-12-02")
DATA_START         = pd.Timestamp("2024-01-01")
DATA_END           = pd.Timestamp("2025-12-31")
TREND_SHIFT_START  = pd.Timestamp("2025-07-01")
BF2024_START       = pd.Timestamp("2024-11-28")
BF2024_END         = pd.Timestamp("2024-12-03")

# SC pre-period: 6.9 months (May 1 – Nov 26, 2025)
# Long enough for donor weight stability; donors share the trend so co-movement is strong
# BSTS alone needs ~2 years; BSTS+SC needs only 6.9 months here
SC_PRE_START = pd.Timestamp("2025-05-01")

TREATED_CHANNEL  = "Paid Search"
DONOR_CHANNELS   = ["Organic Search", "Direct", "Referral", "Social"]
EXCLUDED_CHANNEL = "Email"  # runs own BF promotional campaigns

DATA_DIR    = Path(__file__).resolve().parent.parent / "data"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = {
    "actual":         "#1a1a2e",
    "counterfactual": "#e94560",
    "intervention":   "#f5a623",
    "trend_shift":    "#e74c3c",
    "annotation":     "#666666",
    "grid":           "#f0f0f0",
    "level1":         "#e94560",
    "level2":         "#f5a623",
    "level3":         "#2980b9",
    "truth":          "#27ae60",
}


def set_style():
    plt.rcParams.update({
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.color":        PALETTE["grid"],
        "grid.linewidth":    0.8,
        "font.size":         11,
        "axes.titlesize":    12,
        "axes.titleweight":  "bold",
        "axes.labelsize":    11,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "legend.fontsize":   10,
    })


def load_dataset(data_dir=None):
    path = Path(data_dir or DATA_DIR) / "dataset.csv"
    return pd.read_csv(path, parse_dates=["date"]).sort_values(
        ["date","channel"]).reset_index(drop=True)


def get_treated_series(df):
    return (df[df.channel == TREATED_CHANNEL]
            .sort_values("date").set_index("date")["revenue_usd"])


def get_donor_panel(df, donors=None):
    return (df[df.channel.isin(donors or DONOR_CHANNELS)]
            .pivot_table(index="date", columns="channel",
                         values="revenue_usd", fill_value=0)
            .sort_index())


def add_intervention_band(ax, label=True, alpha=0.15):
    ax.axvspan(INTERVENTION_START, INTERVENTION_END,
               alpha=alpha, color=PALETTE["intervention"], zorder=1)
    if label:
        ymin, ymax = ax.get_ylim()
        ax.annotate(
            "Black Friday 2025\nNov 27-Dec 2",
            xy=(INTERVENTION_START + pd.Timedelta(days=2.5), ymax * 0.95),
            fontsize=8, color=PALETTE["annotation"], ha="center", va="top",
        )


def add_bf2024_band(ax, alpha=0.08):
    ax.axvspan(BF2024_START, BF2024_END, alpha=alpha, color="green", zorder=1)
    ymin, ymax = ax.get_ylim()
    ax.annotate(
        "BF 2024\n(pre-period)",
        xy=(BF2024_START + pd.Timedelta(days=3), ymax * 0.88),
        fontsize=8, color="green", ha="center", va="top",
    )


def add_trend_shift_line(ax, label=True):
    ax.axvline(TREND_SHIFT_START, color=PALETTE["trend_shift"],
               lw=1.5, ls="--", alpha=0.8, zorder=2)
    if label:
        ymin, ymax = ax.get_ylim()
        ax.annotate(
            "Trend shift\nJul 1, 2025",
            xy=(TREND_SHIFT_START + pd.Timedelta(days=5), ymax * 0.75),
            fontsize=8, color=PALETTE["trend_shift"], ha="left", va="top",
        )


def format_date_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def usd_formatter():
    return plt.FuncFormatter(lambda x, _: f"${x:,.0f}")


def save_figure(fig, name, dpi=150):
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"Saved: {path.name}")
    return path


def fit_synthetic_control(treated_series, donor_panel, pre_start=None, pre_end=None):
    """Fit SC weights by minimizing MSPE on normalized pre-period."""
    from scipy.optimize import minimize
    pre_end   = pre_end   or INTERVENTION_START - pd.Timedelta(days=1)
    pre_start = pre_start or treated_series.index.min()
    m      = (treated_series.index >= pre_start) & (treated_series.index <= pre_end)
    t_pre  = treated_series[m].values
    d_pre  = donor_panel.loc[m].values
    t_mu   = t_pre.mean()
    d_mu   = d_pre.mean(axis=0)
    res = minimize(
        fun=lambda W: np.sum(((t_pre/t_mu) - (d_pre/d_mu) @ W) ** 2),
        x0=np.ones(len(d_mu)) / len(d_mu),
        method="SLSQP",
        bounds=[(0,1)] * len(d_mu),
        constraints={"type":"eq","fun": lambda W: W.sum()-1},
        options={"ftol":1e-10,"maxiter":1000},
    )
    donors = list(donor_panel.columns)
    W      = res.x
    synth  = pd.Series(
        (donor_panel.values / d_mu) @ W * t_mu,
        index=donor_panel.index, name="synthetic",
    )
    pre_t  = treated_series[m].values
    pre_s  = synth[m].values
    mape   = np.mean(np.abs(pre_t - pre_s) / pre_t) * 100
    return dict(zip(donors, W)), synth, {"mape": round(mape,2)}


def compute_bf_effect(actual_series, counterfactual_series):
    """BF window effect: actual minus counterfactual, aligned by date index."""
    m   = (actual_series.index >= INTERVENTION_START) & \
          (actual_series.index <= INTERVENTION_END)
    act = actual_series[m].values
    # reindex counterfactual to match actual's index
    if hasattr(counterfactual_series, "reindex"):
        cf = counterfactual_series.reindex(actual_series.index)[m].values
    else:
        cf = counterfactual_series[m]
    gap = act - cf
    return {
        "actual_mean":  round(float(act.mean()), 2),
        "cf_mean":      round(float(cf.mean()),  2),
        "daily_effect": round(float(gap.mean()), 2),
        "total_effect": round(float(gap.sum()),  2),
        "pct_effect":   round(float(gap.mean() / cf.mean() * 100), 1),
    }
