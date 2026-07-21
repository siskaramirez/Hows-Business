import flet as ft

def sidebar(page: ft.Page, active_route: str):
    is_mobile = page.width <= 768

    if not hasattr(page, "sidebar_visible"):
        page.sidebar_visible = not is_mobile
    
    if not is_mobile:
        page.sidebar_visible = True
        
    if is_mobile and not page.sidebar_visible:
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                icon_color=ft.Colors.WHITE,
                icon_size=25,
                padding=0,
                on_click=lambda _: [setattr(page, "sidebar_visible", True), page.on_route_change(None)]
            ),
            margin=ft.Margin(left=0, top=20, right=0, bottom=0),
            alignment=ft.Alignment.CENTER,
        )
    
    def is_active(route_path: str):
        return active_route == route_path
    
    def close_sidebar(_):
        page.sidebar_visible = False
        page.update()
        page.on_route_change(None)
        
    def create_menu_item(label: str, target_route: str, is_logout=False):
        active = is_active(target_route)
        
        if is_logout:
            text_color = ft.Colors.RED_400
        else:
            text_color = "#1C2541" if active else ft.Colors.WHITE

        return ft.Container(
            content=ft.Text(
                label,
                color=text_color,
                weight=ft.FontWeight.BOLD,
                size=16,
                style=ft.TextStyle(letter_spacing=1.2)
            ),
            bgcolor=ft.Colors.WHITE if active else ft.Colors.TRANSPARENT,
            border_radius=8,
            margin=ft.Margin(left=35, top=0, right=25, bottom=0),
            padding=ft.Padding(left=20, top=10, right=20, bottom=10),
            width=210,
            alignment=ft.Alignment.CENTER_LEFT,
            on_click=lambda _: page.navigate(target_route)
        )
    
    def create_section_label(text: str):
        return ft.Container(
            content=ft.Text(
                text.upper(),
                color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                size=12,
                weight=ft.FontWeight.BOLD,
                style=ft.TextStyle(letter_spacing=1.5)
            ),
            margin=ft.Margin(left=15, top=20, right=0, bottom=8)
        )
    
    close_btn = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=ft.Colors.WHITE,
            icon_size=25,
            on_click=close_sidebar,
            padding=0,
        ),
        visible=is_mobile,
    )

    sidebar_content = ft.Column(
        controls=[
            ft.Container(
                content=ft.Row([
                    ft.Container(expand=True),
                    ft.Column([
                        ft.Text("HOW'S BUSINESS", size=19, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text("FINANCIAL INSIGHTS", size=12, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE), text_align=ft.TextAlign.CENTER)
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(content=close_btn, alignment=ft.Alignment.TOP_RIGHT, width=40)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                margin=ft.Margin(left=0, top=30, right=0, bottom=20),
            ),
            
            create_section_label("Overview"),
            create_menu_item("DASHBOARD", "/dashboard"),
            create_menu_item("RECORDS", "/records"),
            create_menu_item("FINANCIAL STATEMENT", "/statements"),
            create_menu_item("SIMULATION", "/simulation"),
            
            create_section_label("Account"),
            create_menu_item("LOGOUT", "/login", is_logout=True),
        ],
        spacing=4,
        scroll=ft.ScrollMode.AUTO,
    )
    
    return ft.Container(
        content=sidebar_content,
        width=300,
        padding=ft.Padding(left=20, top=10, right=20, bottom=20),
        expand=False,
    )