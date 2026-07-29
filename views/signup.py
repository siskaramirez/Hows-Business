import flet as ft
import requests
from components.auth import auth_card

API_URL = "http://127.0.0.1:8000"

def signup(page: ft.Page, on_back_callback):
    email_input = ft.TextField(
        hint_text="abc@gmail.com",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    contact_input = ft.TextField(
        hint_text="09123456789",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    first_name_input = ft.TextField(
        hint_text="First Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    middle_name_input = ft.TextField(
        hint_text="Middle Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
        height=45,
    )

    last_name_input = ft.TextField(
        hint_text="Last Name",
        bgcolor="#D9D9D9",
        border_radius=10,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color="#1C2541",
        color="#1C2541",
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
        height=45,
    )

    terms_checkbox = ft.Checkbox(
        value=False,
        fill_color="#1C2541",
        margin=ft.Margin(0, 0, 0, 0),
    )

    def show_message(message, error=True):
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else "#2E7D32",
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def handle_signup(_):
        required = (
            email_input.value,
            contact_input.value,
            first_name_input.value,
            last_name_input.value,
            password_input.value,
            confirm_password_input.value,
        )
        if not all(value and value.strip() for value in required):
            show_message("Please complete all required fields.")
            return
        if password_input.value != confirm_password_input.value:
            show_message("Passwords do not match.")
            return
        if len(password_input.value) < 8:
            show_message("Password must be at least 8 characters.")
            return
        if not terms_checkbox.value:
            show_message("Please accept the terms and privacy policy.")
            return

        payload = {
            "email": email_input.value.strip(),
            "contact_number": contact_input.value.strip(),
            "first_name": first_name_input.value.strip(),
            "middle_name": (middle_name_input.value or "").strip() or None,
            "last_name": last_name_input.value.strip(),
            "password": password_input.value,
        }
        try:
            response = requests.post(f"{API_URL}/signup", json=payload, timeout=30)
            data = response.json()
            if response.status_code == 201:
                page.session.store.set("user", data["user"])
                show_message("Account created successfully.", error=False)
                page.navigate("/welcome")
                return
            if response.status_code == 404:
                show_message(
                    "The running backend is outdated. Restart How's Business and try again."
                )
                return
            show_message(data.get("detail", "Unable to create account."))
        except (requests.RequestException, ValueError):
            show_message("Unable to reach the signup service. Please try again.")

    create_account_btn = ft.Container(
        content=ft.Text("CREATE ACCOUNT", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=14),
        bgcolor="#1C2541",
        border_radius=5,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=handle_signup,
    )

    login_link = ft.Row(
        controls=[
            ft.Text("Already a member?", size=14, color="#1C2541"),
            ft.TextButton(
                content=ft.Text("LOGIN HERE!", size=17, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)),
                style=ft.ButtonStyle(padding=0),
                on_click=lambda _: page.navigate("/login")
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            auth_card(page, on_back_click=lambda _: page.navigate("/login"), show_logo=True),
                            ft.Container(height=13),
                            
                            ft.Text("Sign Up", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                            ft.Container(height=2, bgcolor="#1C2541", margin=ft.Margin(0, 0, 0, 15)),
                            
                            ft.ResponsiveRow(
                                controls=[
                                    ft.Column(
                                        [ft.Text("Email address", size=14, color="#1C2541", weight=ft.FontWeight.W_500), email_input], 
                                        col={"xs": 12, "sm": 6}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Contact number", size=14, color="#1C2541", weight=ft.FontWeight.W_500), contact_input], 
                                        col={"xs": 12, "sm": 6}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),
                                    
                                    ft.Column(
                                        [ft.Text("First Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), first_name_input], 
                                        col={"xs": 12, "sm": 4}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Middle Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), middle_name_input], 
                                        col={"xs": 12, "sm": 4}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Last Name", size=14, color="#1C2541", weight=ft.FontWeight.W_500), last_name_input], 
                                        col={"xs": 12, "sm": 4}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Create password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), password_input], 
                                        col={"xs": 12, "sm": 6}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),

                                    ft.Column(
                                        [ft.Text("Confirm password", size=14, color="#1C2541", weight=ft.FontWeight.W_500), confirm_password_input], 
                                        col={"xs": 12, "sm": 6}, 
                                        spacing=3,
                                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    ),
                                ],
                                run_spacing=10,
                            ),
                            
                            ft.Container(height=10),

                            ft.Row(
                                controls=[
                                    terms_checkbox,
                                    ft.Text(
                                        spans=[
                                            ft.TextSpan("BY SIGNING UP, YOU ACCEPT OUR ", style=ft.TextStyle(color="#1C2541", size=9, weight=ft.FontWeight.W_500)),
                                            ft.TextSpan("TERMS OF CONDITION", style=ft.TextStyle(color="#1C2541", size=9, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.UNDERLINE)),
                                            ft.TextSpan(" & ", style=ft.TextStyle(color="#1C2541", size=9, weight=ft.FontWeight.W_500)),
                                            ft.TextSpan("PRIVACY POLICY", style=ft.TextStyle(color="#1C2541", size=9, weight=ft.FontWeight.BOLD, decoration=ft.TextDecoration.UNDERLINE)),
                                        ]
                                    )
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                wrap=True
                            ),
                            ft.Container(height=10),

                            create_account_btn,
                            ft.Container(height=18),
                            
                            login_link
                        ],
                        spacing=5,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=30,
                    width=min(450, page.width - 30),
                    padding=30,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True
    )
