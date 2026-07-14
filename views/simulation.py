import flet as ft

def simulation(page: ft.Page):
    return ft.Container(
        content=ft.Text(
            "This is the simulation panel.", 
            size=18, 
            weight=ft.FontWeight.BOLD,
            color="#1C2541"
        ),
        alignment=ft.Alignment.CENTER,
        expand=True
    )