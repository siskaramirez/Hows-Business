import flet as ft

def navbar(page: ft.Page, on_navigate_callback):
    if not hasattr(page, "current_tab"):
        page.current_tab = "HOME"

    def nav_item(text: str, route: str, key: str):
        is_active = (page.current_tab == text)
        return ft.TextButton(
            content=ft.Text(
                text, 
                size=13,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                color="#1C2541",
                style=ft.TextStyle(
                    decoration=ft.TextDecoration.UNDERLINE if is_active else ft.TextDecoration.NONE
                )
            ),
            on_click=lambda _: on_navigate_callback(text, route, key)
        )

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, color="#4EA8DE", size=24),
                    ft.Text("HOW'S BUSINESS", size=18, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(letter_spacing=1.5))
                ], spacing=10),
                
                ft.Row([
                    nav_item("HOME", "/", "home"),
                    nav_item("FEATURES", "/features", "features"),
                    ft.OutlinedButton(
                        content=ft.Text("LOGIN", size=13, color="#1C2541"),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#1C2541"),
                        ),
                        on_click=lambda _: on_navigate_callback("LOGIN", "/login", "login")
                    )
                ], spacing=15)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=30,
        padding=ft.Padding(left=25, top=12, right=25, bottom=12),
        margin=ft.Margin(left=40, top=30, right=40, bottom=0)
    )