import flet as ft

def welcome(page: ft.Page, on_back_callback):
    btn_text = ft.Text(
        "CONTINUE", 
        size=17,
        color=ft.Colors.WHITE, 
        weight=ft.FontWeight.BOLD, 
        style=ft.TextStyle(letter_spacing=1.5)
    )

    def on_btn_hover(e):
        is_hovering = str(e.data).lower() == "true"
        e.control.bgcolor = ft.Colors.WHITE if is_hovering else ft.Colors.with_opacity(0.001, ft.Colors.WHITE)
        btn_text.color = "#1C2541" if is_hovering else ft.Colors.WHITE
        
        page.update()
    
    continue_btn = ft.Container(
        content=btn_text,
        bgcolor=ft.Colors.TRANSPARENT,
        border=ft.Border.all(1.5, ft.Colors.WHITE),
        border_radius=25,
        width=220,
        height=50,
        alignment=ft.Alignment.CENTER,
        on_hover=on_btn_hover,
        on_click=lambda _: page.navigate("/create-pin"),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.QUESTION_ANSWER_ROUNDED, color="#4EA8DE", size=100),
                ft.Container(height=15),
                
                ft.Text("THANK YOU FOR TRUSTING US,", color=ft.Colors.WHITE, size=22, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                ft.Text("USER!", color=ft.Colors.WHITE, size=42, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Lets have a prosperous business!", color="#E2E8F0", size=17, italic=True, text_align=ft.TextAlign.CENTER),
                
                ft.Container(height=30),
                continue_btn,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )