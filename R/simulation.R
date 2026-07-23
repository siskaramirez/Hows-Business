library(DBI)

# -----------------------------------------
# Predict Business Health
# -----------------------------------------
predict_business_health <- function(conn, user_no, seasonality, inflation, competition) {

    # -----------------------------------------
    # Retrieve Financial Data
    # -----------------------------------------
    total_debits <- get_total_debits(conn, user_no)
    total_credits <- get_total_credits(conn, user_no)

    # -----------------------------------------
    # Step 1
    # Base Probability Score
    # -----------------------------------------
    if ((total_debits + total_credits) == 0) {
        p_base <- 0
    } else {
        p_base <- (total_debits / (total_debits + total_credits)) * 100
    }

    # -----------------------------------------
    # Step 2
    # External Adjustment Multiplier
    # -----------------------------------------
    lambda <-
        (1 + ((seasonality - 50) / 200)) *
        (1 - (inflation / 300)) *
        (1 - (competition / 300))

    # -----------------------------------------
    # Step 3
    # Adjusted Probability
    # -----------------------------------------
    p_adj <- min(p_base * lambda, 100)

    # -----------------------------------------
    # Step 4
    # Interpretation
    # -----------------------------------------
    if (p_adj >= 80) {
        position <- "High debit dominance"

        recommendation <-
        "Proceed — implement the simulated budget plan"

    } else if (p_adj >= 60) {
        position <- "Moderate debit dominance"

        recommendation <-
        "Proceed with caution — monitor COGS and expense lines"

    } else if (p_adj >= 50) {
        position <- "Near-balanced position"

        recommendation <-
        "Review — identify and trim specific cost drivers"

    } else {
        position <- "Credit dominance (High Risk)"

        recommendation <-
        "Do not proceed — restructure the simulation parameters"
    }

    # -----------------------------------------
    # Return Results
    # -----------------------------------------
    return(list(
        total_debits = total_debits,
        total_credits = total_credits,
        probability_base = round(p_base, 2),
        adjustment_multiplier = round(lambda, 4),
        probability_adjusted = round(p_adj, 2),
        financial_position = position,
        recommendation = recommendation
    ))

}