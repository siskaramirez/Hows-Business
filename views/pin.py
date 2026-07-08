import flet as ft

def pin(page: ft.Page, mode="create"):
    is_create = (mode == "create")
    title_text = "Create Security PIN" if is_create else "Secure PIN Verification"
    subtitle_text = (
        "This 4-digit code will be required to access\nyour financial data."
        if is_create else "Enter your 4-digit security code to unlock."
    )
    action_btn_text = "SAVE" if is_create else "VERIFY"

    pin_fields = [ft.TextField() for _ in range(4)]

    def on_pin_change(e, current_index):
        if len(e.control.value) > 1:
            e.control.value = e.control.value[-1]
            e.control.update()
            
        if e.control.value and current_index < 3:
            page.run_task(pin_fields[current_index + 1].focus)
            page.update()

    def clear_pin(_):
        for field in pin_fields:
            field.value = ""
        page.run_task(pin_fields[0].focus)
        page.update()
        
    def handle_submit(_):
        entered_pin = "".join([f.value for f in pin_fields if f.value])
        if len(entered_pin) < 4:
            print("Error: Please complete the 4-digit PIN.")
            return
            
        print(f"PIN Submitted ({mode}): {entered_pin}")
        page.navigate("/home")

    pin_box_row = ft.Row(spacing=15, alignment=ft.MainAxisAlignment.CENTER)
    for i in range(4):
        tf = ft.TextField(
            width=60,
            height=60,
            text_size=25,
            text_align=ft.TextAlign.CENTER,
            password=True,               
            can_reveal_password=False,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""),
            bgcolor="#C0C0C0",           
            border_radius=12,
            border_color=ft.Colors.TRANSPARENT,
            color="#1C2541",
            cursor_color="#1C2541",
            content_padding=0,
            on_change=lambda e, idx=i: on_pin_change(e, idx)
        )
        pin_fields[i] = tf
        pin_box_row.controls.append(tf)

    clear_btn = ft.Container(
        content=ft.Text("CLEAR", size=15, color="#1C2541", weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
        border=ft.Border.all(1.5, "#1C2541"),
        border_radius=8,
        width=140,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=clear_pin
    )

    submit_btn = ft.Container(
        content=ft.Text(action_btn_text, size=15, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, style=ft.TextStyle(letter_spacing=1)),
        bgcolor="#1C2541",
        border_radius=8,
        width=140,
        height=45,
        alignment=ft.Alignment.CENTER,
        on_click=handle_submit
    )

    card_contents = [
        ft.Text(title_text, size=28, weight=ft.FontWeight.BOLD, color="#1C2541", text_align=ft.TextAlign.CENTER),
        ft.Container(height=1),
        ft.Text(subtitle_text, size=15, color="#555555", text_align=ft.TextAlign.CENTER, style=ft.TextStyle(letter_spacing=1)),
        ft.Container(height=10),
        pin_box_row,
        ft.Container(height=5),
    ]

    if not is_create:
        forgot_link = ft.TextButton(
            content=ft.Text("Forgot your PIN?", size=12, color="#555555", style=ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE)),
            on_click=lambda _: page.navigate("/create-pin")
        )
        card_contents.append(ft.Container(content=forgot_link, alignment=ft.Alignment.CENTER, margin=ft.Margin(left=0, top=-22, right=0, bottom=0)))
        card_contents.append(ft.Container(height=10))
    else:
        card_contents.append(ft.Container(height=10))

    card_contents.append(ft.Row([clear_btn, submit_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=20))

    return ft.Container(
        content=ft.Container(
            content=ft.Column(controls=card_contents, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE,
            border_radius=30,
            padding=ft.Padding(left=40, top=40, right=40, bottom=40),
            width=480,
            height=350,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )