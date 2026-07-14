import flet as ft
from components.navbar import navbar
from components.sidebar import sidebar
from components.header import header
from views.home import home
from views.features import features
from views.login import login
from views.signup import signup
from views.forgot_pass import forgot
from views.welcome import welcome
from views.pin import pin
from views.dashboard import dashboard
from views.records import records
from views.statements import statements
from views.simulation import simulation

def main(page: ft.Page):
    page.title = "How's Business - Management System"
    page.bgcolor = "#0B132B"
    page.padding = 0
    
    page.current_tab = "HOME"

    def route_change(e=None):
        page.clean()
        current_route = page.route if page.route else "/home"
        
        # No Navbar Pages
        layout_type = "navbar"

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
        elif current_route == "/welcome":
            page.current_tab = "WELCOME"
            page.add(welcome(page, on_back_callback=lambda target, r, k: page.navigate(r)))
            return
        elif current_route == "/create-pin":
            page.current_tab = "CREATE_PIN"
            page.add(pin(page, mode="create"))
            return
        elif current_route == "/verify-pin":
            page.current_tab = "VERIFY_PIN"
            page.add(pin(page, mode="verify"))
            return
        
        # With Top Navbar Wrapper
        elif current_route == "/home" or current_route == "/":
            page.current_tab = "HOME"
            active_content = home(page)
            layout_type = "navbar"
        elif current_route == "/features":
            page.current_tab = "FEATURES"
            active_content = features(page)
            layout_type = "navbar"

        # With Sidebar
        elif current_route == "/dashboard":
            page.current_tab = "DASHBOARD"
            active_content = dashboard(page)
            layout_type = "sidebar"
        elif current_route == "/records":
            page.current_tab = "RECORDS"
            active_content = records(page)
            layout_type = "sidebar"
        elif current_route == "/statements":
            page.current_tab = "STATEMENTS"
            active_content = statements(page)
            layout_type = "sidebar"
        elif current_route == "/simulation":
            page.current_tab = "SIMULATION"
            active_content = simulation(page)
            layout_type = "sidebar"
        elif current_route == "/settings":
            page.current_tab = "SETTINGS"
            active_content = ft.Text("This is the account settings panel.", size=16)
            layout_type = "sidebar"
        
        # Fallback for unknown routes
        else:
            page.navigate("/home")
            return
        
        if layout_type == "navbar":
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
        
        elif layout_type == "sidebar":
            global_header = header(current_route)
            
            header_controls = []
            if global_header:
                header_controls.extend([
                    global_header,
                    ft.Divider(height=1, color="#1C2541"),
                    ft.Container(height=15)
                ])
            
            header_controls.append(ft.Container(content=active_content, expand=True))

            header_content = ft.Container(
                content=ft.Column(controls=header_controls, spacing=0),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )

            page.add(
                ft.Row(
                    controls=[
                        sidebar(page, active_route=current_route),
                        header_content
                    ],
                    spacing=0,
                    expand=True
                )
            )
            
        elif layout_type == "none":
            page.add(active_content)

        page.update()

    def handle_resize(e):
        route_change()

    page.on_route_change = route_change
    page.on_resize = handle_resize

    if page.route == "/" or not page.route:
        page.navigate("/home")
    else:
        route_change()

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)