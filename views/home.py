import flet as ft

def home(page: ft.Page):
    hero_title = ft.Text(
        value="Your Roadmap to",
        size=48,
        weight=ft.FontWeight.BOLD,
        color="#a8c5f0",
        text_align=ft.TextAlign.CENTER,
    )

    hero_subtitle = ft.Text(
        value="Digital Mastery & Financial Stability",
        size=48,
        weight=ft.FontWeight.BOLD,
        color="#7ee08a",
        text_align=ft.TextAlign.CENTER,
    )

    hero_description = ft.Text(
        value="Login to Automate your Books of Accounts, Predict Future\nSales, and Navigate Inflationary Stocks in Risk-Free,\nVisual Testing Environment",
        size=20,
        color="white",
        text_align=ft.TextAlign.CENTER,
        style=ft.TextStyle(height=1.5),
    )

    learn_more_btn = ft.Container(
        content=ft.Text("LEARN MORE", color="#1C2541", weight=ft.FontWeight.BOLD, size=15),
        bgcolor=ft.Colors.WHITE,
        padding=ft.Padding(left=30, top=12, right=30, bottom=12),
        border_radius=5,
        margin=ft.Margin(left=0, top=25, right=0, bottom=0),
        alignment=ft.Alignment.CENTER,
        width=160,
        on_click=lambda _: page.navigate("/features"),
    )

    return ft.Container(
        content=ft.Column(
            controls=[hero_title, ft.Container(height=10), hero_subtitle, ft.Container(height=35),
                      hero_description, ft.Container(height=22), learn_more_btn],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=ft.Padding(left=40, top=70, right=40, bottom=70),
    )