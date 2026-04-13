"""
utils.py — Shared helpers for the Causal Identification Framework project.

Covers:
- Data loading and validation
- Intervention window constants
- Plotting defaults (consistent visual language across all notebooks)
- Pre/post period splitting
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

INTERVENTION_START = pd.Timestamp("2017-11-24")  # Black Friday
INTERVENTION_END   = pd.Timestamp("2017-11-27")  # Cyber Monday
PRE_PERIOD_START   = pd.Timestamp("2017-01-01")
POST_PERIOD_END    = pd.Timestamp("2017-12-31")

DATA_DIR = Path(__file__).parent.parent / "data"
FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ── Plot style ─────────────────────────────────────────────────────────────────

PALETTE = {
    "actual":      "#1a1a2e",
    "counterfactual": "#e94560",
    "ci":          "#e9456030",
    "intervention":"#f5a623",
    "annotation":  "#666666",
    "grid":        "#f0f0f0",
}

def set_style():
    """Apply consistent plot style across all notebooks."""
    plt.rcParams.update({
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.color":        PALETTE["grid"],
        "grid.linewidth":    0.8,
        "font.family":       "sans-serif",
        "font.size":         11,
        "axes.titlesize":    13,
        "axes.titleweight":  "bold",
        "axes.labelsize":    11,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "legend.frameon":    False,
        "legend.fontsize":   10,
    })

# ── Data loading ───────────────────────────────────────────────────────────────

def load_daily_agg(path=None) -> pd.DataFrame:
    """
    Load the daily aggregated revenue series.
    Expected columns: date, revenue_usd, transactions, sessions, pageviews
    """
    if path is None:
        path = DATA_DIR / "ga_daily_revenue_2017_agg.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    _validate_daily_agg(df)
    return df


def load_daily_by_channel(path=None) -> pd.DataFrame:
    """
    Load the channel/device-level daily data (for Synthetic Control donors).
    Expected columns: date, revenue_usd, transactions, sessions, pageviews, channel, device_type
    """
    if path is None:
        path = DATA_DIR / "ga_daily_revenue_2017.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values(["date", "channel"]).reset_index(drop=True)
    return df


def _validate_daily_agg(df: pd.DataFrame):
    required = {"date", "revenue_usd"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in aggregated data: {missing}")
    assert df["date"].is_monotonic_increasing, "Date column must be sorted ascending"
    assert df["date"].min() <= INTERVENTION_START, "Data must start before intervention"
    assert df["date"].max() >= INTERVENTION_END, "Data must extend past intervention"


# ── Period splitting ───────────────────────────────────────────────────────────

def split_periods(df: pd.DataFrame, date_col="date"):
    """
    Returns (pre_df, intervention_df, post_df) based on intervention constants.
    pre: before INTERVENTION_START
    intervention: INTERVENTION_START to INTERVENTION_END inclusive
    post: after INTERVENTION_END
    """
    pre  = df[df[date_col] < INTERVENTION_START].copy()
    intr = df[(df[date_col] >= INTERVENTION_START) & (df[date_col] <= INTERVENTION_END)].copy()
    post = df[df[date_col] > INTERVENTION_END].copy()
    return pre, intr, post


# ── Plotting helpers ───────────────────────────────────────────────────────────

def add_intervention_band(ax, label=True, alpha=0.15):
    """Shade the intervention window on any time-series axis."""
    ax.axvspan(INTERVENTION_START, INTERVENTION_END,
               alpha=alpha, color=PALETTE["intervention"], zorder=1)
    if label:
        ax.annotate(
            "Black Friday\nNov 24–27",
            xy=(INTERVENTION_START + pd.Timedelta(days=1.5),
                ax.get_ylim()[1] * 0.95),
            fontsize=9, color=PALETTE["annotation"],
            ha="center", va="top",
        )


def format_date_axis(ax, freq="MS"):
    """Apply clean monthly date formatting to x-axis."""
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)


def save_figure(fig, name: str, dpi=150):
    """Save figure to outputs/figures/ with consistent naming."""
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"Saved: {path}")
    return path


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_naive_lift(pre: pd.DataFrame, intervention: pd.DataFrame,
                       col="revenue_usd") -> dict:
    """
    Compute naive before/after lift estimate.
    Returns dict with pre_mean, intervention_mean, abs_lift, pct_lift.
    """
    pre_mean  = pre[col].mean()
    intr_mean = intervention[col].mean()
    return {
        "pre_mean":         round(pre_mean, 2),
        "intervention_mean": round(intr_mean, 2),
        "abs_lift":          round(intr_mean - pre_mean, 2),
        "pct_lift":          round((intr_mean - pre_mean) / pre_mean * 100, 1),
    }
