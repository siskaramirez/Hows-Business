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


get_schedule_features <- function(dates, schedule_path = NULL) {
    empty <- data.frame(
        schedule_intensity = rep(0, length(dates)),
        business_phase = rep(NA_character_, length(dates)),
        stringsAsFactors = FALSE
    )
    if (is.null(schedule_path) || !nzchar(schedule_path) || !file.exists(schedule_path)) {
        return(empty)
    }

    schedule <- tryCatch(
        read.csv(schedule_path, stringsAsFactors = FALSE, check.names = FALSE),
        error = function(e) NULL
    )
    required <- c("Phase", "Start_Date", "End_Date")
    if (is.null(schedule) || !all(required %in% names(schedule))) {
        return(empty)
    }

    schedule$start <- as.Date(schedule$Start_Date, format = "%m/%d/%Y")
    schedule$end <- as.Date(schedule$End_Date, format = "%m/%d/%Y")
    schedule <- schedule[!is.na(schedule$start) & !is.na(schedule$end), ]
    if (nrow(schedule) == 0) {
        return(empty)
    }

    result <- empty
    for (i in seq_along(dates)) {
        month_start <- as.Date(format(dates[i], "%Y-%m-01"))
        month_end <- seq(month_start, by = "month", length.out = 2)[2] - 1
        overlap_days <- pmax(
            0,
            pmin(as.numeric(schedule$end), as.numeric(month_end)) -
                pmax(as.numeric(schedule$start), as.numeric(month_start)) + 1
        )
        active <- overlap_days > 0
        if (!any(active)) {
            next
        }

        phases <- tolower(schedule$Phase)
        instructional_days <- sum(
            overlap_days[grepl("instruction", phases)],
            na.rm = TRUE
        )
        event_days <- sum(
            overlap_days[grepl("enrollment|opening|end-of-term|closing", phases)],
            na.rm = TRUE
        )
        break_days <- sum(
            overlap_days[grepl("break", phases)],
            na.rm = TRUE
        )
        days_in_month <- as.numeric(month_end - month_start) + 1
        result$schedule_intensity[i] <- (
            instructional_days + (event_days * 0.5) - break_days
        ) / days_in_month
        result$business_phase[i] <- paste(
            unique(schedule$Phase[active]),
            collapse = " / "
        )
    }
    result
}


forecast_sales <- function(
    conn,
    user_no,
    periods = 12,
    future_only = TRUE,
    schedule_path = NULL
) {
    revenue <- get_monthly_revenue(conn, user_no)
    if (nrow(revenue) < 1) {
        stop("At least one month of revenue is required.")
    }

    revenue$ds <- as.Date(revenue$ds)
    current_month <- as.Date(format(Sys.Date(), "%Y-%m-01"))
    anchor <- max(current_month, max(revenue$ds))
    first_month <- min(revenue$ds)
    annual_end <- as.Date(sprintf("%d-12-01", as.integer(format(anchor, "%Y")) + 5))
    requested_end <- seq(anchor, by = "month", length.out = periods + 1)[periods + 1]
    forecast_end <- max(annual_end, requested_end)
    timeline <- seq(first_month, forecast_end, by = "month")
    time_index <- seq_along(timeline)
    observed_index <- match(revenue$ds, timeline)
    schedule_features <- get_schedule_features(timeline, schedule_path)

    training <- data.frame(
        y = revenue$y,
        time_index = observed_index,
        annual_sin = sin(2 * pi * observed_index / 12),
        annual_cos = cos(2 * pi * observed_index / 12),
        schedule_intensity = schedule_features$schedule_intensity[observed_index]
    )
    prediction_data <- data.frame(
        time_index = time_index,
        annual_sin = sin(2 * pi * time_index / 12),
        annual_cos = cos(2 * pi * time_index / 12),
        schedule_intensity = schedule_features$schedule_intensity
    )
    schedule_rows <- sum(training$schedule_intensity != 0, na.rm = TRUE)
    schedule_variation <- sd(training$schedule_intensity, na.rm = TRUE)
    use_schedule_feature <- (
        nrow(training) >= 12 &&
        schedule_rows >= 2 &&
        !is.na(schedule_variation) &&
        schedule_variation > 0
    )

    if (nrow(training) == 1) {
        fitted_values <- rep(training$y[1], length(timeline))
        residual_sd <- max(abs(training$y[1]) * 0.15, 1)
    } else {
        model <- if (nrow(training) >= 12 && use_schedule_feature) {
            lm(
                y ~ time_index + annual_sin + annual_cos + schedule_intensity,
                data = training
            )
        } else if (nrow(training) >= 12) {
            lm(y ~ time_index + annual_sin + annual_cos, data = training)
        } else {
            lm(y ~ time_index, data = training)
        }
        fitted_values <- as.numeric(predict(model, newdata = prediction_data))
        residual_sd <- sd(residuals(model))
        if (is.na(residual_sd) || residual_sd <= 0) {
            residual_sd <- max(mean(abs(training$y)) * 0.15, 1)
        }
    }

    months_after_anchor <- pmax(0, time_index - match(anchor, timeline))
    uncertainty <- residual_sd * (1.96 + sqrt(months_after_anchor / 12) * 0.35)
    full_forecast <- data.frame(
        ds = timeline,
        yhat = pmax(0, fitted_values),
        yhat_lower = pmax(0, fitted_values - uncertainty),
        yhat_upper = pmax(0, fitted_values + uncertainty),
        business_phase = schedule_features$business_phase,
        schedule_intensity = schedule_features$schedule_intensity
    )
    anomalies <- detect_anomalies(revenue, full_forecast[, c("ds", "yhat")])

    forecast_all <- full_forecast[full_forecast$ds > anchor, ]
    forecast_only <- head(forecast_all, periods)
    points <- list()
    anchor_actual <- revenue$y[revenue$ds == anchor]
    prev_value <- if (length(anchor_actual)) {
        anchor_actual[1]
    } else {
        full_forecast$yhat[full_forecast$ds == anchor][1]
    }
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
            trend_pct_change = trend_point$pct_change,
            business_phase = if (is.na(row$business_phase)) NULL else row$business_phase,
            schedule_intensity = round(row$schedule_intensity, 3)
        )
        prev_value <- row$yhat
    }

    historical_dates <- timeline[timeline <= anchor]
    historical_model <- full_forecast[full_forecast$ds <= anchor, ]
    actual_values <- revenue$y[match(historical_dates, revenue$ds)]
    historical <- data.frame(
        ds = as.character(historical_dates),
        actual = round(actual_values, 2),
        forecast = round(historical_model$yhat, 2),
        business_phase = historical_model$business_phase
    )

    # Current year is the starting annual point; the next five calendar years
    # are projections. Actual months are retained and missing/future months use
    # the fitted model so each point represents a complete calendar year.
    start_year <- as.integer(format(anchor, "%Y"))
    annual_years <- seq(start_year, start_year + 5)
    annual_points <- lapply(annual_years, function(year) {
        year_rows <- full_forecast[format(full_forecast$ds, "%Y") == as.character(year), ]
        actual_for_year <- revenue$y[format(revenue$ds, "%Y") == as.character(year)]
        actual_by_date <- revenue$y[match(year_rows$ds, revenue$ds)]
        combined <- ifelse(is.na(actual_by_date), year_rows$yhat, actual_by_date)
        list(
            year = year,
            yhat = round(sum(combined, na.rm = TRUE), 2),
            actual = if (length(actual_for_year)) round(sum(actual_for_year), 2) else NULL
        )
    })

    historical_years <- seq(
        as.integer(format(first_month, "%Y")),
        start_year
    )
    historical_yearly <- lapply(historical_years, function(year) {
        actual_for_year <- revenue$y[format(revenue$ds, "%Y") == as.character(year)]
        model_for_year <- full_forecast$yhat[
            format(full_forecast$ds, "%Y") == as.character(year)
        ]
        list(
            year = year,
            actual = if (length(actual_for_year)) round(sum(actual_for_year), 2) else NULL,
            forecast = if (length(model_for_year)) {
                round(sum(model_for_year), 2)
            } else {
                NULL
            }
        )
    })

    overall_pct <- if (nrow(forecast_only) > 1 && forecast_only$yhat[1] != 0) {
        round(
            ((tail(forecast_only$yhat, 1) - forecast_only$yhat[1]) /
                abs(forecast_only$yhat[1])) * 100,
            1
        )
    } else {
        0
    }
    overall_direction <- if (overall_pct > 2) {
        "Upward"
    } else if (overall_pct < -2) {
        "Downward"
    } else {
        "Stable"
    }

    list(
        points = points,
        historical = historical,
        annual_points = annual_points,
        historical_yearly = historical_yearly,
        forecast_anchor = as.character(anchor),
        schedule_feature_used = use_schedule_feature,
        schedule_dataset = if (is.null(schedule_path)) NULL else basename(schedule_path),
        trend_summary = sprintf(
            "%s trend, %+.1f%% projected over %d months",
            overall_direction, overall_pct, periods
        ),
        overall_direction = overall_direction,
        overall_pct_change = overall_pct,
        anomalies = anomalies
    )
}
