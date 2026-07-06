import flet as ft
from components.navbar import navbar
from views.home import home
from views.features import features
from views.login import login
from views.signup import signup


def main(page: ft.Page):
    page.title = "How's Business - Management System"
    page.padding = 30
    page.bgcolor = "#0B132B" 
    page.window_width = 900
    page.window_height = 600
    page.scroll = ft.ScrollMode.AUTO
    
    if not hasattr(page, "current_tab"):
        page.current_tab = "HOME"

    def route_change(target_tab: str, route: str, key: str):
        page.current_tab = target_tab
        page.clean()
        
        if page.current_tab == "LOGIN":
            page.add(login(page, on_back_callback=route_change))
            return

        elif page.current_tab == "SIGNUP":
            page.add(signup(page, on_back_callback=route_change))
            return
        
        elif page.current_tab == "FORGOT":
            page.add(login(page, on_back_callback=route_change))
            return

        active_content = home(page) if page.current_tab == "HOME" else features(page)
        
        page.add(
            ft.Column(
                controls=[
                    navbar(page, on_navigate_callback=route_change),
                    active_content
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                expand=True
            )
        )

    route_change(page.current_tab, "/", "home")

ft.run(main)