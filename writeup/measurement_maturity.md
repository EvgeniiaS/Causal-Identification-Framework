# Did That Actually Work?
## A Case Study in Campaign Measurement

*This case study accompanies Pillar II of the Decision Intelligence framework: Causal Inference — answers when there is no control group.*

---

Black Friday arrived. The Paid Search team did what teams do: raised bids, expanded budgets, launched BF-specific creatives. Revenue spiked — up 127% over the November baseline. The team reported the number. Leadership was pleased. Budget was renewed.

But here is the question nobody asked: how much of that spike came from the campaign decisions, and how much would have happened anyway?

Paid Search is auction-based. During Black Friday, millions of consumers are actively searching for deals regardless of what any advertiser does. That surge in search volume drives more impressions, more clicks, and more conversions even on a completely unchanged campaign. The BF-specific decisions — higher bids, bigger budgets, seasonal creatives — add incremental lift on top of that organic demand wave. The measurement question is specifically about that increment: what did the active campaign decisions contribute above what baseline spend would have earned from the demand wave alone?

The organic demand wave is easy to see in the data. Organic Search spiked 73%. Direct traffic spiked 54%. Referral spiked 35%. Social spiked 59%. None of these channels ran BF campaigns. All of them benefited from the same consumer behavior. If you measure Paid Search lift against a pre-BF baseline, you are attributing that entire wave to your campaign decisions.

This is the campaign measurement problem. Black Friday makes it easy to see. The same problem exists for Valentine's Day, back-to-school, a product launch, a pricing change — any event where external demand moves alongside the campaign.

This case study works through four levels of measurement rigor applied to the same problem. Each level is better than the last. Each one also fails in a specific, predictable way — until the final one constructs the right counterfactual. Each level also answers a different question:

- **Before/After:** *Did revenue go up?*
- **YoY:** *Did revenue go up more than last year?*
- **BSTS:** *Did revenue go up more than the model expected?*
- **BSTS+SC:** *Did Paid Search go up more than organic demand alone would explain?*

Each is a legitimate question. Only the last one most closely approximates an incrementality question.

---

## Before We Start: If You Can Randomize, Do It

A geo holdout or user-level split creates the counterfactual by design. Half the markets see the campaign; half do not. The difference is the causal effect — no donor assumptions, no trend assumptions required.

This is generally the most reliable approach, but it is not without its own requirements. Randomized designs assume no interference between treatment and control units (SUTVA), valid randomization, and compliance. In practice, holdouts require advance planning, operational feasibility, and willingness to accept reduced reach in control markets during the measurement period.

Every observational method in this case study exists for when randomization was not possible: the campaign already launched, operational constraints prevent a holdout, or the unit of intervention cannot be split. If you can run a holdout, that is the approach to reach for first.

---

## The Setup

This case study uses synthetic data — two years of daily revenue across six channels, with a trend shift beginning July 1, 2025. Revenue is flat through mid-year, then grows at +0.4% per day. By November, the Paid Search baseline is 61% above what it was a year earlier.

This growth acceleration is the stress test. Any company with double-digit year-over-year growth will face some version of this when measuring seasonal campaigns — and it is precisely what breaks the simpler methods.

**On the ground truth definition.** Because the data is synthetic, the true paid increment can be computed directly: PS observed lift (126.7%) minus the average lift across organic donor channels (55.0%) equals 71.6% of the November baseline — **1,340 USD/day**. Every method is judged against this number.

One important caveat: this definition of ground truth is structurally aligned with the donor-based counterfactual framework. It defines the true increment as the gap between PS and its organic demand channels — which is exactly what SC estimates. This favors SC relative to purely time-series approaches. A fully independent ground truth would require a randomized holdout that kept paid campaigns off in a subset of markets. In the absence of that, this is the most defensible definition available in a synthetic context, but the circularity should be acknowledged rather than ignored.

Performance on synthetic data is also optimistic. Clean co-movement, a smooth trend shift, and a well-defined intervention boundary all favor the methods. Real campaigns are messier in ways that matter — discussed at the end.

---

## Level 1: Before/After

The first instinct is to compare the BF window to what came before. BF mean was 4,241 USD/day. The November 1-26 baseline was 1,871 USD/day. Lift: 2,370 USD/day.

If you use the full two-year pre-period instead — where the average is pulled down by the flat 2024 period — the number climbs to 2,998 USD/day.

Neither number is the campaign's contribution. Both include the organic BF demand wave. Both include the trend growth that was already happening before BF. The estimate shifts by nearly 30% just from choosing a different baseline window — not because the campaigns performed differently, but because the framing changed.

Before/after asks: *did revenue go up?* It cannot ask: *would it have gone up anyway?*

**Result: 2,370–2,998 USD/day reported vs 1,340 USD/day true — 1.8x to 2.2x overstatement.**

---

## Level 1.5: Year-over-Year

Marketing teams often sidestep the baseline problem for seasonal events by comparing to the same event in the prior year. BF 2025 vs BF 2024. The intuition is sound: same event, same calendar window, same consumer behavior patterns. Seasonality is controlled for.

On this dataset, that comparison produces a lift of 2,187 USD/day — better than before/after, but still a 1.6x overstatement.

The reason is straightforward. The November pre-BF baseline grew 61% year-over-year — not from campaigns, but from the underlying trend shift. That baseline growth is embedded in the BF-to-BF delta and cannot be separated from campaign contribution. You are not measuring what the campaigns added; you are measuring what the campaigns added *plus* the year-over-year growth that would have happened with or without them.

There is also a more fundamental problem: no two years are perfectly comparable. BF 2024 and BF 2025 differ not just in baseline revenue but in everything that happened between them — competitor activity, macro conditions, consumer sentiment, product catalog changes, campaign budget and targeting decisions. YoY controls for calendar position but absorbs all of these factors silently into the delta. The number does not tell you how much of the difference is campaign contribution and how much is everything else that changed.

YoY asks: *did revenue go up more than last year?* That is a better question than before/after. But it is still not the incrementality question.

**When YoY is defensible:** When year-over-year growth is flat, competitive dynamics are stable, and nothing structural changed between the two periods. In practice that is a narrow set of conditions, and the overstatement is not auditable from the number itself — you cannot tell from a YoY delta alone how wrong it is.

**Result: 2,187 USD/day vs 1,340 USD/day true — 1.6x overstatement.**

---

## Level 2: Time Series Models

Before/after and YoY fail because they use naive baselines. The natural next step is to model what revenue would have looked like without the campaign — building a counterfactual from the pre-period dynamics.

BSTS (Bayesian Structural Time Series, implemented in Google's CausalImpact) does exactly this. It learns trend direction, weekly patterns, and annual seasonality from the pre-period, then projects forward. Prophet (Meta/Facebook) takes the same approach with a different model structure — decomposing trend, seasonality, and holidays via Fourier terms. Both are trained on the full pre-period, which includes BF 2024.

The pre-BF period is training data — fitted values tracking the actuals is expected, not a signal of model quality. The real test is the BF window, which is out-of-sample. That is where the model has to forecast without having seen the data, and that is where it fails.

During BF, the counterfactual approximates the trend-shifted pre-BF level at ~1,800 USD/day — the growth acceleration is captured. But the counterfactual stays near that level rather than anticipating any BF elevation. Actual revenue spikes to 4,241 USD/day. The gap from 1,800 to 4,241 contains two things the model cannot separate: the organic BF demand spike and the paid campaign contribution. The model attributes the entire gap to the campaign.

Why does the counterfactual not anticipate the spike? The BSTS seasonal component partially learned from BF 2024 — it knows late November is elevated — but the weekly seasonal bin averages BF days with surrounding days, producing a moderate seasonal lift rather than a sharp one. Had the model correctly forecast a BF spike based on 2024 data, that predicted spike would itself contain 2024 organic demand and 2024 paid campaign contribution — so the remaining gap would reflect only the year-over-year change in each, not a clean read on either. The inability to replicate the spike causes the full 2025 organic BF demand to land in the gap alongside the true paid increment.

The result is something close to a trend-adjusted YoY — total BF performance above the pre-BF modeled level, with organic demand and campaign contribution conflated throughout.

**Why not Difference-in-Differences?** DiD is the natural alternative when geographic or unit-level variation exists. It requires a parallel trends assumption — treated and control units would have followed the same trajectory absent the intervention. In a single-channel measurement problem with no untreated geographic analog, there is no natural control unit for DiD. SC is appropriate precisely because it constructs the missing comparison rather than requiring one to already exist.

BSTS asks: *did revenue go up more than the model expected?* Still not the incrementality question.

**Result: approximately 2,400 USD/day vs 1,340 USD/day true — 79% overstatement.**

---

## Level 3: BSTS + Synthetic Control

The insight that makes SC work here is direct: if you want to know what Paid Search would have done on organic demand alone, look at what the organic demand channels actually did.

During BF 2025, Organic Search, Direct, Referral, and Social all spiked — not because of paid campaigns, but because consumers were in BF mode. Those channels anchor the counterfactual — they are a real-time proxy for the organic demand that also flowed through Paid Search, observed at the moment it is needed rather than estimated from historical seasonal patterns.

**Method clarification.** What is implemented here is not classical Abadie-style Synthetic Control, which constructs a convex combination of donor units with non-negative weights summing to one. This is a regression-based SC — organic demand channels are passed as covariates into the CausalImpact BSTS model, with spike-and-slab priors performing Bayesian variable selection over the donor set. It is more accurately described as BSTS with contemporaneous controls than as pure SC. This approach is more flexible but also more dependent on BSTS model assumptions, and a technical reviewer should understand the distinction.

**Why not simply run a regression with controls?** A standard regression with organic channels as controls would estimate the partial effect of Paid Search conditional on organic demand. The BSTS+SC approach adds: structured time-series decomposition handling trend and weekly seasonality, Bayesian variable selection across the donor set rather than manual inclusion, and a full posterior distribution that propagates uncertainty into the causal estimate rather than producing point estimates with frequentist standard errors.

The model learns from the pre-period what weighted combination of donor channels best explains Paid Search dynamics. That weighted combination becomes the counterfactual. The gap between actual Paid Search and the SC counterfactual is the paid-specific contribution — how much more Paid Search generated than it would have earned without BF-specific campaign decisions, with the organic demand wave held as the baseline.

This largely addresses both Level 2 failures. The trend shift is absorbed through the donor weights: all channels shared the same growth acceleration, so their co-movement with Paid Search in the pre-period already embeds the trend. The BF spike is largely captured because donor channels actually spiked at the 2025 level during the BF window — those elevated covariate values anchor the counterfactual at the actual current-year organic demand level rather than relying on smoothed seasonal history.

**Email is excluded from the donor pool.** Email ran its own BF promotional campaigns — its behavior during BF reflects campaign decisions, not organic demand. Including it would contaminate the counterfactual.

**Result: approximately 1,340 USD/day — near true value for both pre-period lengths tested.**

---

## Assumptions

SC validity rests on several assumptions that should be stated explicitly rather than left implicit:

**1. Donor exogeneity.** Donor channels must not be affected by the treatment. In this context, Paid Search campaign decisions must not influence what Organic Search, Direct, Referral, and Social do. This assumption is partially fragile in marketing data: a large paid search campaign can drive branded search volume, inflating Organic Search; paid display or social retargeting can inflate Direct and Social. Violation biases the estimate toward zero — the method will understate the true paid increment. Channels with high correlation to the campaign's own activity are poor donors regardless of their historical co-movement with Paid Search.

**2. No interference (SUTVA).** The method assumes no spillover between the treated channel and donor channels beyond what is captured in the pre-period relationship. Paid Search affecting Organic the next day is the clearest violation in this context.

**3. Contemporaneous relationships.** The model uses donor channel values at the same time point to construct the counterfactual. If meaningful lags exist — paid search driving organic search the following day, or social influencing direct with a delay — a model using only contemporaneous covariates is misspecified. In practice, lagged covariates should be tested.

**4. Stable relationships.** The weights learned in the pre-period are assumed to hold during the post-period. Nonlinear saturation effects — common during high-demand periods like BF — may alter the relationship between channels in ways the pre-period weights do not capture. Large spend changes relative to the pre-period baseline are a particular risk.

**5. Sufficient pre-period fit.** The weighted donor combination must track Paid Search well during the pre-period before the estimate can be trusted. Poor pre-period fit means the counterfactual is misspecified before it even reaches the intervention window.

**6. Donor independence.** Organic Search, Direct, Referral, and Social are often correlated. Highly correlated donor channels create unstable weight attribution — the model may assign arbitrary weight splits across redundant donors, masking poor identification with good aggregate fit. Regularization via spike-and-slab priors mitigates but does not eliminate this risk.

---

## Validation

A SC estimate is only as credible as the pre-period fit, and pre-period fit alone is not sufficient. Three checks are essential before trusting the estimate:

**Pre-period fit diagnostics.** The weighted donor combination should closely track Paid Search during the pre-period. Pre-period MAPE below 10-15% is a useful heuristic, but MAPE alone is not sufficient — it should be complemented with residual bias checks (systematic over- or under-prediction in specific periods) and autocorrelation diagnostics (residuals should not be serially correlated, which would indicate a structural pattern the model missed).

**Placebo test.** Apply the same method to a pseudo-intervention at a point in the pre-period where no intervention occurred. A large placebo effect indicates the model is detecting noise rather than signal. This is the single most important validity check for SC.

**Sensitivity to donor set.** Re-run with each donor excluded in turn. If the estimate changes dramatically when a single donor is dropped, the weights are unstable and the estimate is unreliable. A robust estimate should be stable across reasonable variations in the donor pool.

On this synthetic dataset all three checks pass. On real data, none of them are guaranteed, and a failed check should stop the analysis rather than be noted and proceeded past.

---

## Failure Modes

SC fails predictably in specific situations:

- **Donor contamination.** Treated channel activity influences donor channels, violating exogeneity. Estimate biases toward zero.
- **Weak pre-period correlation.** Donors do not co-move with the treated channel. Weights are unstable, counterfactual is unreliable.
- **Structural breaks.** A change between pre and post period alters the channel relationships. Weights learned in the pre-period no longer apply.
- **Lag mismatch.** Meaningful lags between channels are ignored by a contemporaneous-only model. Counterfactual is misspecified.
- **Donor multicollinearity.** Highly correlated donors produce unstable weight attribution that looks like good fit but is not well-identified.
- **Intervention boundary.** Phased campaign changes create a messy treatment onset that a single start-date model cannot handle cleanly.

---

## Uncertainty

The SC estimate is reported as a point estimate for clarity of comparison against the ground truth. In a real analysis, the BSTS posterior produces credible intervals around the causal estimate. These intervals reflect uncertainty from model fit, donor weight instability, and noise in the post-period.

A point estimate alone is not an actionable causal estimate. The width of the credible interval relative to the decision threshold determines whether the estimate is usable. An estimate of 1,340 USD/day with a 95% interval of ±100 supports a budget decision. The same point estimate with an interval of ±900 tells you the direction but not the magnitude with any confidence — it is informative but not decision-grade. Actionability depends on interval width relative to the expected ROI threshold for the decision being made.

---

## What the Progression Shows

| Method | Question answered | Overstatement |
|---|---|---|
| Before/After | Did revenue go up? | +120 to +124% |
| YoY | Did revenue go up more than last year? | +63% |
| BSTS | Did revenue go up more than the model expected? | +79% |
| BSTS+SC | Did PS go up more than organic demand explains? | ~0% |

The progression is not about sophistication. It is about asking a more precise question at each step. Each method answers a different question — and only the last one most closely approximates the incrementality question, while resting on assumptions that must be explicitly validated.

A team reporting the before/after lift as campaign ROI is not being careless. They are answering the question their tools let them ask. The problem is that the question their tools let them ask is not the question budget decisions require. The error does not stay in the analysis — it propagates into allocation decisions, over-crediting channels that generate large before/after numbers while defunding channels whose contribution is harder to isolate.

This is not a Black Friday problem. Black Friday just makes it visible.

---

## What to Do With the Estimate

A validated SC estimate with appropriately tight credible intervals is actionable for:
- Determining whether BF campaign investment generated positive incremental return above its cost
- Comparing campaign effectiveness across years using a consistent, bias-reduced methodology
- Informing bid and budget decisions for the next campaign cycle

It is not sufficient on its own for:
- Precise budget optimization across channels — that requires MMM, which handles long-run dynamics, diminishing returns, and cross-channel saturation effects that SC does not model
- Attribution across multiple simultaneous campaigns — SC measures one well-defined intervention at a time against a specific counterfactual
- Decisions where the credible interval is wide relative to the ROI threshold

The three methods are complementary, not alternatives:
- **SC** — short-term causal read on a specific intervention
- **MMM** — long-run channel allocation accounting for saturation and carry-over
- **Experiments** — ground truth validation that calibrates both

The most defensible measurement programs use all three in combination, with experiments providing the ground truth that keeps SC and MMM honest.

---

## A Note on Synthetic Data

Performance here is optimistic relative to what real campaigns would produce. The co-movement between donor channels and Paid Search is clean by construction, the trend shift is smooth, the intervention has a well-defined start date, and there is no noise from simultaneous campaigns or data quality issues.

Real data introduces complications that matter in practice:

**Donor contamination.** A large paid search campaign inflating branded search volume violates exogeneity and biases the estimate downward. This requires explicit testing, not domain intuition.

**Messy interventions.** Bid adjustments, budget lifts, and creative swaps happen at different times across ad groups and often ramp gradually. A clean intervention date does not exist in most real campaigns.

**Step-function growth.** Real growth often comes from discrete events — a product launch, a new market, a competitive exit — which can be harder for SC weights to absorb than the smooth acceleration modeled here.

**Lag structure.** Paid Search may influence Organic Search and Direct the following day through branded search effects. A contemporaneous-only model will be misspecified if these lags are meaningful.

**Data quality.** Missing days, platform reporting delays, attribution window mismatches, and channel definition inconsistencies all introduce noise that is absent here.

**Multicollinearity.** Real donor channels are often more correlated than what is modeled here, creating greater weight instability than the synthetic data reflects.

The methods are the same. The judgment calls in applying them to real data are harder, and the results will not be as clean.

---

## Technical Notes

**Dataset:** Synthetic, seed=42, Jan 2024–Dec 2025. Six channels, daily revenue, trend shift from Jul 1, 2025.

**BSTS:** Google's CausalImpact R package. State space: local level + weekly seasonal (nseasons=7) + annual seasonal (nseasons=52, season.duration=7). Pre-period Jan 2024–Nov 26, 2025 includes BF 2024.

**Regression-based SC:** Organic demand channels passed as covariates to CausalImpact via `causal_impact_with_covariates()` (see `src/causal_impact_wrapper.R`). Spike-and-slab priors for Bayesian variable selection over donor set. Pre-period MAPE used as primary model quality gate, supplemented with residual diagnostics. Two pre-period lengths tested: 23 months (Jan 2024–Nov 2025) and 3 months (Aug–Nov 2025).

**Donor channels:** Organic Search, Direct, Referral, Social. Email excluded — runs its own BF campaigns, not an organic demand proxy.

**Limitations:** Four donor channels is a thin pool; production analyses typically use 10-30+ units for stable weight identification. Donor organic BF lift creates slight downward bias in the paid increment estimate. Ground truth definition is structurally aligned with SC logic — an independent holdout would provide a more neutral benchmark. Point estimates reported here; posterior credible intervals should accompany any real analysis.

---

## Reproducibility

```bash
pip install -r requirements.txt
jupyter lab
```

R required for notebooks 02–03: https://cran.r-project.org/bin/macosx/  
R packages install automatically on first run.  
Run in order: `00` → `01` → `02` → `03` → `04`
