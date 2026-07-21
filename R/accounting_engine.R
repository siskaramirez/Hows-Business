library(dplyr)

calculate_account_balances <- function(joined_df) {
    
    account_balances <- joined_df %>%
        mutate(
            balance = case_when(
                # Assets and expenses normally have debit balances
                account_name %in% c("Asset", "Expense") ~ debit - credit,

                # Liabilities, equity, and revenue normally have credit balances
                account_name %in% c("Liability", "Equity", "Revenue") ~ credit - debit,
                TRUE ~ 0
            )
        ) %>%
        group_by(transaction_type, account_name) %>%
        summarise(
        Amount = sum(balance),
        .groups = "drop"
    )
    
    return(account_balances)
}