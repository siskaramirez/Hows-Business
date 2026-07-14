library(readxl)
library(dplyr)
library(jsonlite)


# =========================
# Get uploaded file path
# =========================

args <- commandArgs(trailingOnly = TRUE)

file_path <- args[1]


# =========================
# Read Excel
# =========================

transactions <- read_excel(
  file_path,
  sheet = "Transactions"
)


# =========================
# Cleaning
# =========================

transactions <- transactions %>%
  filter(
    !is.na(Date),
    !is.na(`Account Name`),
    !is.na(Amount)
  )


# =========================
# Return JSON to FastAPI
# =========================

cat(
  toJSON(
    transactions,
    dataframe = "rows",
    pretty = TRUE
  )
)