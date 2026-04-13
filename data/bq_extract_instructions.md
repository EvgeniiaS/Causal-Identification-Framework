# Data Extraction: GA360 BigQuery Sample

The Google Analytics 360 sample dataset is publicly available via BigQuery's free sandbox tier.
No billing required for queries under 1TB/month.

## Access

1. Go to [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Sign in with any Google account
3. The dataset is at: `bigquery-public-data.google_analytics_sample`

## Query

Run the following query to extract daily revenue for 2017. Save the result as `data/ga_daily_revenue_2017.csv`.

```sql
SELECT
  PARSE_DATE('%Y%m%d', date) AS date,
  SUM(totals.transactionRevenue) / 1e6 AS revenue_usd,
  SUM(totals.transactions) AS transactions,
  COUNT(*) AS sessions,
  SUM(totals.pageviews) AS pageviews,
  channelGrouping AS channel,
  device.deviceCategory AS device_type
FROM
  `bigquery-public-data.google_analytics_sample.ga_sessions_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20170101' AND '20171231'
  AND totals.transactionRevenue IS NOT NULL
GROUP BY
  date, channel, device_type
ORDER BY
  date, channel, device_type
```

> **Note:** `transactionRevenue` is stored in micros (millionths of a dollar) in this dataset.
> Dividing by 1e6 converts to USD.

## Expected Output

- ~3,600 rows (365 days × ~10 channel/device combinations)
- Columns: `date`, `revenue_usd`, `transactions`, `sessions`, `pageviews`, `channel`, `device_type`
- Date range: 2017-01-01 to 2017-12-31

## Aggregated Version (for BSTS / CausalImpact)

For the time series models, you'll also want a daily aggregate (no channel/device splits):

```sql
SELECT
  PARSE_DATE('%Y%m%d', date) AS date,
  SUM(totals.transactionRevenue) / 1e6 AS revenue_usd,
  SUM(totals.transactions) AS transactions,
  COUNT(*) AS sessions,
  SUM(totals.pageviews) AS pageviews
FROM
  `bigquery-public-data.google_analytics_sample.ga_sessions_*`
WHERE
  _TABLE_SUFFIX BETWEEN '20170101' AND '20171231'
GROUP BY
  date
ORDER BY
  date
```

Save this as `data/ga_daily_revenue_2017_agg.csv`.

## File Naming Convention

```
data/
├── ga_daily_revenue_2017.csv        ← channel/device splits (for Synthetic Control donors)
├── ga_daily_revenue_2017_agg.csv    ← daily aggregate (for Naive B/A and CausalImpact)
└── bq_extract_instructions.md       ← this file
```

## Note on Data Sharing

The GA360 sample data is publicly licensed for analysis and educational use.
However, to keep this repo lightweight and ensure you're always working with
the authoritative source, raw data files are not committed to the repo.
Extract fresh from BigQuery using the queries above.
