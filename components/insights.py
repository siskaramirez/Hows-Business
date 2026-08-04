import flet as ft
import requests


API_URL = "http://127.0.0.1:8000"
CATEGORIES = ["All", "Revenue", "Cost Control", "Operations", "Demand"]
THEMES = {
    "Revenue": {
        "accent": "#3D8B2B",
        "surface": "#D8FFC5",
        "text": "#245F1A",
    },
    "Cost Control": {
        "accent": "#A61B1B",
        "surface": "#FFD0D0",
        "text": "#7C1717",
    },
    "Operations": {
        "accent": "#1769AA",
        "surface": "#CEEAFE",
        "text": "#12568D",
    },
    "Demand": {
        "accent": "#365AA8",
        "surface": "#D5E2FF",
        "text": "#263F78",
    },
}


def fetch_insights(user_no):
    if not user_no:
        return None, "Your session has expired. Please log in again."

    try:
        response = requests.get(
            f"{API_URL}/insights",
            params={"user_no": user_no},
            timeout=60,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        detail = "Unable to load business insights."
        if exc.response is not None:
            try:
                detail = exc.response.json().get("detail", detail)
            except ValueError:
                pass
        return None, detail


def business_insights_section(page, user_no, prefetched=None):
    result, error = prefetched if prefetched is not None else fetch_insights(user_no)
    insights = result.get("insights", []) if result else []
    period = result.get("period", "No transaction data") if result else ""
    connected_datasets = result.get("datasets_connected", []) if result else []
    active_category = "All"
    expanded_id = None
    content = ft.Column(spacing=10)

    def show_feedback(helpful):
        message = (
            "Thanks. This recommendation was marked helpful."
            if helpful
            else "Thanks. This recommendation was marked not helpful."
        )
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor="#1C2541",
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def select_category(category):
        nonlocal active_category, expanded_id
        active_category = category
        expanded_id = None
        render()
        content.update()

    def toggle_insight(insight_id):
        nonlocal expanded_id
        expanded_id = None if expanded_id == insight_id else insight_id
        render()
        content.update()

    def category_button(category):
        selected = category == active_category
        return ft.TextButton(
            content=ft.Text(
                category,
                size=12,
                weight=ft.FontWeight.BOLD,
                color="#1C2541" if selected else ft.Colors.WHITE,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE if selected else "#555555",
                side=ft.BorderSide(1, "#555555"),
                shape=ft.RoundedRectangleBorder(radius=5),
                padding=ft.Padding(left=16, top=8, right=16, bottom=8),
            ),
            on_click=lambda _, value=category: select_category(value),
        )

    def summary_card(insight):
        theme = THEMES.get(insight["category"], THEMES["Revenue"])
        is_expanded = expanded_id == insight["id"]
        has_data = insight.get("has_enough_data", False)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        insight["eyebrow"],
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=theme["text"],
                    ),
                    ft.Text(
                        insight["title"],
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color="#1C2541",
                    ),
                    ft.Text(
                        insight["summary"],
                        size=13,
                        color="#344054",
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    insight["estimate"],
                                    size=11,
                                    color=ft.Colors.WHITE if has_data else "#344054",
                                ),
                                bgcolor=theme["accent"] if has_data else "#E6E8EC",
                                border_radius=5,
                                padding=ft.Padding(left=12, top=7, right=12, bottom=7),
                            ),
                            ft.Icon(
                                ft.Icons.KEYBOARD_ARROW_DOWN
                                if is_expanded
                                else ft.Icons.KEYBOARD_ARROW_RIGHT,
                                color=theme["accent"],
                                size=30,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=theme["surface"],
            border=ft.Border.all(2, theme["accent"]),
            border_radius=8,
            padding=20,
            data=insight["id"],
            on_click=lambda _: toggle_insight(insight["id"]),
        )

    def detail_panel(insight):
        theme = THEMES.get(insight["category"], THEMES["Revenue"])
        metrics = insight.get("metrics", [])
        actions = insight.get("actions", [])

        metric_controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            item["value"],
                            size=19,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            item["label"],
                            size=10,
                            color=ft.Colors.WHITE_70,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                col={"xs": 12, "sm": 4},
                padding=ft.Padding(left=8, top=6, right=8, bottom=6),
            )
            for item in metrics
        ]

        controls = [
            ft.Text(
                insight["detail_title"],
                size=15,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            ft.Text(insight["detail"], size=13, color=ft.Colors.WHITE),
        ]
        if metric_controls:
            controls.extend(
                [
                    ft.Divider(height=1, color=ft.Colors.WHITE_24),
                    ft.ResponsiveRow(controls=metric_controls, spacing=0, run_spacing=4),
                ]
            )
        controls.extend(
            [
                ft.Text(
                    "WHAT TO DO",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            f"{index}. {action}",
                            size=12,
                            color=ft.Colors.WHITE,
                        )
                        for index, action in enumerate(actions, start=1)
                    ],
                    spacing=5,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Was this helpful?", size=11, color=ft.Colors.WHITE_70),
                        ft.IconButton(
                            icon=ft.Icons.THUMB_UP_OUTLINED,
                            icon_color="#4ADE80",
                            tooltip="Helpful",
                            on_click=lambda _: show_feedback(True),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.THUMB_DOWN_OUTLINED,
                            icon_color="#F87171",
                            tooltip="Not helpful",
                            on_click=lambda _: show_feedback(False),
                        ),
                    ],
                    spacing=4,
                ),
            ]
        )

        return ft.Container(
            content=ft.Column(controls=controls, spacing=9),
            bgcolor="#292929",
            border=ft.Border(left=ft.BorderSide(3, theme["accent"])),
            padding=ft.Padding(left=22, top=18, right=22, bottom=14),
        )

    def insight_control(insight):
        controls = [summary_card(insight)]
        if expanded_id == insight["id"]:
            controls.append(detail_panel(insight))
        return ft.Column(controls=controls, spacing=0)

    def render():
        visible_insights = [
            insight
            for insight in insights
            if active_category == "All" or insight["category"] == active_category
        ]

        section_controls = [
            ft.Text(
                "BUSINESS INSIGHTS & RECOMMENDATIONS",
                size=18,
                weight=ft.FontWeight.BOLD,
                color="#1C2541",
            ),
            ft.Text(
                f"BASED ON YOUR {period.upper()} RECORDS",
                size=12,
                color="#344054",
            ),
            ft.Text(
                (
                    f"{len(connected_datasets)} REFERENCE DATASET"
                    f"{'' if len(connected_datasets) == 1 else 'S'} CONNECTED"
                ),
                size=10,
                color="#365AA8",
                weight=ft.FontWeight.BOLD,
                visible=bool(connected_datasets),
                tooltip=", ".join(connected_datasets),
            ),
            ft.Row(
                controls=[category_button(category) for category in CATEGORIES],
                spacing=8,
                run_spacing=8,
                wrap=True,
            ),
        ]

        if error:
            section_controls.append(
                ft.Container(
                    content=ft.Text(error, color="#A61B1B", size=13),
                    border=ft.Border.all(1, "#A61B1B"),
                    border_radius=8,
                    padding=16,
                )
            )
        elif not visible_insights:
            section_controls.append(
                ft.Text(
                    "No insights are available for this category.",
                    size=13,
                    italic=True,
                    color="#667085",
                )
            )
        else:
            section_controls.extend(
                insight_control(insight) for insight in visible_insights
            )

        content.controls = section_controls

    render()
    return ft.Container(
        content=content,
        bgcolor="#F0F1F3",
        border_radius=8,
        padding=ft.Padding(left=24, top=24, right=24, bottom=24),
        margin=ft.Margin(left=10, top=0, right=10, bottom=10),
    )
