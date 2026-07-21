import flet as ft
from datetime import datetime
import requests

API_URL = "http://127.0.0.1:8000"

def records(page: ft.Page):
    def handle_date(e):
        if date_picker.value:
            raw = date_picker.value
            local_date = raw.astimezone()
            
            date.value = f"{local_date.year}-{local_date.month:02d}-{local_date.day:02d}"
            date.update()

    date_picker = ft.DatePicker(on_change=handle_date)
    page.overlay.append(date_picker)

    input_style = {
        "bgcolor": ft.Colors.WHITE,
        "color": "#1C2541",
        "text_size": 12,
        "height": 45,
        "width" : 150, 
        "content_padding": ft.Padding(left=10, top=10, right=10, bottom=10),
        "border_radius": 6,
        "border_color": ft.Colors.TRANSPARENT,
    }

    dropdown_style = {
        "fill_color": ft.Colors.WHITE, 
        "filled": True,
        "color": "#1C2541",
        "text_size": 12,
        "width" : 150, 
        "content_padding": ft.Padding(left=10, top=0, right=10, bottom=0),
        "border_radius": 6,
        "border_color": ft.Colors.TRANSPARENT,
    }

    date = ft.TextField(
        hint_text="Select date...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        read_only=True,
        on_click=lambda _: date_picker.pick_date(),
        **input_style
    )

    description = ft.TextField(
        hint_text="e.g., Batch Sale",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        **input_style
    )

    account = ft.Dropdown(
        hint_text="Select account...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        value=None,
        options=[
            ft.dropdown.Option("Revenue"), 
            ft.dropdown.Option("Expense")
        ], 
        **dropdown_style
    )

    amount = ft.TextField(
        hint_text="e.g., 1,500.00",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        **input_style
    )

    payment = ft.Dropdown(
        hint_text="Select payment method...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        value=None, 
        options=[
            ft.dropdown.Option("Cash"), 
            ft.dropdown.Option("Gcash"), 
            ft.dropdown.Option("Maya")
        ], 
        **dropdown_style
    )

    transaction_type = ft.Dropdown(
        hint_text="Select type...",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        value=None, 
        options=[
            ft.dropdown.Option("COGS Sales"), 
            ft.dropdown.Option("Operating Expense")
        ], 
        **dropdown_style
    )

    invoice = ft.TextField(
        hint_text="e.g., OR-9982",
        hint_style=ft.TextStyle(color=ft.Colors.BLUE_GREY_300),
        **input_style
    )

    table_container = ft.Column(expand=True)
    
    def build_data_rows():
        rows = []

        try:
            response = requests.get(
                f"{API_URL}/records/"
            )

            if response.status_code == 200:
                data = response.json()
                transactions = data.get("records", data) if isinstance(data, dict) else data
            else:
                transactions = []

        except Exception as e:
            print("API Error:", e)
            transactions = []

        for tx in transactions:
            status_val = tx.get("status", "active")

            status_colors = {
                "active": ("#E2F7ED", "#2ECC71"),
                "edit": ("#FFF3CD", "#F1C40F"),
                "void": ("#F8D7DA", "#E74C3C")
            }
            bg, text_col = status_colors.get(status_val, ("#E0E0E0", "#333333"))

            status_pill = ft.Container(
                content=ft.Text(tx["status"], size=11, color=text_col, weight=ft.FontWeight.BOLD),
                bgcolor=bg, border_radius=15, padding=ft.Padding(left=12, top=3, right=12, bottom=3)
            )

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(tx.get("ref_no") or tx.get("id", "")), size=12)),
                        ft.DataCell(ft.Text(str(tx.get("transaction_date") or tx.get("date", "")), size=12)),
                        ft.DataCell(ft.Text(tx.get("account_name", ""), size=12, weight=ft.FontWeight.W_500)),
                        ft.DataCell(status_pill),
                        ft.DataCell(ft.Text(tx.get("description") or "", size=12)),
                        ft.DataCell(ft.Text(tx.get("invoice_no") or "", size=12)),
                        ft.DataCell(ft.Text(f"₱{float(tx.get('amount', 0)):,.2f}", size=12, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.CHECK_BOX_OUTLINED, icon_size=16, icon_color=ft.Colors.BLUE_GREY_400, padding=0),
                                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=16, icon_color=ft.Colors.RED_300, padding=0)
                            ], spacing=0)
                        ),
                    ]
                )
            )

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Date", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Account Name", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Description", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Invoice no.", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Amount", size=12, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Action", size=12, weight=ft.FontWeight.BOLD)),
            ],
            rows=rows,
            heading_row_height=35,
            data_row_min_height=38,
            horizontal_lines=ft.BorderSide(0.5, "#E0E0E0"),
        )
    
    def update_table_view():
        table_container.controls.clear()
        table_container.controls.append(build_data_rows())
        table_container.update()

    def handle_save_record(e):
        if not amount.value or not description.value or not account.value or not date.value:
            snack = ft.SnackBar(ft.Text("Please fill out required Date, Account, Description, and Amount."), bgcolor=ft.Colors.RED_400)
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        
        data = {
            "transaction_date": date.value,
            "description": description.value,
            "account_name": account.value,
            "amount": float(amount.value or 0),
            "payment_method": payment.value,
            "transaction_type": transaction_type.value,
            "invoice_no": invoice.value
        }

        try:
            response = requests.post(f"{API_URL}/records/", json=data)

            if response.status_code == 200:
                date.value = ""
                description.value = ""
                amount.value = ""
                invoice.value = ""
                account.value = None
                payment.value = None
                transaction_type.value = None
                
                date.update()
                description.update()
                amount.update()
                invoice.update()
                account.update()
                payment.update()
                transaction_type.update()

                update_table_view()
        except Exception as err:
            print("Failed to save entry:", err)

    async def download_template(e):
        await page.launch_url(f"{API_URL}/download-template")

    async def open_upload(e):
        current_user = page.session.store.get("user")
        user_no = current_user.get("user_no") if current_user else None

        if not user_no:
            page.open(ft.SnackBar(ft.Text("Please log in again.")))
            page.update()
            return

        await page.launch_url(
            f"{API_URL}/upload?user_no={user_no}",
            web_popup_window=True,
            web_popup_window_name="upload",
            web_popup_window_width=600,
            web_popup_window_height=700,
        )

    table_container.controls.append(build_data_rows())

    upload_card = ft.Container(
        content=ft.Column([
            ft.Text("UPLOAD TRANSACTION FILE", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1.1)),
            ft.GestureDetector(
                on_tap=open_upload,
                content=ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.UPLOAD_FILE_OUTLINED, color=ft.Colors.WHITE, size=36),
                        ft.Text("Drag & drop a file\nor click to browse", color=ft.Colors.WHITE, size=13, text_align=ft.TextAlign.CENTER)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=0, top=45, right=0, bottom=45),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)), 
                    border_radius=10, 
                    expand=True,
                    alignment=ft.Alignment.CENTER
                ),
            ),
            ft.ElevatedButton(
                content=ft.Text(
                    "DOWNLOAD TEMPLATE",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color="#1C2541"
                ),
                icon=ft.Icons.DOWNLOAD_ROUNDED,
                icon_color="#1C2541",
                bgcolor=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                height=30,
                margin=ft.Margin(left=0, top=5, right=0, bottom=0),
                on_click=download_template
            )
        ]),
        expand=True, 
        bgcolor="#1C2541", 
        border_radius=20, 
        padding=25,
    )
    
    manual_card = ft.Container(
        content=ft.Column([
            ft.Text("MANUAL ENTRY", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1.1)),
            ft.Container(height=10),

            ft.ResponsiveRow([
                ft.Column([ft.Text("Date", color=ft.Colors.WHITE, size=12), date], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                ft.Column([ft.Text("Description", color=ft.Colors.WHITE, size=12), description], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                ft.Column([ft.Text("Account name", color=ft.Colors.WHITE, size=12), account], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                
                ft.Column([ft.Text("Amount (₱)", color=ft.Colors.WHITE, size=12), amount], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                ft.Column([ft.Text("Payment method", color=ft.Colors.WHITE, size=12), payment], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                ft.Column([ft.Text("Transaction Type", color=ft.Colors.WHITE, size=12), transaction_type], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                
                ft.Column([ft.Text("Invoice no.", color=ft.Colors.WHITE, size=12), invoice], col={"xs": 6, "sm": 4, "md": 4}, spacing=4),
                
                ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.TextButton(
                                content=ft.Text(
                                    "CLEAR",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                                )
                            ),
                            ft.ElevatedButton(
                                content=ft.Text(
                                    "SAVE RECORD",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color="#1C2541"
                                ),
                                icon=ft.Icons.SAVE_OUTLINED,
                                icon_color="#1C2541",
                                bgcolor=ft.Colors.WHITE,
                                on_click=handle_save_record,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                                height=30
                            )
                        ], alignment=ft.MainAxisAlignment.END),
                        margin=ft.Margin(left=0, top=30, right=0, bottom=0),
                    )
                ], col={"xs": 12, "sm": 8, "md": 8})
            ], run_spacing=8, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=0),
        bgcolor="#1C2541", 
        border_radius=20, 
        padding=25,
    )

    records_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("TRANSACTION RECORDS", color="#1C2541", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.TextField(hint_text="Search...", width=180, height=30, text_size=12, content_padding=10, prefix_icon=ft.Icons.SEARCH, bgcolor="#F4F6F9", border_radius=8, border_color=ft.Colors.TRANSPARENT),
                    ft.ElevatedButton(
                        content=ft.Text(
                            "GENERATE",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        bgcolor="#1C2541",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                        height=30,
                        on_click=lambda _: page.navigate("/statements")
                    )
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            
            ft.Row([table_container], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        ]),
        bgcolor=ft.Colors.WHITE,
        padding=20,
        border_radius=20,
        margin=ft.Margin.all(10),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 0))
    )

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.ResponsiveRow([
                    ft.Container(upload_card, col={"sm": 12, "md": 5}, height=300),
                    ft.Container(manual_card, col={"sm": 12, "md": 7})
                ], spacing=20, margin=ft.Margin(left=10, top=10, right=10, bottom=0)),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                records_card
            ],
            expand=True
        ),
        expand=True,
    )