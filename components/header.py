import flet as ft

def header(active_route: str):
    header_configs = {
        "/dashboard": {
            "title": "DASHBOARD",
            "subtitle": "May 2026 — Sales Overview & ML Forecast"
        },
        "/records": {
            "title": "ADD RECORDS",
            "subtitle": "Upload files or enter manually"
        },
        "/statements": {
            "title": "FINANCIAL STATEMENTS",
            "subtitle": "Automated statements & BIR-compliant exports"
        },
        "/simulation": {
            "title": "SIMULATION",
            "subtitle": "Adjust parameters to model business outcomes"
        },
        "/settings": {
            "title": "SETTINGS & ACTIVITY LOG",
            "subtitle": "Manage your profile and audit trail"
        }
    }

    if active_route not in header_configs:
        return None
    
    config = header_configs[active_route]

    return ft.Container(
        content=ft.Row([
            ft.Column([
                ft.Text(config["title"], size=24, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(letter_spacing=1.1)),
                ft.Text(config["subtitle"], size=14, color=ft.Colors.BLUE_GREY_400) if config["subtitle"] else ft.Container(height=0),
            ], spacing=2),
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color="#1C2541", bgcolor="#F4F6F9")
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        margin=ft.Margin(left=0, top=0, right=0, bottom=15),
    )