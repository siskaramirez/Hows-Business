import flet as ft
from components.auth import auth_card

def forgot(page: ft.Page, on_back_callback):
    email_input = ft.TextField(
        hint_text="juandelacruz@gmail.com",
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
        width=320,
    )

    content_area = ft.Column(spacing=5, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def open_inbox():
        content_area.controls = [
            auth_card(page, on_back_click=lambda _: page.navigate("/login"), show_logo=True),
            ft.Container(height=10),
            
            ft.Icon(ft.Icons.MARK_EMAIL_READ_OUTLINED, color="#1C2541", size=63),
            ft.Container(height=10),
            
            ft.Text("Check your email!", size=24, weight=ft.FontWeight.BOLD, color="#1C2541", text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Text(
                "We have sent a secure password reset link to\nyour registered email address.",
                size=12,
                color="#1C2541",
                text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.W_400
            ),
            ft.Container(height=20),
            
            ft.Container(
                content=ft.Text("OPEN EMAIL INBOX", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=13),
                bgcolor="#1C2541",
                border_radius=5,
                width=320,
                height=45,
                alignment=ft.Alignment.CENTER,
                on_click=lambda _: page.launch_url_async("https://mail.google.com")
            )
        ]
        content_area.update()

    def handle_send():
        content_area.controls = [
            auth_card(page, on_back_click=lambda _: page.navigate("/login"), show_logo=True),
            ft.Container(height=10),
            
            ft.Text("Forgot your password?", size=24, weight=ft.FontWeight.BOLD, color="#1C2541", text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Text(
                "Enter your email and we'll send you a link to\nreset your password.",
                size=12,
                color="#1C2541",
                text_align=ft.TextAlign.CENTER,
                weight=ft.FontWeight.W_400
            ),
            ft.Container(height=20),
            
            ft.Row([
                ft.Text("Email address", size=12, color="#1C2541", weight=ft.FontWeight.W_500)
            ], alignment=ft.MainAxisAlignment.START, width=320),
            
            ft.Container(height=2),
            
            email_input,
            ft.Container(height=20),

            ft.Container(
                content=ft.Text("SEND EMAIL", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=13),
                bgcolor="#1C2541",
                border_radius=5,
                width=320,
                height=45,
                alignment=ft.Alignment.CENTER,
                on_click=lambda _: open_inbox()
            )
        ]

    handle_send()

    return ft.Container(
        content=ft.Container(
            content=content_area,
            bgcolor=ft.Colors.WHITE,
            border_radius=30,
            width=420,
            padding=30,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True
    )