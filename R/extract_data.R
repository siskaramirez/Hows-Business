library(DBI)
library(RMariaDB)
library(dplyr)
library(jsonlite)
library(readxl)


args <- commandArgs(trailingOnly = TRUE)
excel_path <- ifelse(length(args) > 0, args[1], "uploads/Transaction_Template.xlsx")
user_no_arg <- if (length(args) >= 2) as.integer(args[2]) else NA_integer_
upload_id_arg <- if (length(args) >= 3) as.integer(args[3]) else NA_integer_

# =========================
# Load Database
# =========================
if (file.exists("db_config.json")) {
    config <- read_json("db_config.json")
} else if (file.exists("../db_config.json")) {
    config <- read_json("../db_config.json")
} else {
    stop("db_config.json could not be found.")
}

# =========================
# Read the uploaded Excel file
# =========================
if (!file.exists(excel_path)) {
    stop(paste("Excel file not found at:", excel_path))
}

raw_data <- read_excel(excel_path)


# =========================
# Processing & Cleaning
# =========================
cleaned_data <- raw_data %>%
    select(
        transaction_date = `Date`,
        description      = `Description`,
        account_name     = `Account Type`,
        transaction_type = `Account Name`,
        amount           = `Amount`,
        payment_method   = `Payment Method`,
        invoice_no       = `Invoice No.`
    ) %>%
    mutate(
        user_no          = user_no_arg,
        upload_id        = upload_id_arg,
        transaction_date = as.Date(`transaction_date`, format = "%d/%m/%Y"),
        amount = as.numeric(amount),
        status = "active"
    ) %>%
    filter(
        !is.na(transaction_date),
        !is.na(account_name),
        !is.na(amount)
    )


# =========================
# Format for JSON output
# =========================
transactions <- cleaned_data %>%
    mutate(
        transaction_date = as.character(transaction_date),
        amount = as.numeric(amount)
    )


# =========================
# Return JSON to FastAPI
# =========================
cat(
    toJSON(
        transactions,
        dataframe = "rows",
        auto_unbox = TRUE,
        pretty = TRUE
    )
)