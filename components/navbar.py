import flet as ft

def navbar(page: ft.Page, on_navigate_callback):
    is_mobile = page.width is not None and page.width < 700
    
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
        
    if is_mobile:
        menu_content = ft.PopupMenuButton(
            icon=ft.Icons.MENU_ROUNDED,
            icon_color="#1C2541",
            items=[
                ft.PopupMenuItem(
                    content=ft.Text("HOME", color="#1C2541", weight=ft.FontWeight.BOLD if page.current_tab == "HOME" else ft.FontWeight.NORMAL),
                    icon=ft.Icons.HOME_ROUNDED,
                    on_click=lambda _: on_navigate_callback("HOME", "/home", "home")
                ),

                ft.PopupMenuItem(
                    content=ft.Text("FEATURES", color="#1C2541", weight=ft.FontWeight.BOLD if page.current_tab == "FEATURES" else ft.FontWeight.NORMAL),
                    icon=ft.Icons.LAYERS_ROUNDED,
                    on_click=lambda _: on_navigate_callback("FEATURES", "/features", "features")
                ),
                
                ft.PopupMenuItem(
                    content=ft.Text("LOGIN", color="#1C2541", weight=ft.FontWeight.BOLD if page.current_tab == "LOGIN" else ft.FontWeight.NORMAL),
                    icon=ft.Icons.LOGIN_ROUNDED,
                    on_click=lambda _: on_navigate_callback("LOGIN", "/login", "login")
                ),
            ]
        )
    else:
        menu_content = ft.Row(
            controls=[
                nav_item("HOME", "/home", "home"),
                nav_item("FEATURES", "/features", "features"),
                ft.OutlinedButton(
                    content=ft.Text("LOGIN", size=13, color="#1C2541"),
                    style=ft.ButtonStyle(
                        side=ft.BorderSide(1, "#1C2541"),
                    ),
                    on_click=lambda _: on_navigate_callback("LOGIN", "/login", "login")
                )
            ],
            spacing=15,
        )

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, color="#4EA8DE", size=24),
                    ft.Text("HOW'S BUSINESS", size=18, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(letter_spacing=1.5))
                ], spacing=10),

                menu_content
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=30,
        padding=ft.Padding(left=20 if is_mobile else 25, top=12, right=20 if is_mobile else 25, bottom=12),
        margin=ft.Margin(left=15 if is_mobile else 40, top=15 if is_mobile else 30, right=15 if is_mobile else 40, bottom=0)
    )