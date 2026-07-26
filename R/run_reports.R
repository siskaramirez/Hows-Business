library(jsonlite)
library(DBI)
library(RMariaDB)


args <- commandArgs(trailingOnly = TRUE)
input_path <- if (length(args) > 0) args[1] else ''


if (nzchar(input_path) && file.exists(input_path)) {
    payload <- fromJSON(input_path)
} else {
    config_path <- "../db_config.json"
    if (file.exists(config_path)) {
        db_cfg <- fromJSON(config_path)
        payload <- list(
            report_type = 'income_statement',
            month = '',
            user_no = NA_integer_,
            db = list(host=db_cfg$host, port=db_cfg$port, user=db_cfg$user, password=db_cfg$password, database=db_cfg$database)
        )
    } else {
        payload <- list(
            report_type = 'income_statement', 
            month = '', 
            user_no = NA_integer_,
            db = list(host='localhost', port=3306, user='root', password='Japellako99', database='delikart')
        )
    }
}

connect_database <- function(config) {
    dbConnect(
        RMariaDB::MariaDB(),
        dbname = config$database,
        host = config$host,
        port = as.integer(config$port),
        user = config$user,
        password = config$password
    )
}

normalize_month <- function(month_name) {
    if (is.null(month_name) || is.na(month_name)) {
        return(NA_integer_)
    }

    trimmed <- trimws(as.character(month_name))
    if (!nzchar(trimmed)) {
        return(NA_integer_)
    }

    month_num <- suppressWarnings(as.integer(trimmed))
    if (!is.na(month_num) && month_num >= 1 && month_num <= 12) {
        return(month_num)
    }

    month_index <- match(tolower(trimmed), tolower(month.name))
    if (!is.na(month_index)) {
        return(month_index)
    }

    NA_integer_
}

filter_records_by_month <- function(df, month_name) {
    month_num <- normalize_month(month_name)
    if (is.na(month_num)) {
        return(df)
    }

    if (!('transaction_date' %in% names(df))) {
        return(df)
    }

    parsed_dates <- tryCatch(as.Date(df$transaction_date), error = function(e) NA)
    if (all(is.na(parsed_dates))) {
        return(df)
    }

    current_year <- as.integer(format(Sys.Date(), "%Y"))
    keep <- as.integer(format(parsed_dates, "%m")) == month_num &
        as.integer(format(parsed_dates, "%Y")) == current_year
    df[keep, , drop = FALSE]
}

get_record_lines <- function(con, user_no) {
    query <- "
        SELECT
            rl.line_no, rl.ref_no, rl.debit, rl.credit,
            r.account_name, r.transaction_type, r.transaction_date
        FROM record_lines rl
        INNER JOIN records r ON rl.ref_no = r.ref_no
        WHERE r.status = 'active' AND r.user_no = ?
    "
    dbGetQuery(con, query, params = list(user_no))
}

calculate_account_balances <- function(record_lines_df) {
    debit_side <- record_lines_df$account_name %in% c("Asset", "Expense")
    credit_side <- record_lines_df$account_name %in% c("Liability", "Equity", "Revenue")
    record_lines_df$balance <- ifelse(
        debit_side,
        record_lines_df$debit - record_lines_df$credit,
        ifelse(credit_side, record_lines_df$credit - record_lines_df$debit, 0)
    )

    aggregate(
        balance ~ transaction_type + account_name,
        data = record_lines_df,
        FUN = sum
    ) |>
        setNames(c("transaction_type", "account_name", "Amount"))
}

account_details <- function(account_balances, account_name) {
    rows <- account_balances[
        account_balances$account_name == account_name,
        c("transaction_type", "Amount"),
        drop = FALSE
    ]
    names(rows)[1] <- "Account"
    rows
}

account_total <- function(account_balances, account_name) {
    sum(account_balances$Amount[account_balances$account_name == account_name])
}

generate_income_statement <- function(account_balances) {
    total_revenue <- account_total(account_balances, "Revenue")
    total_expenses <- account_total(account_balances, "Expense")

    list(
        report_type = 'income_statement',
        revenue_details = account_details(account_balances, "Revenue"),
        expense_details = account_details(account_balances, "Expense"),
        total_revenue = total_revenue,
        total_expenses = total_expenses,
        net_profit = total_revenue - total_expenses
    )
}

generate_balance_sheet <- function(account_balances) {
    total_assets <- account_total(account_balances, "Asset")
    total_liabilities <- account_total(account_balances, "Liability")
    total_equity <- account_total(account_balances, "Equity")

    list(
        report_type = 'balance_sheet',
        asset_details = account_details(account_balances, "Asset"),
        liability_details = account_details(account_balances, "Liability"),
        equity_details = account_details(account_balances, "Equity"),
        total_assets = total_assets,
        total_liabilities = total_liabilities,
        total_equity = total_equity
    )
}

generate_trial_balance <- function(account_balances) {
    trial_balance <- data.frame(
        Account = account_balances$transaction_type,
        `Account Type` = account_balances$account_name,
        Debit = ifelse(
            account_balances$account_name %in% c("Asset", "Expense"),
            pmax(account_balances$Amount, 0),
            0
        ),
        Credit = ifelse(
            account_balances$account_name %in% c("Liability", "Equity", "Revenue"),
            pmax(account_balances$Amount, 0),
            0
        ),
        check.names = FALSE
    )

    list(
        report_type = 'trial_balance',
        trial_balance = as.data.frame(trial_balance),
        total_debit = sum(trial_balance$Debit),
        total_credit = sum(trial_balance$Credit)
    )
}

generate_cash_flow <- function(account_balances) {
    rows <- account_balances[
        account_balances$account_name %in% c("Asset", "Liability", "Equity"),
        c("account_name", "transaction_type", "Amount"),
        drop = FALSE
    ]
    names(rows) <- c("Account Type", "Account", "Amount")

    list(
        report_type = 'cash_flow',
        cash_flow_details = rows
    )
}

con <- tryCatch(
    connect_database(payload$db),
    error = function(e) {
        cat(toJSON(list(error = paste("DB connection failed:", conditionMessage(e))), auto_unbox = TRUE))
        quit(status = 1)
    }
)
if (is.null(con)) {
    cat(toJSON(list(error = 'Unable to connect to MySQL database.'), auto_unbox = TRUE))
    quit(status = 1)
}

user_no <- suppressWarnings(as.integer(payload$user_no))
if (is.na(user_no)) {
    cat(toJSON(list(error = 'Missing or invalid user_no.'), auto_unbox = TRUE))
    dbDisconnect(con)
    quit(status = 1)
}

record_lines_df <- get_record_lines(con, user_no)
record_lines_df <- filter_records_by_month(record_lines_df, payload$month)

if (nrow(record_lines_df) == 0) {
    result <- list(report_type = payload$report_type, message = 'No financial data found for this database.', revenue_details = data.frame(), expense_details = data.frame(), total_revenue = 0, total_expenses = 0, net_profit = 0)
    cat(toJSON(result, auto_unbox = TRUE, null = 'null'))
    dbDisconnect(con)
    quit(status = 0)
}

account_balances <- calculate_account_balances(record_lines_df)

if (payload$report_type == 'income_statement') {
    result <- generate_income_statement(account_balances)
} else if (payload$report_type == 'balance_sheet') {
    result <- generate_balance_sheet(account_balances)
} else if (payload$report_type == 'trial_balance') {
    result <- generate_trial_balance(account_balances)
} else if (payload$report_type == 'cash_flow') {
    result <- generate_cash_flow(account_balances)
} else {
    result <- list(report_type = payload$report_type, message = 'This report type is not implemented yet.', revenue_details = data.frame(), expense_details = data.frame(), total_revenue = 0, total_expenses = 0, net_profit = 0)
}

cat(toJSON(result, auto_unbox = TRUE, null = 'null'))
flush.console()
dbDisconnect(con)
quit(status = 0)
