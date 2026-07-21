library(dplyr)

normal_balance <- function(account_name) {
    case_when(
        account_name %in% c("Asset", "Expense") ~ "debit",
        account_name %in% c("Liability", "Equity", "Revenue") ~ "credit",

        TRUE ~ NA_character_
    )
}

# Create the record_lines entry for a single records row
generate_line_for_record <- function(con, ref_no, account_name, amount) {
    side <- normal_balance_side(account_name)
    if (is.na(side)) {
        warning(paste("Unknown account_name for ref_no", ref_no, ":", account_name))
        return(invisible(NULL))
    }

    debit_amt  <- if (side == "debit") amount else 0
    credit_amt <- if (side == "credit") amount else 0

    dbExecute(
        con,
        "INSERT INTO record_lines (ref_no, debit, credit) VALUES (?, ?, ?)",
        params = list(ref_no, debit_amt, credit_amt)
    )
}

# Batch version (after inserting new records)
generate_lines_for_new_records <- function(con, records_df) {
    for (i in seq_len(nrow(records_df))) {
        row <- records_df[i, ]
        generate_line_for_record(con, row$ref_no, row$account_name, row$amount)
    }
}