library(jsonlite)
library(readxl)

args <- commandArgs(trailingOnly = TRUE)
excel_path <- if (length(args) > 0) args[1] else ""

if (!nzchar(excel_path) || !file.exists(excel_path)) {
    stop(paste("Excel file not found at:", excel_path))
}

raw_data <- read_excel(excel_path)
required_columns <- c(
    "Date",
    "Description",
    "Account Type",
    "Account Name",
    "Amount",
    "Payment Method",
    "Invoice No."
)
missing_columns <- setdiff(required_columns, names(raw_data))
if (length(missing_columns) > 0) {
    stop(paste("Missing required columns:", paste(missing_columns, collapse = ", ")))
}

# The template # column is only a visual guide and may be prefilled far below
# the user's data. Keep only rows containing at least one real transaction field.
has_transaction_data <- apply(
    raw_data[, required_columns, drop = FALSE],
    1,
    function(row) {
        any(!is.na(row) & nzchar(trimws(as.character(row))))
    }
)
raw_data <- raw_data[has_transaction_data, , drop = FALSE]

parse_date <- function(value) {
    if (is.na(value) || !nzchar(trimws(as.character(value)))) {
        return(NA_character_)
    }
    if (inherits(value, "Date") || inherits(value, "POSIXt")) {
        return(format(as.Date(value), "%Y-%m-%d"))
    }

    text <- trimws(as.character(value))
    for (date_format in c("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")) {
        parsed <- suppressWarnings(as.Date(text, format = date_format))
        if (!is.na(parsed)) {
            return(format(parsed, "%Y-%m-%d"))
        }
    }
    NA_character_
}

parse_amount <- function(value) {
    text <- gsub("[^0-9.-]", "", as.character(value))
    suppressWarnings(as.numeric(text))
}

clean_text <- function(values) {
    result <- trimws(as.character(values))
    result[is.na(values) | result == "NA"] <- NA_character_
    result
}

transactions <- data.frame(
    transaction_date = vapply(raw_data[["Date"]], parse_date, character(1)),
    description = clean_text(raw_data[["Description"]]),
    account_name = clean_text(raw_data[["Account Type"]]),
    transaction_type = clean_text(raw_data[["Account Name"]]),
    amount = vapply(raw_data[["Amount"]], parse_amount, numeric(1)),
    payment_method = clean_text(raw_data[["Payment Method"]]),
    invoice_no = clean_text(raw_data[["Invoice No."]]),
    stringsAsFactors = FALSE
)

cat(
    toJSON(
        transactions,
        dataframe = "rows",
        auto_unbox = TRUE,
        na = "null",
        pretty = TRUE
    )
)
