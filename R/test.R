library(jsonlite)
library(DBI)
library(RMariaDB)
source("data_access.r")
source("simulation.R")

args <- commandArgs(trailingOnly = TRUE)
user_no <- if (length(args) > 0) as.integer(args[1]) else NA_integer_
periods <- if (length(args) > 1) as.integer(args[2]) else 6

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
    conn = conn,
    branch_no = 1,
    seasonality = 15,
    inflation = 4.2,
    competition = 10
)

print(result)

DBI::dbDisconnect(conn)