import flet as ft

def auth_card(page: ft.Page, on_back_click, show_logo=True):
    return ft.Row(
        controls=[
            ft.Row([
                ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, color="#4EA8DE", size=20),
                ft.Text("HOW'S BUSINESS", size=15, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(letter_spacing=1))
            ], spacing=10) if show_logo else ft.Container(),
            
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_color="#1C2541",
                icon_size=22,
                on_click=on_back_click
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )