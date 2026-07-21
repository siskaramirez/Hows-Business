library(jsonlite)
library(DBI)
library(RMariaDB)
library(dplyr)


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

    df %>%
        mutate(parsed_date = parsed_dates) %>%
        filter(as.integer(format(parsed_date, "%m")) == month_num, as.integer(format(parsed_date, "%Y")) == 2026) %>%
        select(-parsed_date)
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
    record_lines_df %>%
        mutate(
            balance = case_when(
                account_name %in% c("Asset", "Expense") ~ debit - credit,
                account_name %in% c("Liability", "Equity", "Revenue") ~ credit - debit,
                TRUE ~ 0
            )
        ) %>%
        group_by(transaction_type, account_name) %>%
        summarise(Amount = sum(balance), .groups = "drop")
}

generate_income_statement <- function(account_balances) {
    total_revenue <- account_balances %>% 
        filter(account_name == 'Revenue') %>% 
        summarise(total = sum(Amount)) %>% 
        pull(total)

    total_expenses <- account_balances %>% 
        filter(account_name == 'Expense') %>% 
        summarise(total = sum(Amount)) %>% 
        pull(total)

    if (length(total_revenue) == 0) total_revenue <- 0
    if (length(total_expenses) == 0) total_expenses <- 0

    list(
        report_type = 'income_statement',
        revenue_details = as.data.frame(account_balances %>% filter(account_name == 'Revenue') %>% rename(Account = transaction_type) %>% select(Account, Amount)),
        expense_details = as.data.frame(account_balances %>% filter(account_name == 'Expense') %>% rename(Account = transaction_type) %>% select(Account, Amount)),
        total_revenue = total_revenue,
        total_expenses = total_expenses,
        net_profit = total_revenue - total_expenses
    )
}

generate_balance_sheet <- function(account_balances) {
    total_assets <- account_balances %>%
        filter(account_name == 'Asset') %>%
        summarise(total = sum(Amount)) %>%
        pull(total)

    total_liabilities <- account_balances %>%
        filter(account_name == 'Liability') %>%
        summarise(total = sum(Amount)) %>%
        pull(total)

    total_equity <- account_balances %>%
        filter(account_name == 'Equity') %>%
        summarise(total = sum(Amount)) %>%
        pull(total)

    if (length(total_assets) == 0) total_assets <- 0
    if (length(total_liabilities) == 0) total_liabilities <- 0
    if (length(total_equity) == 0) total_equity <- 0

    list(
        report_type = 'balance_sheet',
        asset_details = as.data.frame(account_balances %>% filter(account_name == 'Asset') %>% rename(Account = transaction_type) %>% select(Account, Amount)),
        liability_details = as.data.frame(account_balances %>% filter(account_name == 'Liability') %>% rename(Account = transaction_type) %>% select(Account, Amount)),
        equity_details = as.data.frame(account_balances %>% filter(account_name == 'Equity') %>% rename(Account = transaction_type) %>% select(Account, Amount)),
        total_assets = total_assets,
        total_liabilities = total_liabilities,
        total_equity = total_equity
    )
}

generate_trial_balance <- function(account_balances) {
    trial_balance <- account_balances %>%
        mutate(
            Debit = ifelse(account_name %in% c('Asset', 'Expense'), pmax(Amount, 0), 0),
            Credit = ifelse(account_name %in% c('Liability', 'Equity', 'Revenue'), pmax(Amount, 0), 0)
        ) %>%
        rename(Account = transaction_type, `Account Type` = account_name) %>%
        select(Account, `Account Type`, Debit, Credit)

    list(
        report_type = 'trial_balance',
        trial_balance = as.data.frame(trial_balance),
        total_debit = sum(trial_balance$Debit),
        total_credit = sum(trial_balance$Credit)
    )
}

generate_cash_flow <- function(account_balances) {
    cash_flow <- account_balances %>%
        filter(account_name %in% c('Asset', 'Liability', 'Equity')) %>%
        rename(Account = transaction_type, `Account Type` = account_name) %>%
        select(`Account Type`, Account, Amount)

    list(
        report_type = 'cash_flow',
        cash_flow_details = as.data.frame(cash_flow)
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