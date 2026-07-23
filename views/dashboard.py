import flet as ft
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

def dashboard(page: ft.Page):
    current_user = page.session.store.get("user")
    user_no = current_user.get("user_no") if current_user else None

    forecast_points = []
    forecast_error = None

    if user_no:
        try:
            resp = requests.get(f"{API_URL}/forecast", params={"user_no": user_no, "periods": 6}, timeout=60)
            
            data = resp.json()
            
            if resp.status_code == 200 and not data.get("error"):
                forecast_points = data.get("forecast", [])
            else:
                forecast_error = (
                    data.get("detail") or data.get("error") or "Failed to load forecast"
                )

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
                ft.Text(title.upper(), size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
                ft.Row([
                    ft.Text(value, size=25, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(trend_icon, color=trend_color, size=20) if trend_icon else ft.Container(),
                    ft.Text(trend_text, size=15, color=trend_color, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            col={"xs": 12, "sm": 6, "md": 3},
            bgcolor="#1C2541",
            padding=20,
            border_radius=20,
            height=140,
            
        )
    
    kpi_row = ft.ResponsiveRow(
        controls=[
            kpi_card("Monthly Revenue", "₱ 84,200", "6.4% vs last month", "#4ADE80"),
            kpi_card("Net Profit", "₱ 21,500", "3.1% vs last month", "#4ADE80"),
            kpi_card(
                "Forecast (Next Month)",
                f"₱ {forecast_points[0]['yhat']:,.0f}" if forecast_points else "N/A",
                "projected" if forecast_points else (forecast_error or "no data"),
                "#4ADE80",
            ),
            kpi_card("COGS Ratio", "38.2%", "slightly high", "#F87171"),
        ],
        run_spacing=15,
        spacing=15,
        margin=ft.Margin(left=10, top=10, right=10, bottom=0),
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
        if not forecast_points:
            return ft.Container(
                content=ft.Text("Not enough historical data for a forecast.", size=12, italic=True, color=ft.Colors.BLUE_GREY_300),
                alignment=ft.Alignment.CENTER, height=250,
            )

        data_points = [
            ft.LineChartDataPoint(i, point["yhat"])
            for i, point in enumerate(forecast_points)
        ]

        forecast_line = ft.LineChartData(
            data_points=data_points,
            stroke_width=2,
            color="#7ee08a",
            dash_pattern=[6, 4],
            curved=True,
        )

        return ft.LineChart(
            data_series=[forecast_line],
            height=250,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            left_axis=ft.ChartAxis(labels_size=40),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=i, label=ft.Text(point["ds"][:7], size=10))
                    for i, point in enumerate(forecast_points)
                ],
            ),
        )

    graph_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("MONTHLY SALES", size=14, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
                    ft.Container(height=5),
                    ft.Text("ACTUAL VS ML FORECAST", size=12, weight=ft.FontWeight.W_600, margin=ft.Margin(left=12, top=0, right=0, bottom=0)),
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
                ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.START)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),

            period_filter_row,
            
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            
            build_forecast_chart(),
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