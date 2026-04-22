#' @title causal_impact_with_covariates
#'
#' @description
#' Wrapper around Google's CausalImpact package combining BSTS with
#' Synthetic Control-style covariate donors. Covariates serve as the donor pool —
#' BSTS uses Bayesian variable selection (spike-and-slab priors) to determine
#' which donors best explain the treated series, then uses the learned relationship
#' to construct the post-period counterfactual.
#'
#' Key additions over the base CausalImpact package:
#' - Pre-period MAPE/WMAPE for model selection across iterations
#' - Vacation period exclusion (anomalous periods removed from training)
#' - Reversion period monitoring (does effect persist or revert?)
#' - Three trend model options: local_level, local_linear_trend, semilocal_linear_trend
#' - Iterative model tracking via fit_metrics.csv
#'
#' @param indata         data.frame. Wide format: one row per date, one column per series.
#'                       Column names must be R-safe (no spaces — use underscores).
#' @param pre_period     Date vector length 2: c(start, end) of training period.
#' @param post_period    Date vector length 2: c(start, end) of intervention period.
#' @param vacation_period List of Date vectors. Periods excluded from training.
#'                       Example: list(as.Date(c("2024-12-23","2024-12-26")))
#' @param reversion_period Date vector length 2. Post-intervention monitoring window.
#'                       For temporary interventions: response and prediction should
#'                       converge here as the effect fades. Default NULL.
#' @param time_var       Character. Name of the date column in indata.
#' @param time_var_format Character. strptime format string, e.g. "%Y-%m-%d".
#' @param treated        Character. Name of the treated series column (no spaces).
#' @param covariates     Character vector. Donor column names (no spaces).
#' @param niter          Integer. MCMC iterations. Default 1000.
#' @param standardize_data Logical. Default TRUE.
#' @param prior_level_sd Numeric. Prior SD for local level. Default 0.01.
#' @param nseasons       Integer. Seasonal period (7 for weekly). Default 1.
#' @param season_duration Integer. Data points per season. Default 1.
#' @param dynamic_regression Logical. Time-varying coefficients. Default FALSE.
#' @param trend_model    Character. "local_level" | "local_linear_trend" |
#'                       "semilocal_linear_trend". Default "local_level".
#' @param ver            Character. Version label for this iteration.
#' @param note           Character. Free-text note. Default NULL.
#' @param outpath        Character. Directory for outputs (created if missing).
#'
#' @return Invisibly: list(impact, fit_metrics, mape_pre, wmape_pre)
#'
#' @examples
#' result <- causal_impact_with_covariates(
#'   indata          = panel,          # wide data.frame, R-safe column names
#'   pre_period      = as.Date(c("2025-05-01", "2025-11-26")),
#'   post_period     = as.Date(c("2025-11-27", "2025-12-31")),
#'   reversion_period= as.Date(c("2025-12-03", "2025-12-31")),
#'   time_var        = "date",
#'   time_var_format = "%Y-%m-%d",
#'   treated         = "Paid_Search",
#'   covariates      = c("Organic_Search", "Direct", "Referral", "Social"),
#'   niter           = 1000,
#'   nseasons        = 7,
#'   trend_model     = "local_level",
#'   ver             = "v01",
#'   note            = "7-month pre-period, organic demand donors",
#'   outpath         = "./output/"
#' )
#' dev.off()

causal_impact_with_covariates <- function(
    indata,
    pre_period,
    post_period,
    vacation_period    = NULL,
    reversion_period   = NULL,
    time_var,
    time_var_format,
    treated,
    covariates,
    niter              = 1000,
    standardize_data   = TRUE,
    prior_level_sd     = 0.01,
    nseasons           = 1,
    season_duration    = 1,
    dynamic_regression = FALSE,
    trend_model        = "local_level",
    ver,
    note               = NULL,
    outpath
) {

    # ── Dependencies ──────────────────────────────────────────────────────────
    for (pkg in c("data.table", "CausalImpact", "zoo", "scales")) {
        if (!requireNamespace(pkg, quietly = TRUE)) {
            install.packages(pkg, repos = "https://cran.r-project.org")
        }
        suppressPackageStartupMessages(library(pkg, character.only = TRUE))
    }

    # ── Validate ──────────────────────────────────────────────────────────────
    stopifnot(
        is.data.frame(indata) || is.data.table(indata),
        length(pre_period)  == 2,
        length(post_period) == 2,
        is.character(treated),
        is.character(covariates), length(covariates) >= 1,
        trend_model %in% c("local_level", "local_linear_trend", "semilocal_linear_trend")
    )
    if (!treated %in% names(indata))
        stop(paste("treated not found in indata:", treated))
    missing_cols <- setdiff(covariates, names(indata))
    if (length(missing_cols) > 0)
        stop(paste("Covariates not found:", paste(missing_cols, collapse = ", ")))

    # ── Prepare ───────────────────────────────────────────────────────────────
    dt <- as.data.table(indata)

    # Impute NA -> 0
    na_counts <- sapply(dt[, c(treated, covariates), with = FALSE], function(x) sum(is.na(x)))
    if (any(na_counts > 0)) {
        message("NAs imputed with 0: ", paste(names(na_counts[na_counts > 0]), collapse = ", "))
        for (col in names(na_counts[na_counts > 0])) {
            dt[is.na(get(col)), (col) := 0]
        }
    }

    # Vacation period: mask treated series so model skips anomalous windows
    if (!is.null(vacation_period)) {
        if (!is.list(vacation_period)) vacation_period <- list(vacation_period)
        for (i in seq_along(vacation_period)) {
            vp        <- as.Date(vacation_period[[i]])
            vp_dates  <- as.Date(as.character(dt[[time_var]]), time_var_format)
            dt[vp_dates >= vp[1] & vp_dates <= vp[2], (treated) := NA]
            message(sprintf("Vacation %d excluded: %s to %s", i, vp[1], vp[2]))
        }
    }

    # Build zoo time series
    time_points <- as.Date(as.character(dt[[time_var]]), time_var_format)
    train       <- zoo(dt[, c(treated, covariates), with = FALSE], time_points)

    # ── Fit model ─────────────────────────────────────────────────────────────
    if (trend_model %in% c("local_linear_trend", "semilocal_linear_trend")) {

        kExpectedModelSize <- 3
        kExpectedR2        <- 0.8
        kPriorDf           <- 50

        post_response <- window(train[, treated], start = post_period[1], end = post_period[2])
        window(train[, treated], start = post_period[1], end = post_period[2]) <- NA

        ss <- list()
        if (trend_model == "local_linear_trend") {
            ss <- AddLocalLinearTrend(ss, train[, treated])
        } else {
            ss <- AddSemilocalLinearTrend(ss, train[, treated])
        }
        if (nseasons > 1) {
            ss <- AddSeasonal(ss, train[, treated],
                              nseasons = nseasons, season.duration = season_duration)
        }

        bsts.model <- bsts(
            as.formula(paste0(treated, " ~ .")),
            data                = train,
            state.specification = ss,
            expected.model.size = kExpectedModelSize,
            expected.r2         = kExpectedR2,
            prior.df            = kPriorDf,
            niter               = niter,
            seed                = 1, ping = 0,
            model.options       = BstsOptions(save.prediction.errors = TRUE)
        )
        time(bsts.model$original.series) <- time(train)
        impact <- CausalImpact(bsts.model          = bsts.model,
                               post.period.response = as.vector(post_response))

    } else {
        # local_level: standard CausalImpact call
        impact <- CausalImpact(
            train, pre_period, post_period,
            model.args = list(
                niter              = niter,
                standardize.data   = standardize_data,
                prior.level.sd     = prior_level_sd,
                nseasons           = nseasons,
                season.duration    = season_duration,
                dynamic.regression = dynamic_regression
            )
        )
    }

    # ── Fit metrics ───────────────────────────────────────────────────────────
    pre       <- window(impact$series, start = pre_period[1], end = pre_period[2])
    mape_pre  <- mean(abs(pre$response - pre$point.pred) / abs(pre$response),  na.rm = TRUE)
    wmape_pre <- sum( abs(pre$response - pre$point.pred), na.rm = TRUE) /
                 sum( abs(pre$response), na.rm = TRUE)
    message(sprintf("Pre-period: MAPE=%.1f%%  WMAPE=%.1f%%",
                    mape_pre * 100, wmape_pre * 100))

    mape_rev <- NA_real_; wmape_rev <- NA_real_
    if (!is.null(reversion_period)) {
        rev       <- window(impact$series, start = reversion_period[1], end = reversion_period[2])
        mape_rev  <- mean(abs(rev$response - rev$point.pred) / abs(rev$response),  na.rm = TRUE)
        wmape_rev <- sum( abs(rev$response - rev$point.pred), na.rm = TRUE) /
                     sum( abs(rev$response), na.rm = TRUE)
        message(sprintf("Reversion:  MAPE=%.1f%%  WMAPE=%.1f%%",
                        mape_rev * 100, wmape_rev * 100))
    }

    # ── Save outputs ──────────────────────────────────────────────────────────
    dir.create(outpath, recursive = TRUE, showWarnings = FALSE)

    # fit_metrics.csv — append each iteration
    metrics_path <- file.path(outpath, "fit_metrics.csv")
    fit_row <- data.frame(
        ver              = ver,
        note             = ifelse(is.null(note), "", note),
        treated          = treated,
        trend_model      = trend_model,
        pre_period       = paste(pre_period,  collapse = " / "),
        post_period      = paste(post_period, collapse = " / "),
        mape_pre         = round(mape_pre,  4),
        wmape_pre        = round(wmape_pre, 4),
        reversion_period = if (!is.null(reversion_period))
                               paste(reversion_period, collapse = " / ") else NA_character_,
        mape_reversion   = round(mape_rev,  4),
        wmape_reversion  = round(wmape_rev, 4),
        nseasons         = nseasons,
        niter            = niter,
        covariates       = paste(covariates, collapse = " | "),
        stringsAsFactors = FALSE
    )
    write.table(fit_row, file = metrics_path, append = file.exists(metrics_path),
                sep = ",", row.names = FALSE, col.names = !file.exists(metrics_path))

    # Model object
    save(impact, file = file.path(outpath, paste0("impact_", ver, ".rda")))

    # Text report
    sink(file.path(outpath, paste0("report_", ver, ".txt")))
    cat(sprintf("=== %s | ver: %s ===\n", treated, ver))
    if (!is.null(note)) cat(sprintf("Note: %s\n\n", note))
    print(summary(impact))
    cat("\n")
    print(summary(impact, "report"))
    sink()

    # PDF charts
    pdf(file.path(outpath, paste0("charts_", ver, ".pdf")))
    tryCatch({
        point_fmt <- format_format(big.mark = ",", decimal.mark = ".", scientific = FALSE)
        plot(impact$model$bsts.model, "coefficients")
        plot(impact$model$bsts.model, "components")
        p <- plot(impact)
        print(p + scale_y_continuous(labels = point_fmt))
    }, error = function(e) message("Chart warning: ", e$message))
    dev.off()

    invisible(list(impact      = impact,
                   fit_metrics = fit_row,
                   mape_pre    = mape_pre,
                   wmape_pre   = wmape_pre))
}


#' Compare model iterations ranked by pre-period MAPE
compare_model_versions <- function(outpath) {
    f <- file.path(outpath, "fit_metrics.csv")
    if (!file.exists(f)) stop("fit_metrics.csv not found. Run causal_impact_with_covariates first.")
    m <- read.csv(f, stringsAsFactors = FALSE)
    m <- m[order(m$mape_pre), ]
    cat("\n=== Model versions ranked by pre-period MAPE ===\n")
    print(m[, intersect(c("ver","note","trend_model","mape_pre","wmape_pre",
                           "mape_reversion","wmape_reversion"), names(m))])
    invisible(m)
}
