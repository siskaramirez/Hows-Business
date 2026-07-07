import flet as ft
from components.auth import auth_card

def login(page: ft.Page, on_back_callback):
    email_input = ft.TextField(
        hint_text="Enter your email address",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    password_input = ft.TextField(
        hint_text="Enter your password",
        prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
        password=True,
        can_reveal_password=True,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    forgot_password_btn = ft.TextButton(
        content=ft.Text(
            "Forgot Password?", 
            size=10, 
            color="#1C2541", 
            style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)
        ),
        style=ft.ButtonStyle(padding=0),
        on_click=lambda _: page.navigate("/forgot-password"),
    )

    login_btn = ft.Container(
        content=ft.Text("LOG IN", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=15),
        bgcolor="#1C2541",
        border_radius=5,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: page.navigate("/dashboard"),
    )

    signup_btn = ft.TextButton(
        content=ft.Text(
            "SIGN UP", 
            size=17, 
            weight=ft.FontWeight.BOLD, 
            color="#1C2541", 
            style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)
        ),
        on_click=lambda _: page.navigate("/signup")
    )
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            auth_card(page, on_back_click=lambda _: page.navigate("/home"), show_logo=True),
                            ft.Container(height=13),
                            
                            ft.Text("Login", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                            ft.Container(height=2, bgcolor="#1C2541", width=340, margin=ft.Margin(0, 0, 0, 15)),
                            
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Column(
                                        [ft.Text("Email address", size=14, color="#1C2541", weight=ft.FontWeight.W_500), email_input], 
                                        col={"xs": 12}, 
                                        spacing=5,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), password_input], 
                                        col={"xs": 12}, 
                                        spacing=5,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),
                                ],
                                run_spacing=10,
                            ),

                            ft.Row([forgot_password_btn], alignment=ft.MainAxisAlignment.END),
                            ft.Container(height=10),
                            
                            login_btn,
                            ft.Container(height=20),
                            
                            ft.Row([
                                ft.Container(height=1, bgcolor="#CBD5E1", expand=True),
                                ft.Text("  or  ", size=14, color="#64748B"),
                                ft.Container(height=1, bgcolor="#CBD5E1", expand=True),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=10),
                            
                            ft.Row([signup_btn], alignment=ft.MainAxisAlignment.CENTER)
                        ],
                        spacing=5,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=30,
                    width=min(420, page.width - 40),
                    padding=30,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )