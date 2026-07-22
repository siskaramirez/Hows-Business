import flet as ft
from datetime import datetime
import requests

API_URL = "http://127.0.0.1:8000"

def statements(page: ft.Page):
    current_statement = None
    
    months_list = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]

    default_month = months_list[datetime.now().month - 1]
    current_user = page.session.store.get("user")
    user_no = current_user.get("user_no") if current_user else None
    
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
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 0)) if is_active else None,
            padding=16,
            border_radius=20,
            height=120,
            col={"xs": 12, "md": 6},
            data=text,
            on_click=load_report_for_current_selection
        )
    
    def load_report_for_current_selection(e):
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
        #actions_row.update()
        
        selected_month = month_dropdown.value if month_dropdown.value else default_month
        
        output_workspace.bgcolor = "#1C2541"
        output_workspace.padding = 24

        output_workspace.content = ft.Column([
            ft.Text(
                f"{current_statement} — {selected_month.upper()} 2026", 
                size=16, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.WHITE,
                style=ft.TextStyle(letter_spacing=1)
            ),
            ft.Divider(height=1, color=ft.Colors.WHITE_24),
            ft.ProgressRing(visible=True),
            ft.Text("Generating report...", color="#F5F5F5"),
        ], spacing=16)
        page.update()

        report_type = "income_statement"
        if current_statement == "BALANCE SHEET":
            report_type = "balance_sheet"
        elif current_statement == "TRIAL BALANCE":
            report_type = "trial_balance"
        elif current_statement == "CASH FLOW":
            report_type = "cash_flow"

        def empty_state(message: str):
            return ft.Container(
                content=ft.Text(
                    message,
                    size=12,
                    italic=True,
                    color=ft.Colors.BLUE_GREY_300,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                padding=40,
                expand=True,
            )

        def build_report_view(data):
            if report_type == "income_statement":
                revenue_rows = data.get("revenue_details", []) or []
                expense_rows = data.get("expense_details", []) or []

                if not revenue_rows and not expense_rows:
                    return empty_state("No income statement data available for this period.")

                rows = []
                for item in revenue_rows:
                    rows.append((item.get("Account", ""), f"₱{item.get('Amount', 0):,.2f}", "Revenue"))
                for item in expense_rows:
                    rows.append((item.get("Account", ""), f"₱{item.get('Amount', 0):,.2f}", "Expense"))

                summary = [
                    ("Total Revenue", f"₱{data.get('total_revenue', 0):,.2f}"),
                    ("Total Expenses", f"₱{data.get('total_expenses', 0):,.2f}"),
                    ("Net Profit", f"₱{data.get('net_profit', 0):,.2f}"),
                ]

                return ft.Column([
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Account", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Amount", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Type", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                            ],
                            rows=[
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text(r[0], color="#FFFFFF")),
                                    ft.DataCell(ft.Text(r[1], color="#FFFFFF")),
                                    ft.DataCell(ft.Text(r[2], color="#FFFFFF")),
                                ]) for r in rows
                            ],
                            column_spacing=24,
                            width=float("inf"),
                        ),
                        margin=ft.Margin(left=15, top=5, right=15, bottom=5),
                    ),
                    ft.Column([
                        ft.Text(f"{label}: {value}", size=13, color="#FFFFFF")
                        for label, value in summary
                    ], spacing=4),
                ], spacing=12)

            if report_type == "balance_sheet":
                asset_rows = data.get("asset_details", []) or []
                liability_rows = data.get("liability_details", []) or []
                equity_rows = data.get("equity_details", []) or []

                if not asset_rows and not liability_rows and not equity_rows:
                    return empty_state("No balance sheet data available for this period.")
    
                rows = []
                for item in asset_rows:
                    rows.append((item.get("Account", ""), f"₱{item.get('Amount', 0):,.2f}", "Asset"))
                for item in liability_rows:
                    rows.append((item.get("Account", ""), f"₱{item.get('Amount', 0):,.2f}", "Liability"))
                for item in equity_rows:
                    rows.append((item.get("Account", ""), f"₱{item.get('Amount', 0):,.2f}", "Equity"))

                summary = [
                    ("Total Assets", f"₱{data.get('total_assets', 0):,.2f}"),
                    ("Total Liabilities", f"₱{data.get('total_liabilities', 0):,.2f}"),
                    ("Total Equity", f"₱{data.get('total_equity', 0):,.2f}"),
                ]

                return ft.Column([
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Account", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Amount", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Type", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                            ],
                            rows=[
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text(r[0], color="#FFFFFF")),
                                    ft.DataCell(ft.Text(r[1], color="#FFFFFF")),
                                    ft.DataCell(ft.Text(r[2], color="#FFFFFF")),
                                ]) for r in rows
                            ],
                            column_spacing=24,
                            width=float("inf"),
                        ),
                        margin=ft.Margin(left=15, top=5, right=15, bottom=5),
                    ),
                    ft.Column([
                        ft.Text(f"{label}: {value}", size=13, color="#FFFFFF")
                        for label, value in summary
                    ], spacing=4),
                ], spacing=12)

            if report_type == "trial_balance":
                rows = data.get("trial_balance", []) or []
                
                if not rows:
                    return empty_state("No trial balance data available for this period.")

                return ft.Column([
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Account Type", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Account", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Debit", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Credit", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                            ],
                            rows=[
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text(item.get("Account Type", ""), color="#FFFFFF")),
                                    ft.DataCell(ft.Text(item.get("Account", ""), color="#FFFFFF")),
                                    ft.DataCell(ft.Text(f"₱{item.get('Debit', 0):,.2f}", color="#FFFFFF")),
                                    ft.DataCell(ft.Text(f"₱{item.get('Credit', 0):,.2f}", color="#FFFFFF")),
                                ]) for item in rows
                            ],
                            column_spacing=24,
                            width=float("inf"),
                        ),
                        margin=ft.Margin(left=15, top=5, right=15, bottom=5),
                    ),
                ], spacing=12)

            if report_type == "cash_flow":
                rows = data.get("cash_flow_details", []) or []

                if not rows:
                    return empty_state("No cash flow data available for this period.")
    
                return ft.Column([
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Account", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Amount", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Type", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
                            ],
                            rows=[
                                ft.DataRow(cells=[
                                    ft.DataCell(ft.Text(item.get("Account", ""), color="#FFFFFF")),
                                    ft.DataCell(ft.Text(f"₱{item.get('Amount', 0):,.2f}", color="#FFFFFF")),
                                    ft.DataCell(ft.Text(item.get("account_type", ""), color="#FFFFFF")),
                                ]) for item in rows
                            ],
                            column_spacing=24,
                            width=float("inf"),
                        ),
                        margin=ft.Margin(left=15, top=5, right=15, bottom=5),
                    ),
                ], spacing=12)

            return ft.Text("No report data available", color="#FFFFFF")

        try:
            response = requests.post(
                f"{API_URL}/reports",
                json={"report_type": report_type, "month": selected_month, "user_no": user_no},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                content = ft.Text(data["error"], size=13, color="#FFFFFF")
            else:
                content = build_report_view(data)

        except requests.exceptions.HTTPError:
            print("SERVER RESPONSE BODY:", response.text)
            content = ft.Text(
                f"Server error ({response.status_code}):\n{response.text}",
                size=13,
                color="#FFFFFF",
            )

        except Exception as exc:
            content = ft.Column([
                ft.Text(
                    f"Unable to reach the FastAPI reports service.\nURL: {API_URL}/reports\nError: {exc}",
                    size=13,
                    color="#FFFFFF",
                ),
            ], spacing=16)

        output_workspace.content = ft.Column([
            ft.Text(
                f"{current_statement} — {selected_month.upper()} 2026",
                size=16,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF",
                style=ft.TextStyle(letter_spacing=1),
            ),
            content,
        ], spacing=16)
        page.update()
            
    month_dropdown = ft.Dropdown(
        hint_text="Select a month...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        border_radius=12,
        border_color="#1C2541",
        color="#1C2541",
        label_style=ft.TextStyle(color="#1C2541", weight=ft.FontWeight.W_600),
        options=[ft.dropdown.Option(m) for m in months_list],
        width=220,
        height=55,
        value=default_month,
    )

    def on_month_change(e):
        if current_statement:
            class _FakeControl:
                data = current_statement
                
            class _FakeEvent:
                control = _FakeControl()
            load_report_for_current_selection(_FakeEvent())

    month_dropdown.on_change = on_month_change

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
        margin=ft.Margin(left=10, top=10, right=10, bottom=0),
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    output_workspace = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Select a statement and month to view the report.", 
                    size=12,
                    italic=True, 
                    color=ft.Colors.BLUE_GREY_300,
                    text_align=ft.TextAlign.CENTER,
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.Alignment.CENTER,
        border_radius=20,
        padding=40
    )

    return ft.Container(
        content=ft.Column([
            actions_row,
            output_workspace
        ], spacing=16, scroll=ft.ScrollMode.AUTO),
        expand=True
    )