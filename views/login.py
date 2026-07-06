import flet as ft
from components.auth import auth_card

def login(page: ft.Page, on_back_callback):
    email_input = ft.TextField(
        hint_text="juandelacruz@gmail.com",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=340,
        height=45,
    )

    password_input = ft.TextField(
        hint_text="Password",
        prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
        password=True,
        can_reveal_password=True,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=340,
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
        on_click=lambda _: on_back_callback("FORGOT", "/forgot", "forgot")
    )

    login_btn = ft.Container(
        content=ft.Text("LOG IN", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=15),
        bgcolor="#1C2541",
        border_radius=5,
        width=340,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: on_back_callback("DASHBOARD", "/dashboard", "dashboard")
    )

    signup_btn = ft.TextButton(
        content=ft.Text(
            "SIGN UP", 
            size=17, 
            weight=ft.FontWeight.BOLD, 
            color="#1C2541", 
            style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)
        ),
        on_click=lambda _: on_back_callback("SIGNUP", "/signup", "signup")
    )

    return ft.Container(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    auth_card(page, on_back_click=lambda _: on_back_callback("HOME", "/", "home"), show_logo=True),
                    ft.Container(height=13),
                    
                    ft.Text("Login", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Container(height=2, bgcolor="#1C2541", width=340, margin=ft.Margin(0, 0, 0, 15)),
                    
                    ft.Text("Email address", size=14, color="#1C2541", weight=ft.FontWeight.W_500), email_input,
                    ft.Container(height=10),
                    
                    ft.Text("Password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), password_input,
                    
                    ft.Row([forgot_password_btn], alignment=ft.MainAxisAlignment.END),
                    ft.Container(height=10),
                    
                    ft.Row([login_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                    
                    ft.Row([
                        ft.Container(height=1, bgcolor="#CBD5E1", expand=True),
                        ft.Text("  or  ", size=14, color="#64748B"),
                        ft.Container(height=1, bgcolor="#CBD5E1", expand=True),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=10),
                    
                    ft.Row([signup_btn], alignment=ft.MainAxisAlignment.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=7
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=30,
            width=400,
            padding=30,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True
    )