# Did That Actually Work?
## A Case Study in Campaign Measurement

---

Black Friday arrived. The Paid Search team did what teams do: raised bids, expanded budgets, launched BF-specific creatives. Revenue spiked — up 127% over the November baseline. The team reported the number. Leadership was pleased. Budget was renewed.

But here is the question nobody asked: how much of that spike came from the campaign decisions, and how much would have happened anyway?

Paid Search is auction-based. During Black Friday, millions of consumers are actively searching for deals regardless of what any advertiser does. That surge in search volume would have driven more impressions, more clicks, and more conversions even on a completely unchanged campaign. The BF-specific decisions — higher bids, bigger budgets, seasonal creatives — add incremental lift on top of that organic demand wave. The measurement question is specifically about that increment: what did the active campaign decisions contribute above what baseline spend would have earned from the demand wave alone?

The organic demand wave is easy to see in the data. Organic Search spiked 73%. Direct traffic spiked 54%. Referral spiked 35%. Social spiked 59%. None of these channels ran BF campaigns. All of them benefited from the same consumer behavior. If you measure Paid Search lift against a pre-BF baseline, you are attributing that entire wave to your campaign decisions.

This is the campaign measurement problem. Black Friday makes it easy to see. The same problem exists for Valentine's Day, back-to-school, a product launch, a pricing change — any event where external demand moves alongside the campaign.

This case study works through four levels of measurement rigor applied to the same problem. Each level is better than the last. Each one also fails in a specific, predictable way — until the final one constructs the right counterfactual.

---

## Before We Start: If You Can Randomize, Do It

A geo holdout or user-level split creates the counterfactual by design. Half the markets see the campaign; half do not. The difference is the causal effect — no modeling, no assumptions, no donor channels required.

Every method in this case study exists for situations where randomization was not possible: the campaign already launched, operational constraints prevent a holdout, or the unit of intervention cannot be split. If you can run a holdout, that is always the answer.

---

## The Setup

This case study uses synthetic data with a known ground truth — two years of daily revenue across six channels, with a trend shift beginning July 1, 2025. Revenue is flat through mid-year, then grows at +0.4% per day. By November, the Paid Search baseline is 61% above what it was a year earlier.

This growth acceleration is not incidental. It is the stress test. Any company with double-digit year-over-year growth will face some version of this when measuring seasonal campaigns — and it is precisely what breaks the simpler methods.

Because the data is synthetic, we know the true answer: the paid campaigns contributed **1,340 USD/day** above what organic demand alone would have produced. That is 71.6% of the November baseline. Every method below is judged against this number.

---

## Level 1: Before/After

The first instinct is to compare the BF window to what came before. BF mean was 4,241 USD/day. The November 1-26 baseline was 1,871 USD/day. Lift: 2,370 USD/day.

If you use the full two-year pre-period instead (where the average is pulled down by the flat 2024 period), the number climbs to 2,998 USD/day.

Neither number is the campaign's contribution. Both include the organic BF demand wave. Both include the trend growth that was already happening before BF. The estimate shifts by nearly 30% just from choosing a different baseline window — not because the campaigns performed differently, but because the framing changed.

Before/after asks: *did revenue go up?* It cannot ask: *would it have gone up anyway?*

**Result: 2,370–2,998 USD/day reported vs 1,340 USD/day true — 1.8x to 2.2x overstatement.**

---

## Level 1.5: Year-over-Year

Marketing teams often sidestep the baseline problem for seasonal events by comparing to the same event in the prior year. BF 2025 vs BF 2024. The intuition is sound: same event, same calendar window, same consumer behavior patterns. Seasonality is controlled for.

On this dataset, that comparison produces a lift of 2,187 USD/day — better than before/after, but still a 1.6x overstatement.

The reason is straightforward. The November pre-BF baseline grew 61% year-over-year — not from campaigns, but from the underlying trend shift. That baseline growth is embedded in the BF-to-BF delta and cannot be separated from campaign contribution. You are not measuring what the campaigns added; you are measuring what the campaigns added *plus* the year-over-year growth that would have happened with or without the campaigns.

YoY asks: *did revenue go up more than last year?* That is a better question than before/after. But it is still not the incrementality question.

There is also a more fundamental problem: no two years are perfectly comparable. BF 2024 and BF 2025 differ not just in baseline revenue but in everything that happened between them — competitor activity, macro conditions, consumer sentiment, product catalog changes, campaign budget and targeting decisions. YoY controls for calendar position but absorbs all of these factors silently into the delta. The number does not tell you how much of the difference is campaign contribution and how much is everything else that changed.

**When YoY works:** When year-over-year growth is flat, competitive dynamics are stable, and nothing structural changed between the two periods. In practice that is a narrow set of conditions, and the overstatement is not auditable from the number itself — you cannot tell from a YoY delta alone how wrong it is.

**Result: 2,187 USD/day vs 1,340 USD/day true — 1.6x overstatement.**

---

## Level 2: Time Series Models

Before/after and YoY fail because they use naive baselines. The natural next step is to model what revenue would have looked like without the campaign — building a counterfactual from the pre-period dynamics.

BSTS (Bayesian Structural Time Series, implemented in Google's CausalImpact) does exactly this. It learns trend direction, weekly patterns, and annual seasonality from the pre-period, then projects forward. Prophet (Meta/Facebook) takes the same approach with a different model structure — decomposing trend, seasonality, and holidays via Fourier terms. Both are trained on the full pre-period, which includes BF 2024.

The pre-BF period is training data — fitted values tracking the actuals is expected, not a signal of model quality. The real test is the BF window, which is out-of-sample. That is where the model has to forecast without having seen the data, and that is where it fails.
During BF, the counterfactual sits at roughly 1,800 USD/day while actual revenue spikes to 4,241 USD/day. The model attributes almost the entire spike to the campaign — including the organic BF demand wave that lifted every channel.

Why does the counterfactual under-estimate the spike? The BSTS seasonal component partially learned from BF 2024 — it knows late November is elevated. But the weekly seasonal bin averages the BF days with surrounding days, so the model learns a moderate seasonal lift rather than a sharp one. This is compounded by the fact that BF 2025 occurred at a 61% higher baseline than BF 2024 — even a correctly-learned prior year spike would under-forecast the current year level.

The result is something close to a trend-adjusted YoY — total BF performance vs a modeled baseline that accounts for growth. Better than raw YoY, but still not incrementality. Even if BSTS estimated the spike correctly, the organic demand wave would remain inside the gap, attributed to the campaign. Without donor channels that observed the organic demand directly, the model has no way to separate it from the campaign contribution.

BSTS asks: *did revenue go up more than the model expected?* Still not the incrementality question.

**Result: approximately 2,400 USD/day vs 1,340 USD/day true — 79% overstatement.**

---

## Level 3: BSTS + Synthetic Control

The insight that makes SC work is simple: if you want to know what Paid Search would have done on organic demand alone, look at what the organic demand channels actually did.

During BF 2025, Organic Search, Direct, Referral, and Social all spiked — not because of paid campaigns, but because consumers were in BF mode. Those channels are what Paid Search would have looked like if it were driven purely by organic demand. Their behavior at the BF moment is the counterfactual.

SC constructs this formally. Organic demand channels are passed as covariates into the CausalImpact model. The model learns, from the pre-period, what combination of donor channel weights best explains Paid Search dynamics. That weighted combination becomes the counterfactual — not a projection from historical seasonal patterns, but a real-time reading of organic demand through the donor channels.

This solves both problems simultaneously. The trend shift is absorbed automatically: all donor channels shared the same growth acceleration, so their co-movement with Paid Search in the pre-period already embeds the trend. No extrapolation required. The BF spike is captured correctly: during the BF window, donor channels are actually spiking at the 2025 level, so those elevated covariate values directly anchor the counterfactual at the right level.

The gap between actual Paid Search and the SC counterfactual is the paid-specific contribution. Not total BF impact. Not revenue vs a seasonal baseline. Specifically: how much more did Paid Search generate than it would have earned on baseline spend riding the organic demand wave?

On this dataset, both the 23-month and the 3-month pre-period versions produce estimates near the true 1,340 USD/day. The 3-month version is particularly notable — it uses only August through November 2025, with no prior year data at all, and still recovers the true paid increment. The key requirement is not a long history. It is strong co-movement between the treated channel and the donor channels during the pre-period.

BSTS+SC asks: *did Paid Search go up more than organic demand alone would explain?* That is the incrementality question.

**Result: approximately 1,340 USD/day — near true value for both pre-period lengths.**

---

## What the Progression Shows

| Method | Question answered | Error |
|---|---|---|
| Before/After | Did revenue go up? | +2.2x |
| YoY | Did revenue go up more than last year? | +1.6x |
| BSTS | Did revenue go up more than the model expected? | +79% |
| BSTS+SC | Did PS go up more than organic demand explains? | Near zero |

The progression is not about sophistication. It is about precision. Each method answers a more specific question than the one before it. Only the last one asks the right question — and produces a number that can actually support a budget decision.

A team using before/after will report 2.2x the true campaign contribution. That number will be used to justify next year's budget. Channels that cannot be measured this way will be defunded in its favor. The error does not stay in the analysis — it propagates into allocation decisions.

This is not a Black Friday problem. Black Friday just makes it visible.

---


## A Note on Synthetic Data

This case study uses synthetic data. The advantage is precision: we know the true answer, which makes it possible to measure exactly how wrong each method is — something impossible with real campaigns.

Real data introduces additional complications this simulation does not fully capture. Donor channels may not be as cleanly exogenous — a large paid search campaign can drive branded search volume, inflating Organic Search and contaminating the SC counterfactual. The trend shift here is clean and smooth; real growth often comes in steps, from product launches or market expansions, which can be harder for SC weights to absorb. BF campaign changes — bid adjustments, budget lifts, creative swaps — happen at different times and scales across campaigns, creating a messier intervention boundary than the clean Nov 27 start date here. And real datasets often have data quality issues: missing days, platform reporting delays, attribution window mismatches.

The methods are the same. The judgment calls in applying them to real data are harder.

## Technical Notes

**Dataset:** Synthetic, seed=42, Jan 2024–Dec 2025. Two years of daily revenue across six channels with trend shift from Jul 1, 2025.

**BSTS implementation:** Google's CausalImpact R package. State space: local level + weekly seasonal (nseasons=7) + annual seasonal (nseasons=52, season.duration=7). Full pre-period Jan 2024–Nov 26, 2025 includes BF 2024.

**SC implementation:** Organic demand channels passed as covariates to CausalImpact via `causal_impact_with_covariates()` wrapper (see `src/causal_impact_wrapper.R`). Spike-and-slab priors for donor selection. Pre-period MAPE used as model quality gate. Two pre-period lengths tested: 23 months (Jan 2024–Nov 2025) and 3 months (Aug–Nov 2025).

**Donor selection:** Email excluded — runs its own BF promotional campaigns and is not an organic demand proxy. Organic Search, Direct, Referral, Social included.

**Limitations:** Four donor channels is a thin pool; production analyses typically use 10-30+. Donor organic lift creates slight underestimation of the paid increment. Assumes donor channels are exogenous to the paid campaigns being measured.

---

## Reproducibility

```bash
pip install -r requirements.txt
jupyter lab
```

R required for notebooks 02–03: https://cran.r-project.org/bin/macosx/  
R packages install automatically on first run.  
Run in order: `00` → `01` → `02` → `03` → `04`
