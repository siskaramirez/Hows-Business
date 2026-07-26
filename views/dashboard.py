import flet as ft
import flet_charts as fch
import requests
from datetime import datetime
from components.insights import business_insights_section

API_URL = "http://127.0.0.1:8000"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def fetch_income_statement(user_no: int, month_name: str):
    try:
        resp = requests.post(
            f"{API_URL}/reports",
            json={"report_type": "income_statement", "month": month_name, "user_no": user_no},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("error") or data.get("message"):
            return None
        return data
    
    except Exception:
        return None

def compute_trend(current, previous):
    if current is None:
        return "No data", "#8a94ad"
    if previous in (None, 0):
        return "No prior data", "#8a94ad"
    pct = ((current - previous) / previous) * 100
    color = "#4ADE80" if pct >= 0 else "#F87171"
    return f"{abs(pct):.1f}% vs last month", color
    

def dashboard(page: ft.Page):
    current_user = page.session.store.get("user")
    user_no = current_user.get("user_no") if current_user else None

    now = datetime.now()
    forecast_points = []
    historical_points = []
    forecast_error = None
    trend_summary = None
    overall_direction = None
    anomalies = []

    if user_no:
        try:
            resp = requests.get(f"{API_URL}/forecast", params={"user_no": user_no, "periods": 6}, timeout=60)
            data = resp.json()
             
            if resp.status_code == 200 and not data.get("error"):
                forecast_points = data.get("points", [])
                historical_points = data.get("historical", [])
                trend_summary = data.get("trend_summary")
                overall_direction = data.get("overall_direction")
                anomalies = data.get("anomalies", [])
            else:
                forecast_error = (data.get("detail") or data.get("error") or "Failed to load forecast")
        except Exception as exc:
            forecast_error = "Server unavailable"
    else:
        forecast_error = "Session expired."

    selected_month = now.month
    metrics = {}

    def cogs_ratio(report):
        if not report:
            return None
        revenue = float(report.get("total_revenue", 0) or 0)
        if revenue <= 0:
            return None
        cogs_total = sum(
            float(item.get("Amount", 0) or 0)
            for item in report.get("expense_details", [])
            if any(
                term in str(item.get("Account", "")).lower()
                for term in ("cost of goods", "cogs", "raw material")
            )
        )
        return cogs_total / revenue * 100

    def model_value_for_month(month_index):
        month_key = f"{now.year}-{month_index:02d}"
        for point in historical_points:
            if point["ds"].startswith(month_key):
                return float(point.get("forecast", point["actual"])), "Model estimate"
        for point in forecast_points:
            if point["ds"].startswith(month_key):
                detail = f"{point['trend_pct_change']:+.1f}% ({point['confidence']})"
                return float(point["yhat"]), detail
        return None, "No forecast"

    def load_month_metrics(month_index):
        month_name = MONTHS[month_index - 1]
        previous_index = month_index - 1
        current_report = fetch_income_statement(user_no, month_name) if user_no else None
        previous_report = (
            fetch_income_statement(user_no, MONTHS[previous_index - 1])
            if user_no and previous_index >= 1
            else None
        )

        revenue = current_report.get("total_revenue") if current_report else None
        profit = current_report.get("net_profit") if current_report else None
        previous_revenue = previous_report.get("total_revenue") if previous_report else None
        previous_profit = previous_report.get("net_profit") if previous_report else None
        current_cogs = cogs_ratio(current_report)
        previous_cogs = cogs_ratio(previous_report)
        forecast_value, forecast_detail = model_value_for_month(month_index)

        metrics.update({
            "month_name": month_name,
            "revenue": revenue,
            "profit": profit,
            "revenue_trend": compute_trend(revenue, previous_revenue),
            "profit_trend": compute_trend(profit, previous_profit),
            "forecast": forecast_value,
            "forecast_detail": forecast_detail,
            "cogs": current_cogs,
            "cogs_trend": compute_trend(current_cogs, previous_cogs),
        })

    load_month_metrics(selected_month)

    def kpi_card(title, value, trend_text, trend_color, trend_icon=None):
        if trend_icon == None:
            if trend_color == "#4ADE80":
                trend_icon = ft.Icons.KEYBOARD_ARROW_UP
            elif trend_color == "#F87171":
                trend_icon = ft.Icons.KEYBOARD_ARROW_DOWN
            else:
                trend_icon = None

        return ft.Container(
            content=ft.Column([
                ft.Text(title.upper(), size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
                ft.Row([
                    ft.Text(value, size=20, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(trend_icon, color=trend_color, size=20) if trend_icon else ft.Container(),
                    ft.Text(trend_text, size=12, color=trend_color, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            col={"xs": 12, "sm": 6, "md": 3},
            bgcolor="#1C2541",
            padding=20,
            border_radius=20,
            height=140,
        )

    def build_kpi_controls():
        revenue_trend_text, revenue_trend_color = metrics["revenue_trend"]
        profit_trend_text, profit_trend_color = metrics["profit_trend"]
        cogs_trend_text, cogs_trend_color = metrics["cogs_trend"]
        forecast_value = metrics["forecast"]
        forecast_color = "#4ADE80" if forecast_value is not None else "#8a94ad"

        return [
            kpi_card(
                "Monthly Revenue",
                f"₱ {metrics['revenue']:,.0f}" if metrics["revenue"] is not None else "N/A",
                revenue_trend_text,
                revenue_trend_color,
            ),
            kpi_card(
                "Net Profit",
                f"₱ {metrics['profit']:,.0f}" if metrics["profit"] is not None else "N/A",
                profit_trend_text,
                profit_trend_color,
            ),
            kpi_card(
                f"Forecast ({metrics['month_name']})",
                f"₱ {forecast_value:,.0f}" if forecast_value is not None else "N/A",
                metrics["forecast_detail"],
                forecast_color,
            ),
            kpi_card(
                "COGS Ratio",
                f"{metrics['cogs']:.1f}%" if metrics["cogs"] is not None else "N/A",
                cogs_trend_text if metrics["cogs"] is not None else "No COGS recorded",
                cogs_trend_color if metrics["cogs"] is not None else "#8a94ad",
            ),
        ]

    kpi_row = ft.ResponsiveRow(
        controls=build_kpi_controls(),
        run_spacing=15,
        spacing=15,
        margin=ft.Margin(left=10, top=10, right=10, bottom=0),
    )

    def on_month_change(e):
        nonlocal selected_month
        selected_month = MONTHS.index(e.control.value) + 1
        load_month_metrics(selected_month)
        kpi_row.controls = build_kpi_controls()
        kpi_row.update()

    month_dropdown = ft.Dropdown(
        value=MONTHS[selected_month - 1],
        options=[ft.dropdown.Option(month) for month in MONTHS],
        on_select=on_month_change,
        width=190,
        height=46,
        border_radius=6,
        border_color="#1C2541",
        color="#1C2541",
        text_size=13,
        label="Reporting month",
    )
    month_selector = ft.Row(
        controls=[
            ft.Text(
                f"Monthly performance · {now.year}",
                size=13,
                weight=ft.FontWeight.W_600,
                color="#1C2541",
            ),
            month_dropdown,
        ],
        alignment=ft.MainAxisAlignment.END,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def build_trend_badge():
        if not trend_summary:
            return ft.Container()
        badge_color = (
            "#4ADE80" if overall_direction == "Upward"
            else "#F87171" if overall_direction == "Downward"
            else "#8a94ad"
        )
        return ft.Container(
            content=ft.Text(trend_summary, size=12, weight=ft.FontWeight.BOLD, color=badge_color),
            bgcolor="#1C2541",
            border_radius=20,
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            margin=ft.Margin(left=12, top=8, right=0, bottom=0),
        )

    def build_anomaly_notices():
        if not anomalies:
            return ft.Container()
        return ft.Column(
            controls=[
                ft.Text(
                    f"⚠ {a['ds'][:7]}: {a['note']} (₱{a['actual']:,.0f} vs ₱{a['expected']:,.0f} expected)",
                    size=11, color="#F87171", italic=True,
                )
                for a in anomalies
            ],
            spacing=2,
            margin=ft.Margin(left=12, top=8, right=0, bottom=0),
        )

    current_filter = "6 MONTHS"

    def period_filter(text):
        is_active = current_filter == text
        
        return ft.TextButton(
            content=ft.Text(
                text,
                size=12,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                color="#1C3274" if is_active else ft.Colors.GREY_600,
                style=ft.TextStyle(
                    decoration=ft.TextDecoration.UNDERLINE if is_active else ft.TextDecoration.NONE
                )
            ),
            data=text,
            on_click=on_filter_click
        )
    
    def on_filter_click(e):
        nonlocal current_filter
        current_filter = e.control.data 
        
        period_filter_row.controls = [
            period_filter("6 MONTHS"),
            period_filter("12 MONTHS"),
            period_filter("YTD")
        ]
        
        period_filter_row.update()
        chart_slot.content = build_forecast_chart()
        chart_slot.update()
        
    period_filter_row = ft.Row(
        controls=[
            period_filter("6 MONTHS"),
            period_filter("12 MONTHS"),
            period_filter("YTD")
        ],
        spacing=10
    )

    def build_forecast_chart():
        if forecast_error:
            return ft.Container(
                content=ft.Text(forecast_error, size=12, italic=True, color=ft.Colors.BLUE_GREY_300),
                alignment=ft.Alignment.CENTER, height=250,
            )
        
        if not forecast_points and not historical_points:
            return ft.Container(
                content=ft.Text("Not enough historical data for a forecast.", size=12, italic=True, color=ft.Colors.BLUE_GREY_300),
                alignment=ft.Alignment.CENTER, height=250,
            )

        if current_filter == "6 MONTHS":
            visible_history = historical_points[-6:]
        elif current_filter == "12 MONTHS":
            visible_history = historical_points[-12:]
        else:
            current_year = str(datetime.now().year)
            visible_history = [
                point for point in historical_points
                if point["ds"].startswith(current_year)
            ]

        if not visible_history:
            visible_history = historical_points

        visible_forecast = forecast_points[:1]
        visible_points = visible_history + visible_forecast
        all_labels = [
            datetime.strptime(point["ds"], "%Y-%m-%d").strftime("%b")
            for point in visible_points
        ]

        historical_data_points = [
            fch.LineChartDataPoint(x=i, y=float(h["actual"]))
            for i, h in enumerate(visible_history)
        ]

        fitted_data_points = [
            fch.LineChartDataPoint(x=i, y=float(h["forecast"]))
            for i, h in enumerate(visible_history)
            if h.get("forecast") is not None
        ]
        forecast_data_points = fitted_data_points + [
            fch.LineChartDataPoint(
                x=len(visible_history) + i,
                y=float(point["yhat"]),
            )
            for i, point in enumerate(visible_forecast)
        ]

        actual_line = fch.LineChartData(
            points=historical_data_points,
            stroke_width=2,
            color="#1C2541",
            curved=True,
        )

        forecast_line = fch.LineChartData(
            points=forecast_data_points,
            stroke_width=2,
            color="#7ee08a",
            dash_pattern=[6, 4],
            curved=True,
        )

        label_step = max(1, len(all_labels) // 8)
        bottom_labels = [
            fch.ChartAxisLabel(value=i, label=ft.Text(label, size=10))
            for i, label in enumerate(all_labels)
            if i % label_step == 0
        ]

        return fch.LineChart(
            data_series=[actual_line, forecast_line],
            height=250,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            left_axis=fch.ChartAxis(label_size=40),
            bottom_axis=fch.ChartAxis(labels=bottom_labels),
            expand=True,
            interactive=True,
        )

    chart_slot = ft.Container(content=build_forecast_chart(), expand=True)

    graph_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("MONTHLY SALES", size=16, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
                    ft.Container(height=5),
                    ft.Text("ACTUAL VS ML FORECAST", size=13, weight=ft.FontWeight.W_600, margin=ft.Margin(left=12, top=0, right=0, bottom=0)),
                ], spacing=2),
                
                ft.Row([
                    ft.Row([
                        ft.Container(width=37, height=2, bgcolor="#1C2541"), 
                        ft.Text("ACTUAL", size=11, color="#1C2541", weight=ft.FontWeight.BOLD)
                    ], spacing=6),
                    ft.Container(width=15),
                    ft.Row([
                        ft.Text("————", color="#4ADE80", size=13, weight=ft.FontWeight.BOLD), 
                        ft.Text("FORECAST", size=11, color="#1C2541", weight=ft.FontWeight.BOLD)
                    ], spacing=6),
                ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Container(height=8),
            ft.Row(
                [
                    period_filter_row,
                    build_trend_badge(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            
            chart_slot,
            build_anomaly_notices(),
        ]),
        bgcolor=ft.Colors.WHITE,
        padding=20,
        border_radius=20,
        margin=ft.Margin.all(10),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 0))
    )

    return ft.Container(
        content=ft.Column([
            month_selector,
            kpi_row,
            graph_card,
            business_insights_section(page, user_no),
        ], spacing=18, scroll=ft.ScrollMode.AUTO),
        expand=True
    )
