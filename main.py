import flet as ft
from components.navbar import navbar
from components.sidebar import sidebar
from views.home import home
from views.features import features
from views.login import login
from views.signup import signup
from views.forgot_pass import forgot
from views.welcome import welcome
from views.pin import pin
#from views.dashboard import dashboard#

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
        elif current_route == "/dashboard":
            page.current_tab = "DASHBOARD"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("DASHBOARD", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("May 2026 - Sales Overview & ML Forecast", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("Welcome to the internal analytics system workspace panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/branches":
            page.current_tab = "BRANCHES"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("MY BRANCHES", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("Manage your branches and view their performance.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the branches management panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/records":
            page.current_tab = "RECORDS"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("RECORDS", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("View and manage all your records.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the records management panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/statements":
            page.current_tab = "STATEMENTS"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("FINANCIAL STATEMENT", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("View and analyze your financial statements.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the financial statements panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/simulation":
            page.current_tab = "SIMULATION"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("SIMULATION", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("Run simulations and forecasts for your business.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the simulation panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/compliance":
            page.curent_tab = "COMPLIANCE"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("BIR COMPLIANCE", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("Ensure your business is compliant with BIR regulations.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the BIR compliance panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
            layout_type = "sidebar"
        elif current_route == "/settings":
            page.current_tab = "SETTINGS"
            active_content = ft.Container(
                content=ft.Column([
                    ft.Text("SETTINGS", size=28, weight=ft.FontWeight.BOLD, color="#1C2541"),
                    ft.Text("Manage your account settings and preferences.", size=14, color="#555555"),
                    ft.Divider(height=20, color="#1C2541"),
                    ft.Text("This is the account settings panel.", size=16)
                ]),
                padding=30,
                expand=True,
                bgcolor="#F4F6F9"
            )
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
            page.add(
                ft.Row(
                    controls=[
                        sidebar(page, active_route=current_route),
                        active_content
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

ft.run(main, view=ft.AppView.WEB_BROWSER)