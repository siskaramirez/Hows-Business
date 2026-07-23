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
    forecast <- predict(
        model,
        future
    )

    # ----------------------------------------
    # Keep Only Required Columns
    # ----------------------------------------
    forecast <- forecast[, c(
            "ds",
            "yhat",
            "yhat_lower",
            "yhat_upper"
        )
    ]

    # ----------------------------------------
    # Return Future Forecast Only (Default)
    # ----------------------------------------
    if (future_only) {
        forecast <- forecast[ forecast$ds > max(revenue$ds), ]
    }

    return(forecast)
}