import asyncio

import flet as ft
import requests


API_URL = "http://127.0.0.1:8000"
ACCOUNT_TYPES = ["Asset", "Liability", "Equity", "Revenue", "Expense"]
PAYMENT_METHODS = ["Cash", "Gcash", "Maya"]
TRANSACTION_TYPES = [
    "Cash",
    "Kitchen Equipment",
    "Inventory",
    "Accounts Payable",
    "Loans Payable",
    "Lease Liability",
    "Owner's Equity",
    "Retained Earnings",
    "Food Sales",
    "Beverage and Snack Sales",
    "Cost of Goods Sold (COGS)",
    "Canteen Rent Expense",
    "Utilities Expense",
    "Sales",
    "Rent Expense",
    "Office Supplies",
    "Service Revenue",
    "Cost of Goods Sold",
    "Equipment",
]


def records(page: ft.Page):
    current_user = page.session.store.get("user")
    user_no = current_user.get("user_no") if current_user else None

    input_style = {
        "bgcolor": ft.Colors.WHITE,
        "color": "#1C2541",
        "text_size": 12,
        "height": 45,
        "content_padding": ft.Padding(left=10, top=10, right=10, bottom=10),
        "border_radius": 6,
        "border_color": ft.Colors.TRANSPARENT,
    }
    dropdown_style = {
        "fill_color": ft.Colors.WHITE,
        "filled": True,
        "color": "#1C2541",
        "text_size": 12,
        "content_padding": ft.Padding(left=10, top=0, right=10, bottom=0),
        "border_radius": 6,
        "border_color": ft.Colors.TRANSPARENT,
    }

    date_field = ft.TextField(
        hint_text="YYYY-MM-DD",
        width=150,
        **input_style,
    )
    description_field = ft.TextField(
        hint_text="e.g., Batch Sale",
        width=150,
        **input_style,
    )
    account_field = ft.Dropdown(
        hint_text="Select account...",
        options=[ft.dropdown.Option(value) for value in ACCOUNT_TYPES],
        width=150,
        **dropdown_style,
    )
    amount_field = ft.TextField(
        hint_text="e.g., 1,500.00",
        width=150,
        **input_style,
    )
    payment_field = ft.Dropdown(
        hint_text="Select payment...",
        options=[ft.dropdown.Option(value) for value in PAYMENT_METHODS],
        width=150,
        **dropdown_style,
    )
    transaction_field = ft.Dropdown(
        hint_text="Select type...",
        options=[ft.dropdown.Option(value) for value in TRANSACTION_TYPES],
        width=150,
        **dropdown_style,
    )
    invoice_field = ft.TextField(
        hint_text="e.g., OR-9982",
        width=150,
        **input_style,
    )
    search_field = ft.TextField(
        hint_text="Search...",
        width=190,
        height=36,
        text_size=12,
        content_padding=10,
        prefix_icon=ft.Icons.SEARCH,
        bgcolor="#F4F6F9",
        border_radius=8,
        border_color=ft.Colors.TRANSPARENT,
    )
    table_container = ft.Column(expand=True)
    page_size = 50
    current_page = 0
    total_records = 0
    pagination_text = ft.Text(size=12, color="#667085")
    previous_page_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        tooltip="Previous page",
    )
    next_page_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT,
        tooltip="Next page",
    )

    def show_message(message, color="#1C2541"):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def close_dialog(_=None):
        page.pop_dialog()

    def fetch_records():
        nonlocal total_records
        if not user_no:
            return []
        try:
            params = {
                "user_no": user_no,
                "limit": page_size,
                "offset": current_page * page_size,
            }
            query = (search_field.value or "").strip()
            if query:
                params["search"] = query
            response = requests.get(
                f"{API_URL}/records/",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                total_records = int(payload.get("total", 0) or 0)
                return payload.get("records", [])
            total_records = len(payload)
            return payload
        except (requests.RequestException, ValueError):
            return []

    def fetch_records_version():
        if not user_no:
            return None
        try:
            response = requests.get(
                f"{API_URL}/records/version",
                params={"user_no": user_no},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            return (
                int(payload.get("record_count", 0) or 0),
                int(payload.get("latest_ref", 0) or 0),
            )
        except (requests.RequestException, TypeError, ValueError):
            return None

    def confirm_delete(record):
        def void_record(_):
            try:
                response = requests.delete(
                    f"{API_URL}/records/{record['ref_no']}",
                    params={"user_no": user_no},
                    timeout=30,
                )
                response.raise_for_status()
                close_dialog()
                update_table_view()
                show_message(f"{record.get('invoice_no') or 'Record'} was voided.")
            except requests.RequestException:
                close_dialog()
                show_message("Unable to void this record.", ft.Colors.RED_400)

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Void record?"),
                content=ft.Text(
                    "The entry will remain in the audit list but will be excluded "
                    "from reports, forecasts, and simulations."
                ),
                actions=[
                    ft.TextButton(content=ft.Text("Cancel"), on_click=close_dialog),
                    ft.TextButton(
                        content=ft.Text("Void", color=ft.Colors.RED_600),
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=void_record,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def edit_control(control, col):
        return ft.Container(content=control, col=col)

    def open_edit_dialog(record):
        edit_date = ft.TextField(label="Date", value=str(record["transaction_date"]))
        edit_description = ft.TextField(
            label="Description",
            value=record.get("description") or "",
        )
        edit_account = ft.Dropdown(
            label="Account type",
            value=record.get("account_name"),
            options=[ft.dropdown.Option(value) for value in ACCOUNT_TYPES],
        )
        edit_amount = ft.TextField(
            label="Amount (PHP)",
            value=str(record.get("amount") or ""),
        )
        edit_payment = ft.Dropdown(
            label="Payment method",
            value=record.get("payment_method"),
            options=[ft.dropdown.Option(value) for value in PAYMENT_METHODS],
        )
        edit_transaction = ft.Dropdown(
            label="Transaction type",
            value=record.get("transaction_type"),
            options=[ft.dropdown.Option(value) for value in TRANSACTION_TYPES],
        )
        edit_invoice = ft.TextField(
            label="Invoice no.",
            value=record.get("invoice_no") or "",
        )
        error_text = ft.Text(color=ft.Colors.RED_600, visible=False, size=12)

        def show_edit_error(message):
            error_text.value = message
            error_text.visible = True
            error_text.update()

        def save_edit(_):
            values = (
                edit_date.value,
                edit_description.value,
                edit_account.value,
                edit_amount.value,
                edit_payment.value,
                edit_transaction.value,
                edit_invoice.value,
            )
            if not all(values):
                show_edit_error("Complete every field before saving.")
                return
            try:
                amount = float(str(edit_amount.value).replace(",", ""))
                if amount <= 0:
                    raise ValueError
            except ValueError:
                show_edit_error("Amount must be a positive number.")
                return

            try:
                response = requests.put(
                    f"{API_URL}/records/{record['ref_no']}",
                    json={
                        "user_no": user_no,
                        "transaction_date": edit_date.value,
                        "description": edit_description.value,
                        "account_name": edit_account.value,
                        "amount": amount,
                        "payment_method": edit_payment.value,
                        "transaction_type": edit_transaction.value,
                        "invoice_no": edit_invoice.value,
                    },
                    timeout=30,
                )
                if response.status_code == 200:
                    close_dialog()
                    update_table_view()
                    show_message("Record updated successfully.")
                    return
                show_edit_error(
                    response.json().get("detail", "Unable to update this record.")
                )
            except (requests.RequestException, ValueError):
                show_edit_error("Unable to update this record.")

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "EDIT ENTRY",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color="#1C2541",
                ),
                content=ft.Container(
                    width=690,
                    content=ft.Column(
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    edit_control(edit_date, {"xs": 12, "sm": 4}),
                                    edit_control(edit_description, {"xs": 12, "sm": 8}),
                                    edit_control(edit_account, {"xs": 12, "sm": 4}),
                                    edit_control(edit_amount, {"xs": 12, "sm": 4}),
                                    edit_control(edit_payment, {"xs": 12, "sm": 4}),
                                    edit_control(edit_transaction, {"xs": 12, "sm": 8}),
                                    edit_control(edit_invoice, {"xs": 12, "sm": 4}),
                                ],
                                spacing=12,
                                run_spacing=12,
                            ),
                            error_text,
                        ],
                        tight=True,
                    ),
                ),
                actions=[
                    ft.TextButton(content=ft.Text("CANCEL"), on_click=close_dialog),
                    ft.ElevatedButton(
                        content=ft.Text("SAVE CHANGES"),
                        bgcolor="#4FAE3A",
                        color=ft.Colors.WHITE,
                        on_click=save_edit,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def status_pill(status):
        colors = {
            "active": ("#E2F7ED", "#2ECC71"),
            "edited": ("#FFF3CD", "#B7791F"),
            "voided": ("#F8D7DA", "#E74C3C"),
        }
        background, foreground = colors.get(status, ("#E0E0E0", "#333333"))
        return ft.Container(
            content=ft.Text(
                status,
                size=11,
                color=foreground,
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=background,
            border_radius=15,
            padding=ft.Padding(left=12, top=3, right=12, bottom=3),
        )

    def build_table(transactions=None):
        if transactions is None:
            transactions = fetch_records()

        rows = []
        for row_index, record in enumerate(transactions, start=1):
            status = record.get("status", "active")
            display_no = int(record.get("display_no") or row_index)
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"{display_no:02d}", size=12)),
                        ft.DataCell(ft.Text(str(record.get("transaction_date") or ""), size=12)),
                        ft.DataCell(
                            ft.Text(
                                record.get("account_name") or "",
                                size=12,
                                weight=ft.FontWeight.W_500,
                            )
                        ),
                        ft.DataCell(status_pill(status)),
                        ft.DataCell(ft.Text(record.get("description") or "", size=12)),
                        ft.DataCell(ft.Text(record.get("invoice_no") or "", size=12)),
                        ft.DataCell(
                            ft.Text(
                                f"₱{float(record.get('amount', 0)):,.2f}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            )
                        ),
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.CHECK_BOX_OUTLINED,
                                        icon_size=18,
                                        icon_color="#1C2541",
                                        padding=0,
                                        tooltip="Edit entry",
                                        visible=status != "voided",
                                        on_click=lambda _, item=record: open_edit_dialog(item),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_OUTLINE,
                                        icon_size=18,
                                        icon_color=ft.Colors.RED_400,
                                        padding=0,
                                        tooltip="Void entry",
                                        visible=status != "voided",
                                        on_click=lambda _, item=record: confirm_delete(item),
                                    ),
                                ],
                                spacing=0,
                            )
                        ),
                    ]
                )
            )

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("#", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Account Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Description", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Invoice no.", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Amount", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Action", weight=ft.FontWeight.BOLD)),
            ],
            rows=rows,
            heading_row_height=42,
            data_row_min_height=42,
            horizontal_lines=ft.BorderSide(0.5, "#E0E0E0"),
        )

    def update_pagination():
        page_count = max(1, (total_records + page_size - 1) // page_size)
        start = current_page * page_size + 1 if total_records else 0
        end = min((current_page + 1) * page_size, total_records)
        pagination_text.value = (
            f"Showing {start}–{end} of {total_records} · "
            f"Page {current_page + 1} of {page_count}"
        )
        previous_page_button.disabled = current_page <= 0
        next_page_button.disabled = current_page >= page_count - 1

    def update_table_view(_=None):
        table_container.controls = [build_table()]
        update_pagination()
        page.update()

    def on_search_change(_):
        nonlocal current_page
        current_page = 0
        update_table_view()

    def go_to_previous_page(_):
        nonlocal current_page
        if current_page > 0:
            current_page -= 1
            update_table_view()

    def go_to_next_page(_):
        nonlocal current_page
        if (current_page + 1) * page_size < total_records:
            current_page += 1
            update_table_view()

    search_field.on_change = on_search_change
    previous_page_button.on_click = go_to_previous_page
    next_page_button.on_click = go_to_next_page

    def clear_manual_fields(_=None):
        for control in (
            date_field,
            description_field,
            amount_field,
            invoice_field,
        ):
            control.value = ""
        for control in (account_field, payment_field, transaction_field):
            control.value = None
        page.update()

    def save_manual_record(_):
        values = (
            date_field.value,
            description_field.value,
            account_field.value,
            amount_field.value,
            payment_field.value,
            transaction_field.value,
            invoice_field.value,
        )
        if not all(values):
            show_message("Please complete every transaction field.", ft.Colors.RED_400)
            return
        try:
            amount = float(str(amount_field.value).replace(",", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            show_message("Amount must be a positive number.", ft.Colors.RED_400)
            return

        try:
            response = requests.post(
                f"{API_URL}/records/",
                json={
                    "user_no": user_no,
                    "transaction_date": date_field.value,
                    "description": description_field.value,
                    "account_name": account_field.value,
                    "amount": amount,
                    "payment_method": payment_field.value,
                    "transaction_type": transaction_field.value,
                    "invoice_no": invoice_field.value,
                },
                timeout=30,
            )
            if response.status_code == 200:
                clear_manual_fields()
                update_table_view()
                show_message("Record saved successfully.")
                return
            show_message(
                response.json().get("detail", "Unable to save record."),
                ft.Colors.RED_400,
            )
        except (requests.RequestException, ValueError):
            show_message("Unable to save record.", ft.Colors.RED_400)

    def show_mpin_dialog(_=None):
        pin_fields = []
        error_text = ft.Text(
            color=ft.Colors.RED_600,
            visible=False,
            size=12,
            text_align=ft.TextAlign.CENTER,
        )

        def on_pin_change(event, index):
            digits = "".join(
                character for character in (event.control.value or "") if character.isdigit()
            )
            event.control.value = digits[-1:] if digits else ""
            event.control.update()
            if digits and index < 3:
                page.run_task(pin_fields[index + 1].focus)

        def verify(_):
            pin = "".join(field.value or "" for field in pin_fields)
            if len(pin) != 4:
                error_text.value = "Enter your complete 4-digit MPIN."
                error_text.visible = True
                error_text.update()
                return
            try:
                response = requests.post(
                    f"{API_URL}/verify-pin/user",
                    json={"user_no": user_no, "pin": pin},
                    timeout=15,
                )
                if response.status_code == 200:
                    close_dialog()
                    page.navigate("/statements")
                    return
                error_text.value = response.json().get("detail", "Incorrect MPIN.")
            except (requests.RequestException, ValueError):
                error_text.value = "Unable to verify your MPIN."
            error_text.visible = True
            error_text.update()

        for index in range(4):
            field = ft.TextField(
                width=62,
                height=62,
                password=True,
                text_align=ft.TextAlign.CENTER,
                text_size=24,
                keyboard_type=ft.KeyboardType.NUMBER,
                input_filter=ft.InputFilter(
                    allow=True,
                    regex_string=r"[0-9]",
                    replacement_string="",
                ),
                bgcolor="#D9D9D9",
                border_radius=12,
                border_color=ft.Colors.TRANSPARENT,
                on_change=lambda event, position=index: on_pin_change(event, position),
            )
            pin_fields.append(field)

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    "Secure MPIN Verification",
                    size=25,
                    weight=ft.FontWeight.BOLD,
                    color="#1C2541",
                    text_align=ft.TextAlign.CENTER,
                ),
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Enter your 4-digit security code to verify all entries.",
                            color="#344054",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Row(
                            controls=pin_fields,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=14,
                        ),
                        error_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    spacing=18,
                ),
                actions=[
                    ft.OutlinedButton(content=ft.Text("CANCEL"), on_click=close_dialog),
                    ft.ElevatedButton(
                        content=ft.Text("VERIFY"),
                        bgcolor="#1C2541",
                        color=ft.Colors.WHITE,
                        on_click=verify,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
        )

    async def download_template(_):
        await page.launch_url(f"{API_URL}/download-template")

    async def open_upload(_):
        if not user_no:
            show_message("Please log in again.", ft.Colors.RED_400)
            return
        await page.launch_url(
            f"{API_URL}/upload?user_no={user_no}",
            web_popup_window=True,
            web_popup_window_name="upload",
            web_popup_window_width=1200,
            web_popup_window_height=820,
        )

    initial_transactions = fetch_records()
    table_container.controls = [build_table(initial_transactions)]
    update_pagination()
    initial_version = fetch_records_version()

    page.records_view_generation = getattr(page, "records_view_generation", 0) + 1
    view_generation = page.records_view_generation

    async def watch_for_imports():
        latest_refs = [int(record.get("ref_no") or 0) for record in initial_transactions]
        last_version = initial_version or (total_records, max(latest_refs, default=0))
        while page.route == "/records" and page.records_view_generation == view_generation:
            await asyncio.sleep(2)
            if page.route != "/records" or page.records_view_generation != view_generation:
                return
            new_version = await asyncio.to_thread(fetch_records_version)
            if new_version is not None and new_version != last_version:
                last_version = new_version
                transactions = await asyncio.to_thread(fetch_records)
                table_container.controls = [build_table(transactions)]
                update_pagination()
                try:
                    page.update()
                except RuntimeError:
                    return

    page.run_task(watch_for_imports)

    upload_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "UPLOAD TRANSACTION FILE",
                    color=ft.Colors.WHITE,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.GestureDetector(
                    on_tap=open_upload,
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.UPLOAD_FILE_OUTLINED,
                                    color=ft.Colors.WHITE,
                                    size=36,
                                ),
                                ft.Text(
                                    "Drag & drop a file\nor click to browse",
                                    color=ft.Colors.WHITE,
                                    size=13,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding(left=0, top=45, right=0, bottom=45),
                        border=ft.Border.all(
                            1,
                            ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                        ),
                        border_radius=10,
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                    ),
                ),
                ft.ElevatedButton(
                    content=ft.Text(
                        "DOWNLOAD TEMPLATE",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                    ),
                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                    bgcolor=ft.Colors.WHITE,
                    color="#1C2541",
                    on_click=download_template,
                ),
            ]
        ),
        expand=True,
        bgcolor="#1C2541",
        border_radius=20,
        padding=25,
    )

    def manual_column(label, control):
        return ft.Column(
            controls=[ft.Text(label, color=ft.Colors.WHITE, size=12), control],
            col={"xs": 6, "sm": 4},
            spacing=4,
        )

    manual_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "MANUAL ENTRY",
                    color=ft.Colors.WHITE,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(height=10),
                ft.ResponsiveRow(
                    controls=[
                        manual_column("Date", date_field),
                        manual_column("Description", description_field),
                        manual_column("Account name", account_field),
                        manual_column("Amount (₱)", amount_field),
                        manual_column("Payment method", payment_field),
                        manual_column("Transaction type", transaction_field),
                        manual_column("Invoice no.", invoice_field),
                        ft.Column(
                            controls=[
                                ft.Container(
                                    content=ft.Row(
                                        controls=[
                                            ft.TextButton(
                                                content=ft.Text(
                                                    "CLEAR",
                                                    color=ft.Colors.WHITE,
                                                ),
                                                on_click=clear_manual_fields,
                                            ),
                                            ft.ElevatedButton(
                                                content=ft.Text("SAVE RECORD"),
                                                icon=ft.Icons.SAVE_OUTLINED,
                                                bgcolor=ft.Colors.WHITE,
                                                color="#1C2541",
                                                on_click=save_manual_record,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    ),
                                    margin=ft.Margin(left=0, top=25, right=0, bottom=0),
                                )
                            ],
                            col={"xs": 12, "sm": 8},
                        ),
                    ],
                    run_spacing=8,
                ),
            ],
            spacing=0,
        ),
        bgcolor="#1C2541",
        border_radius=20,
        padding=25,
    )

    records_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            "TRANSACTION RECORDS",
                            color="#1C2541",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Row(
                            controls=[
                                search_field,
                                ft.ElevatedButton(
                                    content=ft.Text(
                                        "VERIFY ALL ENTRIES",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    bgcolor="#1C2541",
                                    color=ft.Colors.WHITE,
                                    height=36,
                                    on_click=show_mpin_dialog,
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row(
                    controls=[table_container],
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Row(
                    controls=[
                        pagination_text,
                        ft.Row(
                            controls=[previous_page_button, next_page_button],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ]
        ),
        bgcolor=ft.Colors.WHITE,
        padding=20,
        border_radius=20,
        margin=ft.Margin.all(10),
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
        ),
    )

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        ft.Container(upload_card, col={"sm": 12, "md": 5}),
                        ft.Container(manual_card, col={"sm": 12, "md": 7}),
                    ],
                    spacing=20,
                    margin=ft.Margin(left=10, top=10, right=10, bottom=0),
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                records_card,
            ],
            expand=True,
        ),
        expand=True,
    )
