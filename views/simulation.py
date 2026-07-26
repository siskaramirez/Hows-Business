import flet as ft
import requests


API_URL = "http://127.0.0.1:8000"

def simulation(page: ft.Page):
    current_user = page.session.store.get("user")
    user_no = current_user.get("user_no") if current_user else None

    state = {
        "price": 0.00,
        "volume": 0,
        "marketing": 0.00,
        "raw_mat": 0.00,
        "wages": 0.00,
        "utilities": 0.00,
        "seasonal": 0,
        "inflation": 0.0,
        "competition": 0
    }

    def create_parameter_control(label, key, min_v, max_v, is_int=False):
        def on_slider_change(e):
            val = int(e.control.value) if is_int else round(e.control.value, 2)
            state[key] = val
            input_field.value = str(val)
            input_field.update()

        def on_input_submit(e):
            try:
                val = int(e.control.value) if is_int else float(e.control.value)
                val = max(min_v, min(max_v, val)) 
            except ValueError:
                val = state[key]
                
            state[key] = val
            slider.value = val
            input_field.value = str(val)
            slider.update()
            input_field.update()
            run_projection()

        slider = ft.Slider(
            min=min_v, max=max_v, value=state[key],
            active_color=ft.Colors.WHITE, inactive_color=ft.Colors.WHITE_38,
            on_change=on_slider_change,
            on_change_end=lambda _: run_projection(),
            expand=True
        )
        
        input_field = ft.TextField(
            value=str(state[key]), text_size=11, height=28, width=75,
            color="#1C2541", bgcolor=ft.Colors.WHITE, content_padding=4,
            border_radius=6, text_align=ft.TextAlign.CENTER,
            on_submit=on_input_submit, on_blur=on_input_submit
        )

        return ft.Column([
            ft.Text(label, size=11, color=ft.Colors.WHITE_70, weight=ft.FontWeight.W_500),
            ft.Row([slider, input_field], spacing=10)
        ], spacing=2)

    adjustment_column = ft.Column([ 
        ft.Text("ADJUST PARAMETERS", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1)),

        ft.Text("REVENUE & PRICING", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1)),
        create_parameter_control("Unit selling price (₱)", "price", 0, 500),
        create_parameter_control("Sales volume (units)", "volume", 0, 5000, is_int=True),
        create_parameter_control("Marketing spend (₱)", "marketing", 0, 50000),
            
        ft.Divider(color=ft.Colors.WHITE_24, height=15),
        ft.Text("OPERATIONAL COST", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1)),
        create_parameter_control("Raw material cost (₱)", "raw_mat", 0, 150000),
        create_parameter_control("Wages & labor (₱)", "wages", 0, 100000),
        create_parameter_control("Utilities & fuel (₱)", "utilities", 0, 30000),
            
        ft.Divider(color=ft.Colors.WHITE_24, height=15),
        ft.Text("EXTERNAL FACTORS", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1)),
        create_parameter_control("Seasonal demand (%)", "seasonal", -50, 50, is_int=True),
        create_parameter_control("Inflation impact (%)", "inflation", 0, 20),
        create_parameter_control("Market competition (%)", "competition", 0, 100, is_int=True),
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    adjustment_panel = ft.Container(
        content=adjustment_column,
        bgcolor="#1C2541",
        padding=25,
        border_radius=20,
        height=470,
        col={"xs": 12, "md": 5}
    )

    rev_text = ft.Text("₱ 0.00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    profit_text = ft.Text("₱ 0.00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    
    projections_panel = ft.Container(
        content=ft.Column([
            ft.Text("PROJECTED PARAMETERS", size=15, weight=ft.FontWeight.BOLD, color="#1C2541", style=ft.TextStyle(letter_spacing=1)),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Projected Revenue", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        rev_text
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="#1C2541", border_radius=20, padding=16, expand=True, height=110
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Projected Profit", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        profit_text
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor="#1C2541", border_radius=20, padding=16, expand=True, height=110
                )
            ], spacing=15)
        ]),
        bgcolor=ft.Colors.WHITE,
        padding=24,
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), offset=ft.Offset(0, 0))
    )

    prob_percent = ft.Text("0%", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    prob_status = ft.Text("Awaiting Parameters", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_300)
    prob_fill = ft.Container(height=15, width=0, bgcolor="#F87171", border_radius=8)
    prob_bar = ft.Container(
        content=ft.Row([prob_fill], spacing=0),
        height=15,
        bgcolor=ft.Colors.WHITE_10,
        border_radius=8,
        width=280,
        margin=ft.Margin(left=0, top=5, right=0, bottom=0),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
    risk_signal = ft.Text("Adjust the parameters on the left to begin modeling.", size=11, color=ft.Colors.WHITE_70)
    risk_icon = ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.AMBER, size=20)

    success_panel = ft.Container(
        content=ft.Column([
            ft.Text("SUCCESS PROBABILITY", size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=1)),
            ft.Container(
                content=ft.Column([
                    prob_percent,
                    prob_status,
                    ft.Column([
                        prob_bar,
                        ft.Row([
                            ft.Text("High risk", size=10, color=ft.Colors.WHITE_54),
                            ft.Text("Moderate", size=10, color=ft.Colors.WHITE_54),
                            ft.Text("Safe zone", size=10, color=ft.Colors.WHITE_54),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=280)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                alignment=ft.Alignment.CENTER, expand=True
            ),
            ft.Divider(color=ft.Colors.WHITE_24, height=15),
            ft.Row([
                risk_icon,
                ft.Column([
                    ft.Text("Key risk signal", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    risk_signal
                ], spacing=1)
            ], margin=ft.Margin(left=40, top=0, right=0, bottom=0), spacing=10)
        ], spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor="#1C2541",
        padding=25,
        border_radius=20,
        height=260,
    )

    def run_projection():
        if not user_no:
            prob_status.value = "Session expired"
            risk_signal.value = "Please log in again to run a simulation."
            prob_status.update()
            risk_signal.update()
            return

        payload = {
            "user_no": user_no,
            "price": state["price"],
            "volume": state["volume"],
            "marketing": state["marketing"],
            "raw_material": state["raw_mat"],
            "wages": state["wages"],
            "utilities": state["utilities"],
            "seasonality": state["seasonal"],
            "inflation": state["inflation"],
            "competition": state["competition"],
        }

        try:
            response = requests.post(
                f"{API_URL}/simulate",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            projected_revenue = float(result.get("projected_revenue", 0))
            projected_profit = float(result.get("projected_profit", 0))
            probability = max(
                0,
                min(100, float(result.get("probability_adjusted", 0))),
            )

            rev_text.value = f"₱ {projected_revenue:,.2f}"
            profit_text.value = f"₱ {projected_profit:,.2f}"
            profit_text.color = "#4ADE80" if projected_profit >= 0 else "#F87171"
            prob_percent.value = f"{probability:.0f}%"
            prob_status.value = result.get("financial_position", "High risk")
            risk_signal.value = result.get(
                "recommendation",
                "Review the selected parameters.",
            )
            prob_fill.width = 280 * probability / 100

            if probability >= 75:
                signal_color = "#4ADE80"
                risk_icon.icon = ft.Icons.CHECK_CIRCLE_ROUNDED
            elif probability >= 50:
                signal_color = ft.Colors.AMBER
                risk_icon.icon = ft.Icons.WARNING_ROUNDED
            else:
                signal_color = "#F87171"
                risk_icon.icon = ft.Icons.ERROR_ROUNDED

            prob_fill.bgcolor = signal_color
            prob_status.color = signal_color
            risk_icon.color = signal_color

            for control in (
                rev_text,
                profit_text,
                prob_percent,
                prob_status,
                prob_fill,
                risk_signal,
                risk_icon,
            ):
                control.update()
        except (requests.RequestException, ValueError):
            prob_status.value = "Simulation unavailable"
            risk_signal.value = "Unable to calculate this scenario. Check the API connection."
            prob_status.color = "#F87171"
            prob_status.update()
            risk_signal.update()

    right_workspace_stack = ft.Column([
        projections_panel,
        success_panel
    ], spacing=20, col={"xs": 12, "md": 7})

    master_scroll_column = ft.Column(
        controls=[
            ft.ResponsiveRow([
                adjustment_panel,
                right_workspace_stack
            ], spacing=20, margin=ft.Margin(left=10, top=10, right=10, bottom=0))
        ],
        expand=True
    )

    def handle_page_resize(e):
        if page.width < 768:
            master_scroll_column.scroll = ft.ScrollMode.AUTO
            adjustment_column.scroll = None
            adjustment_panel.height = None
            success_panel.height = None
        else:
            master_scroll_column.scroll = None
            adjustment_column.scroll = ft.ScrollMode.AUTO
            adjustment_panel.height = 470
            success_panel.height = 260

        master_scroll_column.update()
        adjustment_panel.update()
        success_panel.update()

    page.on_resize = handle_page_resize
    
    initial_width = page.width if page.width else 1200
    if initial_width < 768:
        master_scroll_column.scroll = ft.ScrollMode.AUTO
        adjustment_column.scroll = None
        adjustment_panel.height = None
        success_panel.height = None
    else:
        master_scroll_column.scroll = None
        adjustment_column.scroll = ft.ScrollMode.AUTO
        adjustment_panel.height = 470
        success_panel.height = 260

    return ft.Container(
        content=master_scroll_column,
        expand=True
    )
