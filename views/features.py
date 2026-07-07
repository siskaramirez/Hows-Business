import flet as ft

def features(page: ft.Page):
    def feature_card(icon: str, title: str, focus: str, description: str):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=50, color="#1C2541"),
                    ft.Container(height=5),
                    ft.Text(
                        title, 
                        size=17, 
                        weight=ft.FontWeight.BOLD, 
                        color="#1C2541",
                        style=ft.TextStyle(letter_spacing=1.5)
                    ),

                    ft.Container(
                        width=120,
                        height=1.5,
                        bgcolor="#1C2541",
                        margin=ft.Margin(0, 4, 0, 8)
                    ),
                    
                    ft.Text(
                        f"Focus: {focus}",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color="#1C2541",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=15),
                    
                    ft.Text(
                        description,
                        size=12,
                        color="#334155",
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(height=1.3)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=25,
            width=210,
            padding=ft.Padding(left=15, top=25, right=15, bottom=20),
            alignment=ft.Alignment.CENTER,
        )
    
    page_title = ft.Text(
        "Key Features",
        size=40,
        weight=ft.FontWeight.BOLD,
        color="#a8c5f0",
        text_align=ft.TextAlign.CENTER,
    )

    cards = ft.Row(
        controls=[
            feature_card(
                icon=ft.Icons.AUTORENEW_ROUNDED,
                title="AUTOMATION",
                focus="Speed, Accuracy, and Efficiency",
                description="It instantly captures every transaction to ensure your records are always precise, organized, and free from human error."
            ),
            feature_card(
                icon=ft.Icons.TRENDING_UP_ROUNDED,
                title="FORECAST",
                focus="Insight and Growth Patterns",
                description="It translates your financial history into visual trends, identifying long-term growth cycles to anticipate the direction of your business."
            ),
            feature_card(
                icon=ft.Icons.BAR_CHART_ROUNDED,
                title="ANALYTICS",
                focus="Discover Meaningful Patterns and Actionable Insights",
                description="It systemize computational analysis of data, to interpret information and communicate complex findings."
            ),
            feature_card(
                icon=ft.Icons.PSYCHOLOGY_ROUNDED,
                title="SIMULATION",
                focus="Strategic Modeling and Risk Control",
                description="It allows you to test business scenarios, such as price or cost changes, to see the impact on your profit before taking any risks."
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=25,
        wrap=True,
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                page_title,
                ft.Container(height=40),
                cards,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
        padding=ft.Padding(left=40, top=40, right=40, bottom=40)
    )