import flet as ft
from components.navbar import navbar
from views.home import home
from views.features import features
from views.login import login
from views.signup import signup
from views.forgot_pass import forgot

def main(page: ft.Page):
    page.title = "How's Business - Management System"
    page.bgcolor = "#0B132B"
    page.padding = 0
    
    page.current_tab = "HOME"

    def route_change(e=None):
        page.clean()
        current_route = page.route if page.route else "/home"
        
        # No Navbar Pages
        if current_route == "/login":
            page.current_tab = "LOGIN"
            page.add(login(page, on_back_callback=lambda target, r, k: page.navigate(r)))
            return
        elif current_route == "/signup":
            page.current_tab = "SIGNUP"
            page.add(signup(page, on_back_callback=lambda target, r, k: page.navigate(r)))
            return
        elif current_route == "/forgot-password":
            page.current_tab = "FORGOT"
            page.add(forgot(page, on_back_callback=lambda target, r, k: page.navigate(r)))
            return
        
        # With Top Navbar Wrapper
        elif current_route == "/home" or current_route == "/":
            page.current_tab = "HOME"
            active_content = home(page)
        elif current_route == "/features":
            page.current_tab = "FEATURES"
            active_content = features(page)
        
        # Fallback for unknown routes
        else:
            page.navigate("/home")
            return
        
        def show_navbar(target_tab, route, key):
            page.navigate(route)
        
        page.add(
            ft.Column(
                controls=[
                    navbar(page, on_navigate_callback=show_navbar),
                    active_content
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                expand=True
            )
        )
        page.update()

    def handle_resize(e):
        route_change()

    page.on_route_change = route_change
    page.on_resize = handle_resize

    if page.route == "/" or not page.route:
        page.navigate("/home")
    else:
        route_change()

ft.run(main, view=ft.AppView.WEB_BROWSER)