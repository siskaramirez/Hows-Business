import flet as ft
import flet_charts as fch
import requests
from datetime import datetime

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
    current_month_name = MONTHS[now.month - 1]
    previous_month_name = MONTHS[(now.month - 2) % 12]

    monthly_revenue = None
    net_profit = None
    revenue_trend_text, revenue_trend_color = "No Data", "#8a94ad"
    profit_trend_text, profit_trend_color = "No Data", "#8a94ad"
    
    if user_no:
        current_data = fetch_income_statement(user_no, current_month_name)
        previous_data = fetch_income_statement(user_no, previous_month_name)

        if current_data:
            monthly_revenue = current_data.get("total_revenue", 0)
            net_profit = current_data.get("net_profit", 0)

        previous_revenue = previous_data.get("total_revenue") if previous_data else None
        previous_profit = previous_data.get("net_profit") if previous_data else None

        revenue_trend_text, revenue_trend_color = compute_trend(monthly_revenue, previous_revenue)
        profit_trend_text, profit_trend_color = compute_trend(net_profit, previous_profit)

    forecast_points = []
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

    if forecast_points:
        target_date = datetime.strptime(forecast_points[0]["ds"], "%Y-%m-%d")
        forecast_title = f"Forecast ({target_date.strftime('%B %Y')})"
        
        forecast_next_value = f"₱ {forecast_points[0]['yhat']:,.0f}"
        forecast_trend_text = f"{forecast_points[0]['trend_pct_change']:+.1f}% ({forecast_points[0]['confidence']})"
        
        trend_dir = forecast_points[0].get("trend_direction")
        forecast_trend_color = "#4ADE80" if trend_dir == "up" else "#F87171" if trend_dir == "down" else "#9CA3AF"
    else:
        forecast_title = "Forecast"
        forecast_next_value = "N/A" if forecast_error else "₱0.00"
        forecast_trend_text = "N/A" if forecast_error else "No Data"
        forecast_trend_color = "#8a94ad"
    
    kpi_row = ft.ResponsiveRow(
        controls=[
            kpi_card(
                "Monthly Revenue",
                f"₱ {monthly_revenue:,.0f}" if monthly_revenue is not None else "N/A",
                revenue_trend_text,
                revenue_trend_color,
            ),
            
            kpi_card(
                "Net Profit",
                f"₱ {net_profit:,.0f}" if net_profit is not None else "N/A",
                profit_trend_text,
                profit_trend_color,
            ),

            kpi_card(
                forecast_title,
                forecast_next_value,
                forecast_trend_text,
                forecast_trend_color,
            ),
            kpi_card("COGS Ratio", "0%", "slightly high", "#F87171"),
        ],
        run_spacing=15,
        spacing=15,
        margin=ft.Margin(left=10, top=10, right=10, bottom=0),
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
        
        # (Optional) Place your backend trigger here:
        # load_backend_data(current_filter)
        
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

        all_labels = [h["ds"][:7] for h in historical_points] + [f["ds"][:7] for f in forecast_points]

        historical_data_points = [
            fch.LineChartDataPoint(x=i, y=float(h["actual"]))
            for i, h in enumerate(historical_points)
        ]

        forecast_start_index = len(historical_points)
        forecast_data_points = [
            fch.LineChartDataPoint(x=forecast_start_index + i, y=float(f["yhat"]))
            for i, f in enumerate(forecast_points)
        ]

        if historical_data_points:
            forecast_data_points = [
                fch.LineChartDataPoint(x=forecast_start_index - 1, y=float(historical_points[-1]["actual"]))
            ] + forecast_data_points

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
            
            build_forecast_chart(),
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
            kpi_row,
            graph_card
        ], spacing=18, scroll=ft.ScrollMode.AUTO),
        expand=True
    )