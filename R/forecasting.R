library(prophet)
library(jsonlite)
library(DBI)
library(RMariaDB)
source("data_access.R")

connect_database <- function() {
    config_path <- "../db_config.json"
    if (file.exists(config_path)) {
        db_cfg <- fromJSON(config_path)
    } else {
        db_cfg <- list(host = "localhost", port = 3306, user = "root", password = "Japellako99", database = "delikart")
    }
    
    dbConnect(
        RMariaDB::MariaDB(),
        dbname = db_cfg$database,
        host = db_cfg$host,
        port = as.integer(db_cfg$port),
        user = db_cfg$user,
        password = db_cfg$password
    )
}

# --- Classify a single confidence interval width into a label ---
classify_confidence <- function(yhat, lower, upper) {
    if (yhat == 0) return("Low confidence")
    spread_pct <- (upper - lower) / abs(yhat) * 100
    if (spread_pct < 20) return("High confidence")
    if (spread_pct < 50) return("Moderate confidence")
    return("Low confidence")
}

# --- Classify month-over-month change ---
classify_trend_point <- function(current, previous) {
    if (is.na(previous) || previous == 0) return(list(direction = "flat", pct_change = 0))
    pct <- ((current - previous) / previous) * 100
    direction <- if (pct > 2) "up" else if (pct < -2) "down" else "flat"
    list(direction = direction, pct_change = round(pct, 1))
}

# --- Detect anomalies: actual vs model's fitted value on historical data ---
detect_anomalies <- function(revenue, fitted_df) {
    merged <- merge(revenue, fitted_df[, c("ds", "yhat")], by = "ds")
    if (nrow(merged) == 0) return(list())

    merged$residual <- merged$y - merged$yhat
    resid_sd <- sd(merged$residual)
    if (is.na(resid_sd) || resid_sd == 0) return(list())

    merged$z_score <- merged$residual / resid_sd
    anomalies <- merged[abs(merged$z_score) > 1.5, ]

    if (nrow(anomalies) == 0) return(list())

    lapply(seq_len(nrow(anomalies)), function(i) {
        row <- anomalies[i, ]
        list(
        ds = as.character(row$ds),
        actual = round(row$y, 2),
        expected = round(row$yhat, 2),
        note = if (row$residual > 0) "Higher than expected" else "Lower than expected"
        )
    })
}


forecast_sales <- function(conn, user_no, periods = 6, future_only = TRUE) {

    # ----------------------------------------
    # Retrieve Historical Revenue
    # ----------------------------------------
    revenue <- get_monthly_revenue(
        conn,
        user_no
    )

    # ----------------------------------------
    # Validate Data
    # ----------------------------------------
    if (nrow(revenue) < 12) {
        stop("At least 12 months of revenue is required.")
    }

    # ----------------------------------------
    # Train Prophet Model
    # ----------------------------------------
    model <- prophet(
        revenue,
        yearly.seasonality = FALSE,
        weekly.seasonality = FALSE,
        daily.seasonality = FALSE
    )

    # ----------------------------------------
    # Generate Future Dates
    # ----------------------------------------
    future <- make_future_dataframe(
        model,
        periods = periods,
        freq = "month"
    )

    # ----------------------------------------
    # Predict Revenue
    # ----------------------------------------
    full_forecast <- predict(
        model,
        future
    )

    # Anomalies use ALL fitted values against historical actuals
    anomalies <- detect_anomalies(revenue, full_forecast[, c("ds", "yhat")])

    # ----------------------------------------
    # Keep Only Required Columns
    # ----------------------------------------
    forecast_only <- full_forecast[full_forecast$ds > max(revenue$ds), c(
            "ds",
            "yhat",
            "yhat_lower",
            "yhat_upper"
        )
    ]

    # --- Per-point confidence + month-over-month trend ---
    points <- list()
    prev_value <- tail(revenue$y, 1)  # last known actual, to compare against first forecast point

    for (i in seq_len(nrow(forecast_only))) {
        row <- forecast_only[i, ]
        trend_point <- classify_trend_point(row$yhat, prev_value)
        points[[i]] <- list(
            ds = as.character(row$ds),
            yhat = round(row$yhat, 2),
            yhat_lower = round(row$yhat_lower, 2),
            yhat_upper = round(row$yhat_upper, 2),
            confidence = classify_confidence(row$yhat, row$yhat_lower, row$yhat_upper),
            trend_direction = trend_point$direction,
            trend_pct_change = trend_point$pct_change
        )
        prev_value <- row$yhat
    }

    # --- Overall trend summary across the whole forecast horizon ---
    overall_pct <- if (forecast_only$yhat[1] != 0) {
        round(((tail(forecast_only$yhat, 1) - forecast_only$yhat[1]) / abs(forecast_only$yhat[1])) * 100, 1)
    } else {
        0
    }
    overall_direction <- if (overall_pct > 2) "Upward" else if (overall_pct < -2) "Downward" else "Stable"
    trend_summary <- sprintf(
        "%s trend, %+.1f%% projected over %d months",
        overall_direction, overall_pct, periods
    )

    historical <- data.frame(
        ds = as.character(revenue$ds),
        actual = round(revenue$y, 2)
    )

    list(
        points = points,
        historical = historical,
        trend_summary = trend_summary,
        overall_direction = overall_direction,
        overall_pct_change = overall_pct,
        anomalies = anomalies
    )
}