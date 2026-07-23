library(DBI)

# ---------------------------------------------------
# Get Total Debits
# ---------------------------------------------------
get_total_debits <- function(conn, user_no) {
    query <- "
        SELECT
            COALESCE(SUM(rl.debit), 0) AS total_debits
        FROM 
            record_lines rl
        INNER JOIN records r
            ON rl.ref_no = r.ref_no
        WHERE
            r.user_no = ? AND 
            r.status <> 'voided';
    "

    result <- dbGetQuery(
        conn,
        query,
        params = list(user_no)
    )

    return(result$total_debits[1])
}


# ---------------------------------------------------
# Get Total Credits
# ---------------------------------------------------
get_total_credits <- function(conn, user_no) {
    query <- "
        SELECT
            COALESCE(SUM(rl.credit), 0) AS total_credits
        FROM 
            record_lines rl
        INNER JOIN records r
            ON rl.ref_no = r.ref_no
        WHERE
            r.user_np = ? AND 
            r.status <> 'voided';
    "

    result <- dbGetQuery(
        conn,
        query,
        params = list(user_no)
    )

    return(result$total_credits[1])
}


# ---------------------------------------------------
# Get Monthly Revenue
# ---------------------------------------------------
get_monthly_revenue <- function(conn, user_no) {
    query <- "
        SELECT
            YEAR(r.transaction_date) AS year,
            MONTH(r.transaction_date) AS month,
            SUM(rl.credit - rl.debit) AS y

        FROM records r

        INNER JOIN record_lines rl
            ON r.ref_no = rl.ref_no

        WHERE r.user_no = ? AND 
            rl.account_name = 'Revenue' AND 
            r.status <> 'voided'

        GROUP BY 
            YEAR(r.transaction_date), 
            MONTH(r.transaction_date)

        ORDER BY 
            YEAR(r.transaction_date), 
            MONTH(r.transaction_date);
    "

    df <- dbGetQuery(
        conn,
        query,
        params = list(user_no)
    )


    if (nrow(df) > 0) {
        df$year <- as.integer(df$year)
        df$month <- as.integer(df$month)

        df$ds <- as.Date(
            sprintf("%04d-%02d-01", df$year, df$month)
        )
        df <- df[, c("ds", "y")]
    } else {
        df <- data.frame(
            ds = as.Date(character()),
            y = numeric()
        )
    }

    return(df)
}


# ---------------------------------------------------
# Get Total Expenses
# ---------------------------------------------------
get_total_expenses <- function(conn, user_no) {
    query <- "
        SELECT
            COALESCE(SUM(rl.debit),0) AS expenses

        FROM records r

        INNER JOIN record_lines rl
            ON r.ref_no = rl.ref_no

        WHERE r.user_no = ? AND 
            rl.account_name = 'Expense' AND 
            r.status <> 'voided';
    "

    result <- dbGetQuery(
        conn,
        query,
        params = list(user_no)
    )

    return(result$expenses[1])

}