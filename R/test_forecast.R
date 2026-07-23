library(DBI)
source("data_access.R")
source("forecasting.R")

conn <- connect_database()

forecast <- forecast_sales(
    conn = conn,
    user_no = 1,
    periods = 6,
    future_only = FALSE
)

print(forecast)

DBI::dbDisconnect(conn)