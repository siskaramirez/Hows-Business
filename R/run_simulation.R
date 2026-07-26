library(jsonlite)
library(DBI)
library(RMariaDB)
source("data_access.R")
source("simulation.R")
source("forecasting.R")


args <- commandArgs(trailingOnly = TRUE)
user_no <- if (length(args) > 0) as.integer(args[1]) else NA_integer_
price <- if (length(args) > 1) as.numeric(args[2]) else 0
volume <- if (length(args) > 2) as.numeric(args[3]) else 0
marketing <- if (length(args) > 3) as.numeric(args[4]) else 0
raw_material <- if (length(args) > 4) as.numeric(args[5]) else 0
wages <- if (length(args) > 5) as.numeric(args[6]) else 0
utilities <- if (length(args) > 6) as.numeric(args[7]) else 0
seasonality <- if (length(args) > 7) as.numeric(args[8]) else 0
inflation <- if (length(args) > 8) as.numeric(args[9]) else 0
competition <- if (length(args) > 9) as.numeric(args[10]) else 0

if (is.na(user_no)) {
    cat(toJSON(list(error = "Missing or invalid user_no."), auto_unbox = TRUE))
    quit(status = 1)
}

conn <- tryCatch(
    connect_database(),
    error = function(e) {
        cat(toJSON(list(error = paste("DB connection failed:", conditionMessage(e))), auto_unbox = TRUE))
        quit(status = 1)
    }
)

result <- predict_business_health(
    conn,
    user_no,
    price,
    volume,
    marketing,
    raw_material,
    wages,
    utilities,
    seasonality,
    inflation,
    competition
)

cat(toJSON(result, auto_unbox = TRUE, null = "null"))
dbDisconnect(conn)
