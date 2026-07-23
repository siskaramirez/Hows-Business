library(jsonlite)
library(DBI)
library(RMariaDB)
source("data_access.R")
source("simulation.R")
source("forecasting.R")


args <- commandArgs(trailingOnly = TRUE)
user_no <- if (length(args) > 0) as.integer(args[1]) else NA_integer_
seasonality <- if (length(args) > 1) as.numeric(args[2]) else 50
inflation <- if (length(args) > 2) as.numeric(args[3]) else 0
competition <- if (length(args) > 3) as.numeric(args[4]) else 0

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

result <- predict_business_health(conn, user_no, seasonality, inflation, competition)

cat(toJSON(result, auto_unbox = TRUE, null = "null"))
dbDisconnect(conn)