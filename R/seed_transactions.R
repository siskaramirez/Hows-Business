library(DBI)
library(RMariaDB)
library(jsonlite)

connect_database <- function() {
    config_path <- "db_config.json"
    if (file.exists(config_path)) {
        db_cfg <- fromJSON(config_path)
    } else {
        db_cfg <- list(
            host = "localhost",
            port = 3306,
            user = "root",
            password = "Japellako99",
            database = "delikart"
        )
    }
    dbConnect(
        RMariaDB::MariaDB(),
        dbname = db_cfg$database,
        host = db_cfg$host,
        port = as.integer(db_cfg$port),
        user = db_cfg$user,
        password = db_cfg$password
    )
}

# --- Read user_no and confirmation flag from command line ---
args <- commandArgs(trailingOnly = TRUE)
user_no <- if (length(args) > 0) as.integer(args[1]) else NA_integer_
confirmed <- length(args) > 1 && args[2] == "--yes"

if (is.na(user_no)) {
    stop("Usage: Rscript seed_transactions.R <user_no> --yes")
}

if (!confirmed) {
    stop(paste0(
        "This will DELETE ALL existing records for user_no=",
        user_no,
        " to use fake records.\n",
        "Re-run with --yes to confirm: Rscript seed_transactions.R ",
        user_no,
        " --yes"
    ))
}

set.seed(123)
conn <- connect_database()

# ----------------------------------------
# Clear only certain user's data
# ----------------------------------------
DBI::dbExecute(
    conn,
    "
  DELETE rl FROM record_lines rl
  INNER JOIN records r ON rl.ref_no = r.ref_no
  WHERE r.user_no = ?",
    params = list(user_no)
)
DBI::dbExecute(
    conn,
    "DELETE FROM records WHERE user_no = ?",
    params = list(user_no)
)

invoice_counter <- 1
next_invoice <- function() {
    invoice <- sprintf("OR-%04d", invoice_counter)
    invoice_counter <<- invoice_counter + 1
    invoice
}

payment_methods <- c("Cash", "Gcash", "Maya")
random_payment <- function() {
    sample(payment_methods, 1, prob = c(0.45, 0.35, 0.20))
}

# ----------------------------------------
# Insert Journal Entry
# ----------------------------------------
insert_transaction <- function(
    conn,
    user_no,
    invoice_no,
    entry_date,
    description,
    account_name,
    transaction_type,
    amount,
    payment_method
) {
    DBI::dbExecute(
        conn,
        "INSERT INTO records
      (user_no, transaction_date, description, account_name, amount,
       payment_method, transaction_type, invoice_no, status)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')",
        params = list(
            user_no,
            as.character(entry_date),
            description,
            account_name,
            amount,
            payment_method,
            transaction_type,
            invoice_no
        )
    )

    ref_no <- DBI::dbGetQuery(conn, "SELECT LAST_INSERT_ID() AS id")$id

    normal_debit_side <- c("Asset", "Expense")
    debit_amt <- if (account_name %in% normal_debit_side) amount else 0
    credit_amt <- if (!(account_name %in% normal_debit_side)) amount else 0

    DBI::dbExecute(
        conn,
        "INSERT INTO record_lines (ref_no, account_name, transaction_type, debit, credit)
     VALUES (?, ?, ?, ?, ?)",
        params = list(
            ref_no,
            account_name,
            transaction_type,
            debit_amt,
            credit_amt
        )
    )
}

# ----------------------------------------
# Generate Daily Sales
# ----------------------------------------
start_date <- as.Date("2025-07-01")
end_date <- as.Date("2026-07-31")
all_dates <- seq(start_date, end_date, by = "day")

insert_transaction(
    conn, user_no, next_invoice(), start_date, "Owner's initial capital",
    "Equity", "Owner's Equity", 150000, "Cash"
)
insert_transaction(
    conn, user_no, next_invoice(), start_date, "Kitchen equipment purchase",
    "Asset", "Kitchen Equipment", 75000, "Cash"
)
insert_transaction(
    conn, user_no, next_invoice(), start_date, "Initial cash on hand",
    "Asset", "Cash", 50000, "Cash"
)
insert_transaction(
    conn, user_no, next_invoice(), start_date, "Bank loan for startup",
    "Liability", "Loans Payable", 60000, "Cash"
)


for (i in seq_along(all_dates)) {
    current_day <- all_dates[i]
    weekday <- weekdays(current_day)

    sales_today <- if (weekday == "Saturday") {
        sample(6:10, 1)
    } else if (weekday %in% c("Sunday", "Friday")) {
        sample(4:8, 1)
    } else {
        sample(2:5, 1)
    }

    daily_cogs_total <- 0

    for (j in seq_len(sales_today)) {
        sale_amount <- sample(150:850, 1)
        insert_transaction(
            conn,
            user_no,
            invoice_no = next_invoice(),
            entry_date = current_day,
            description = "Food Sale",
            account_name = "Revenue",
            transaction_type = "Food Sales",
            amount = sale_amount,
            payment_method = random_payment()
        )

        cogs_amount <- round(sale_amount * runif(1, 0.35, 0.45))
        daily_cogs_total <- daily_cogs_total + cogs_amount
    }

    if (daily_cogs_total > 0) {
        insert_transaction(
            conn, user_no, next_invoice(), current_day, "Cost of goods sold",
            "Expense", "Cost of Goods Sold (COGS)", daily_cogs_total, "Cash"
        )
    }

    if (weekday == "Wednesday") {
        insert_transaction(
            conn, user_no, next_invoice(), current_day, "Inventory restock",
            "Asset", "Inventory", sample(3000:6000, 1), "Cash"
        )
    }

    if (format(current_day, "%d") == "15") {
        insert_transaction(
            conn, user_no, next_invoice(), current_day, "Supplier invoice due",
            "Liability", "Accounts Payable", sample(4000:8000, 1), "Cash"
        )
    }
    
    if (format(current_day, "%d") == "01") {
        insert_transaction(
            conn,
            user_no,
            next_invoice(),
            current_day,
            "Monthly rent",
            "Expense",
            "Canteen Rent Expense",
            sample(6000:9000, 1),
            "Cash"
        )
    }
    if (weekday == "Monday") {
        insert_transaction(
            conn,
            user_no,
            next_invoice(),
            current_day,
            "Utility bill",
            "Expense",
            "Utilities Expense",
            sample(500:1500, 1),
            "Gcash"
        )
    }
}

cat(sprintf(
    "Seeded %d days of transactions for user_no=%d\n",
    length(all_dates),
    user_no
))
DBI::dbDisconnect(conn)
