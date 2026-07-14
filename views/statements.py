import flet as ft

def statements(page: ft.Page):
    current_statement = None
    
    months_list = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]
    
    def statement_button(text):
        is_active = current_statement == text
        
        return ft.Container(
            content=ft.Text(
                text,
                size=18,
                weight=ft.FontWeight.BOLD,
                color="#1C2541" if is_active else ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.WHITE if is_active else "#1C2541",
            border=ft.Border.all(2, "#1C2541") if is_active else None,
            padding=16,
            border_radius=20,
            height=120,
            col={"xs": 12, "md": 6},
            data=text,
            on_click=on_statement_click
        )
    
    def on_statement_click(e):
        nonlocal current_statement
        current_statement = e.control.data
        
        actions_row.controls = [
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        statement_button("INCOME STATEMENT"),
                        statement_button("BALANCE SHEET"),
                        statement_button("TRIAL BALANCE"),
                        statement_button("CASH FLOW")
                    ],
                    spacing=15,
                    run_spacing=15,
                ),
                col={"xs": 12, "md": 8},
            ),
            ft.Container(
                content=month_dropdown,
                alignment=ft.Alignment.TOP_RIGHT,
                col={"xs": 12, "md": 4},
            )
        ]
        actions_row.update()
        
        selected_month = month_dropdown.value if month_dropdown.value else "SELECT MONTH"
        
        output_workspace.content = ft.Column([
            ft.Text(
                f"{current_statement} — {selected_month.upper()} 2026", 
                size=16, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.WHITE,
                style=ft.TextStyle(letter_spacing=1)
            ),
            ft.Divider(height=1, color=ft.Colors.WHITE_24),
            ft.Container(
                content=ft.Text(
                    f"Tabular accounting data structure for {current_statement.lower()} displays here.", 
                    size=13, 
                    italic=True, 
                    color=ft.Colors.BLUE_GREY_200
                ),
                alignment=ft.Alignment.CENTER,
                height=200,
            )
        ], spacing=16)
        
        output_workspace.bgcolor = "#1C2541"
        output_workspace.padding = 24
        output_workspace.update()

    month_dropdown = ft.Dropdown(
        hint_text="Select a month...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        border_radius=12,
        border_color="#1C2541",
        color="#1C2541",
        label_style=ft.TextStyle(color="#1C2541", weight=ft.FontWeight.W_600),
        options=[ft.dropdown.Option(m) for m in months_list],
        width=220,
        height=55
    )

    actions_row = ft.ResponsiveRow(
        controls = [
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        statement_button("INCOME STATEMENT"),
                        statement_button("BALANCE SHEET"),
                        statement_button("TRIAL BALANCE"),
                        statement_button("CASH FLOW")
                    ],
                    spacing=15,
                    run_spacing=15,
                ),
                col={"xs": 12, "md": 8},
            ),
            ft.Container(
                content=month_dropdown,
                alignment=ft.Alignment.TOP_RIGHT,
                col={"xs": 12, "md": 4},
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    output_workspace = ft.Container(
        content=ft.Container(),
        border_radius=20,
        height=350,
    )

    return ft.Container(
        content=ft.Column([
            actions_row,
            output_workspace
        ], spacing=16, scroll=ft.ScrollMode.AUTO),
        expand=True
    )