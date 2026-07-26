empty_insight <- function(category, eyebrow, title, description, actions) {
    list(
        id = tolower(gsub("[^a-zA-Z]+", "_", category)),
        category = category,
        eyebrow = eyebrow,
        title = title,
        summary = description,
        estimate = "Add more records",
        detail_title = title,
        detail = description,
        metrics = list(),
        actions = actions,
        has_enough_data = FALSE
    )
}

money <- function(value) {
    paste0("PHP ", format(round(value), big.mark = ",", scientific = FALSE, trim = TRUE))
}

metric <- function(value, label) {
    list(value = value, label = label)
}

month_label <- function(value) {
    months <- c(
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    )
    paste(months[as.integer(format(value, "%m"))], format(value, "%Y"))
}

prepare_records <- function(records) {
    if (is.null(records) || length(records) == 0 || nrow(records) == 0) {
        return(data.frame())
    }

    records$transaction_date <- as.Date(records$transaction_date)
    records$amount <- suppressWarnings(as.numeric(records$amount))
    records <- records[
        !is.na(records$transaction_date) &
        !is.na(records$amount) &
        records$status != "voided",
    ]
    records
}

revenue_insight <- function(records) {
    revenue <- records[records$account_name == "Revenue", ]
    actions <- c(
        "Compare weekday and weekend sales for at least four weeks.",
        "Test a weekend bundle using products that are commonly purchased together.",
        "Promote the offer before the slower days instead of discounting every day.",
        "Track daily revenue after the change to measure its effect."
    )

    if (nrow(revenue) < 4) {
        return(empty_insight(
            "Revenue", "REVENUE OPPORTUNITY",
            "Find your strongest and weakest selling days",
            "At least four revenue records across different dates are needed to compare weekday and weekend performance.",
            actions
        ))
    }

    daily <- aggregate(amount ~ transaction_date, revenue, sum)
    day_number <- as.POSIXlt(daily$transaction_date)$wday
    weekend <- daily$amount[day_number %in% c(0, 6)]
    weekday <- daily$amount[!day_number %in% c(0, 6)]

    if (length(weekend) == 0 || length(weekday) == 0) {
        return(empty_insight(
            "Revenue", "REVENUE OPPORTUNITY",
            "Compare weekend sales with weekday sales",
            "Revenue records currently cover only weekdays or only weekends. Add records for both groups to reveal the opportunity.",
            actions
        ))
    }

    weekend_avg <- mean(weekend)
    weekday_avg <- mean(weekday)
    gap_pct <- if (weekday_avg == 0) 0 else ((weekday_avg - weekend_avg) / abs(weekday_avg)) * 100
    monthly_opportunity <- max(weekday_avg - weekend_avg, 0) * 8
    direction <- if (gap_pct >= 0) "lower" else "higher"
    title <- sprintf("Weekend sales are %.0f%% %s than weekdays", abs(gap_pct), direction)

    list(
        id = "revenue_timing",
        category = "Revenue",
        eyebrow = "REVENUE OPPORTUNITY",
        title = title,
        summary = sprintf(
            "Weekend revenue averages %s per day versus %s on weekdays.",
            money(weekend_avg), money(weekday_avg)
        ),
        estimate = if (monthly_opportunity > 0) {
            paste("Est.", money(monthly_opportunity), "/mo")
        } else {
            "Weekend lead"
        },
        detail_title = title,
        detail = paste(
            "This comparison uses the average daily revenue recorded for Saturdays and Sundays",
            "against Monday through Friday."
        ),
        metrics = list(
            metric(money(weekend_avg), "Weekend avg/day"),
            metric(money(weekday_avg), "Weekday avg/day"),
            metric(sprintf("%+.0f%%", gap_pct), "Gap to close")
        ),
        actions = actions,
        has_enough_data = TRUE
    )
}

cost_control_insight <- function(records) {
    actions <- c(
        "Request volume pricing from the suppliers used most often.",
        "Compare at least two alternative suppliers for high-cost ingredients.",
        "Review portions and waste before reducing product quality.",
        "Test a small price adjustment on the best-selling products."
    )

    if (nrow(records) == 0) {
        return(empty_insight(
            "Cost Control", "COST ALERT",
            "Track cost of goods sold against revenue",
            "Revenue and COGS records are needed to calculate whether raw material cost is within a healthy range.",
            actions
        ))
    }

    latest_month <- format(max(records$transaction_date), "%Y-%m")
    current <- records[format(records$transaction_date, "%Y-%m") == latest_month, ]
    revenue_total <- sum(current$amount[current$account_name == "Revenue"])
    cogs_rows <- current$account_name == "Expense" &
        grepl("cost of goods|cogs|raw material|ingredient|inventory", current$transaction_type, ignore.case = TRUE)
    cogs_total <- sum(current$amount[cogs_rows])

    if (revenue_total <= 0 || cogs_total <= 0) {
        return(empty_insight(
            "Cost Control", "COST ALERT",
            "Track cost of goods sold against revenue",
            "The latest month needs both revenue and COGS expense records before a cost ratio can be calculated.",
            actions
        ))
    }

    ratio <- cogs_total / revenue_total * 100
    target_high <- 35
    overage <- max(cogs_total - revenue_total * target_high / 100, 0)
    title <- sprintf("Raw material cost is %.1f%% of revenue", ratio)

    list(
        id = "cogs_ratio",
        category = "Cost Control",
        eyebrow = if (ratio > target_high) "COST ALERT" else "COST CONTROL",
        title = title,
        summary = if (ratio > target_high) {
            "The COGS ratio is above the 30-35% working range. Supplier, waste, portion, or pricing changes may improve margin."
        } else {
            "The COGS ratio is within the 30-35% working range. Continue monitoring supplier prices and waste."
        },
        estimate = if (overage > 0) paste("Save", money(overage), "/mo") else "Within target",
        detail_title = title,
        detail = paste(
            "The ratio divides recorded COGS and raw material expenses by revenue",
            "for the latest month in the records."
        ),
        metrics = list(
            metric(sprintf("%.1f%%", ratio), "Current COGS ratio"),
            metric("30-35%", "Working target"),
            metric(money(overage), "Monthly overage")
        ),
        actions = actions,
        has_enough_data = TRUE
    )
}

operations_insight <- function(records) {
    actions <- c(
        "Schedule energy-intensive work outside peak operating hours where practical.",
        "Consolidate production runs to reduce repeated preheating and equipment startup.",
        "Inspect equipment seals, maintenance schedules, and unnecessary idle time.",
        "Record utility expenses every month so the trend remains visible."
    )

    months_available <- sort(unique(format(records$transaction_date, "%Y-%m")))
    if (length(months_available) == 0) {
        return(empty_insight(
            "Operations", "OPERATIONS",
            "Measure utility cost for every revenue peso",
            "Utility expense and revenue records are needed to measure operating efficiency.",
            actions
        ))
    }

    latest_month <- tail(months_available, 1)
    current <- records[format(records$transaction_date, "%Y-%m") == latest_month, ]
    current_revenue <- sum(current$amount[current$account_name == "Revenue"])
    utility_match <- current$account_name == "Expense" &
        grepl("utilit|electric|water|fuel|gas", current$transaction_type, ignore.case = TRUE)
    current_utility <- sum(current$amount[utility_match])

    if (current_revenue <= 0 || current_utility <= 0) {
        return(empty_insight(
            "Operations", "OPERATIONS",
            "Measure utility cost for every revenue peso",
            "The latest month needs both revenue and utility expense records before operating efficiency can be calculated.",
            actions
        ))
    }

    current_ratio <- current_utility / current_revenue
    previous_ratio <- NA_real_
    if (length(months_available) >= 2) {
        previous_month <- tail(months_available, 2)[1]
        previous <- records[format(records$transaction_date, "%Y-%m") == previous_month, ]
        previous_revenue <- sum(previous$amount[previous$account_name == "Revenue"])
        previous_utility_match <- previous$account_name == "Expense" &
            grepl("utilit|electric|water|fuel|gas", previous$transaction_type, ignore.case = TRUE)
        previous_utility <- sum(previous$amount[previous_utility_match])
        if (previous_revenue > 0 && previous_utility > 0) {
            previous_ratio <- previous_utility / previous_revenue
        }
    }

    change_pct <- if (is.na(previous_ratio) || previous_ratio == 0) {
        NA_real_
    } else {
        (current_ratio - previous_ratio) / previous_ratio * 100
    }
    title <- if (!is.na(change_pct) && change_pct > 5) {
        "Utility cost per revenue peso is rising"
    } else {
        "Monitor utility cost per revenue peso"
    }

    list(
        id = "utility_efficiency",
        category = "Operations",
        eyebrow = "OPERATIONS",
        title = title,
        summary = sprintf(
            "Utilities cost PHP %.3f for every PHP 1 of revenue in the latest month.",
            current_ratio
        ),
        estimate = paste("Utility spend", money(current_utility)),
        detail_title = title,
        detail = paste(
            "Utility expenses are divided by revenue for the latest month.",
            "A rising ratio means utilities are consuming more of each revenue peso."
        ),
        metrics = list(
            metric(sprintf("PHP %.3f", current_ratio), "Utility per PHP 1"),
            metric(
                if (is.na(previous_ratio)) "No baseline" else sprintf("PHP %.3f", previous_ratio),
                "Previous month"
            ),
            metric(
                if (is.na(change_pct)) "N/A" else sprintf("%+.0f%%", change_pct),
                "Ratio change"
            )
        ),
        actions = actions,
        has_enough_data = TRUE
    )
}

demand_insight <- function(records) {
    actions <- c(
        "Promote pre-orders shortly before the strongest part of the month.",
        "Use a simple reservation form to reduce last-minute order pressure.",
        "Offer clear basic, standard, and premium options for custom orders.",
        "Prepare ingredients and staff capacity before the expected demand window."
    )

    custom <- records[
        records$account_name == "Revenue" &
        grepl("service|custom|special|pre.?order", records$transaction_type, ignore.case = TRUE),
    ]
    if (nrow(custom) < 3) {
        return(empty_insight(
            "Demand", "DEMAND SIGNAL",
            "Look for recurring custom-order windows",
            "At least three service or custom-order revenue records are needed to detect month-end demand.",
            actions
        ))
    }

    day_of_month <- as.integer(format(custom$transaction_date, "%d"))
    late_total <- sum(custom$amount[day_of_month >= 20])
    total <- sum(custom$amount)
    share <- if (total == 0) 0 else late_total / total * 100
    average_order <- mean(custom$amount)
    potential <- average_order * max(round(nrow(custom) * share / 100 * 0.2), 1)
    title <- if (share >= 55) {
        "Custom orders spike near month-end"
    } else {
        "Custom-order demand is spread across the month"
    }

    list(
        id = "month_end_demand",
        category = "Demand",
        eyebrow = "DEMAND SIGNAL",
        title = title,
        summary = sprintf(
            "%.0f%% of custom-order revenue was recorded from the 20th through month-end.",
            share
        ),
        estimate = paste("Potential", money(potential), "/mo"),
        detail_title = title,
        detail = paste(
            "This signal measures the share of service and custom-order revenue",
            "recorded from the twentieth day through the end of each month."
        ),
        metrics = list(
            metric(sprintf("%.0f%%", share), "Revenue after day 20"),
            metric(money(average_order), "Average custom order"),
            metric(as.character(nrow(custom)), "Orders analyzed")
        ),
        actions = actions,
        has_enough_data = TRUE
    )
}

generate_business_insights <- function(records) {
    clean_records <- prepare_records(records)
    if (nrow(clean_records) == 0) {
        return(list(
            status = "no_data",
            period = "No transaction data",
            insights = list(
                revenue_insight(clean_records),
                cost_control_insight(clean_records),
                operations_insight(clean_records),
                demand_insight(clean_records)
            )
        ))
    }

    latest_date <- max(clean_records$transaction_date)
    list(
        status = "success",
        period = month_label(latest_date),
        insights = list(
            revenue_insight(clean_records),
            cost_control_insight(clean_records),
            operations_insight(clean_records),
            demand_insight(clean_records)
        )
    )
}
