saaaalibrary(DBI)

clamp <- function(value, lower = 0, upper = 100) {
    min(max(value, lower), upper)
}

predict_business_health <- function(
    conn,
    user_no,
    price,
    volume,
    marketing,
    raw_material,
    wages,
    utilities,
    seasonality,
    inflation,
    competition
) {
    total_debits <- get_total_debits(conn, user_no)
    total_credits <- get_total_credits(conn, user_no)

    base_revenue <- max(price, 0) * max(volume, 0)
    demand_multiplier <- max(
        0,
        1 + (seasonality / 100) - (competition / 200)
    )
    marketing_lift <- 1 + min(
        max(marketing, 0) / max(base_revenue, 1),
        0.25
    )
    projected_revenue <- base_revenue * demand_multiplier * marketing_lift
    projected_cost <- (
        max(raw_material, 0) +
        max(wages, 0) +
        max(utilities, 0)
    ) * (1 + max(inflation, 0) / 100) + max(marketing, 0)
    projected_profit <- projected_revenue - projected_cost

    if (projected_revenue <= 0) {
        margin <- -1
        margin_score <- 0
    } else {
        margin <- projected_profit / projected_revenue
        margin_score <- clamp(((margin + 0.2) / 0.6) * 100)
    }

    historical_total <- total_debits + total_credits
    historical_score <- if (historical_total == 0) {
        50
    } else {
        total_credits / historical_total * 100
    }

    probability <- if (base_revenue == 0) {
        0
    } else {
        clamp(
            (margin_score * 0.65) +
            (historical_score * 0.35) +
            (seasonality * 0.1) -
            (inflation * 0.5) -
            (competition * 0.15)
        )
    }

    if (probability >= 75) {
        position <- "Safe zone"
        recommendation <- "Strong outlook. The projected margin can absorb the selected risks."
    } else if (probability >= 50) {
        position <- "Moderate risk"
        recommendation <- "Review pricing or reduce operating costs before proceeding."
    } else {
        position <- "High risk"
        recommendation <- "Projected costs and market pressure outweigh the expected return."
    }

    list(
        total_debits = total_debits,
        total_credits = total_credits,
        projected_revenue = round(projected_revenue, 2),
        projected_cost = round(projected_cost, 2),
        projected_profit = round(projected_profit, 2),
        profit_margin = round(margin * 100, 2),
        probability_base = round(historical_score, 2),
        probability_adjusted = round(probability, 2),
        financial_position = position,
        recommendation = recommendation
    )
}
