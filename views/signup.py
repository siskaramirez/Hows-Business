import flet as ft
from components.auth import auth_card

def signup(page: ft.Page, on_back_callback):
    email_input = ft.TextField(
        hint_text="abc@gmail.com",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=205,
        height=45,
    )

    contact_input = ft.TextField(
        hint_text="09123456789",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=205,
        height=45,
    )

    first_name_input = ft.TextField(
        hint_text="First Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=133,
        height=45,
    )

    middle_name_input = ft.TextField(
        hint_text="Middle Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=133,
        height=45,
    )

    last_name_input = ft.TextField(
        hint_text="Last Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=133,
        height=45,
    )

    password_input = ft.TextField(
        hint_text="Password",
        password=True,
        can_reveal_password=True,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=205,
        height=45,
    )

    confirm_password_input = ft.TextField(
        hint_text="Confirm Password",
        password=True,
        can_reveal_password=True,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        width=205,
        height=45,
    )

    terms_checkbox = ft.Row(
        controls=[
            ft.Checkbox(value=False, fill_color="#1C2541", margin=ft.Margin(0, 0, 0, 0)),
            ft.Text(
                spans=[
                    ft.TextSpan("BY SIGNING UP, YOU ACCEPT OUR ", style=ft.TextStyle(color="#1C2541", size=10, weight=ft.FontWeight.W_500)),
                    ft.TextSpan("TERMS OF CONDITION", style=ft.TextStyle(color="#1C2541", size=10, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.UNDERLINE)),
                    ft.TextSpan(" & ", style=ft.TextStyle(color="#1C2541", size=10, weight=ft.FontWeight.W_500)),
                    ft.TextSpan("PRIVACY POLICY", style=ft.TextStyle(color="#1C2541", size=10, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.UNDERLINE)),
                ]
            )
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=2,
        width=420
    )

    create_account_btn = ft.Container(
        content=ft.Text("CREATE ACCOUNT", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
        bgcolor="#1C2541",
        border_radius=5,
        width=420,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: on_back_callback("LOGIN", "/login", "login")
    )

    login_link = ft.Row(
        controls=[
            ft.Text("Already a member?", size=14, color="#1C2541"),
            ft.TextButton(
                content=ft.Text("LOGIN HERE!", size=17, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)),
                style=ft.ButtonStyle(padding=0),
                on_click=lambda _: on_back_callback("LOGIN", "/login", "login")
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
        width=420
    )

    return ft.Container(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    auth_card(page, on_back_click=lambda _: on_back_callback("LOGIN", "/login", "login"), show_logo=True),
                    ft.Container(height=13),
                    
                    ft.Text("Sign Up", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Container(height=2, bgcolor="#1C2541", width=420, margin=ft.Margin(0, 0, 0, 15)),
                    
                    ft.Row([
                        ft.Column([ft.Text("Email address", size=14, color="#1C2541", weight=ft.FontWeight.W_500), email_input], spacing=5),
                        ft.Column([ft.Text("Contact number", size=14, color="#1C2541", weight=ft.FontWeight.W_500), contact_input], spacing=5),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=5),
                    
                    ft.Row([
                        ft.Column([ft.Text("First Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), first_name_input], spacing=5),
                        ft.Column([ft.Text("Middle Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), middle_name_input], spacing=5),
                        ft.Column([ft.Text("Last Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), last_name_input], spacing=5),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=5),
                    
                    ft.Row([
                        ft.Column([ft.Text("Create password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), password_input], spacing=5),
                        ft.Column([ft.Text("Confirm password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), confirm_password_input], spacing=5),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=5),
                    
                    terms_checkbox,
                    ft.Container(height=5),
                    
                    ft.Row([create_account_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=18),
                    
                    login_link
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=7,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=30,
            width=490,
            padding=30,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True
    )