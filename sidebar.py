import flet as ft
import mysql.connector
from mysql.connector import Error

class TopBar(ft.Container):
    def __init__(self, page: ft.Page, height=55, bg_color="#4682B4", top_bar_ref=None):
        super().__init__()
        self.page = page
        self.height = height
        self.bg_color = bg_color
        self.top_bar_ref = top_bar_ref
        self.new_job_count = 0
        self.bell_icon_ref = ft.Ref[ft.Stack]()
        # Safely access user department from session
        user = page.session.get("user")
        self.user_department = user.get("department_name", "") if isinstance(user, dict) else ""

    def get_new_job_count(self):
        """Fetch count of open job cards for user's department from database."""
        db_config = {
            "host": "200.200.200.23",
            "user": "root",
            "password": "Pak@123",
            "database": "asm_sys"
        }
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_cards WHERE status = 'Open' AND department_name = %s", (self.user_department,))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count
        except Error as e:
            print(f"Error fetching job card count: {e}")
            return 0

    def update_notification_icon(self):
        """Update the bell icon with current job card count."""
        self.new_job_count = self.get_new_job_count()
        if self.bell_icon_ref.current:
            badge = ft.Container(
                content=ft.Text(str(self.new_job_count), size=12, color=ft.Colors.WHITE),
                width=20,
                height=20,
                bgcolor=ft.Colors.RED_600,
                border_radius=10,
                alignment=ft.alignment.center,
                visible=self.new_job_count > 0
            )
            self.bell_icon_ref.current.controls[1] = badge
            self.bell_icon_ref.current.update()

    def handle_logout(self, e):
        print("Logging out")
        self.page.session.set("user", None)
        self.page.go("/login")
        if self.top_bar_ref and self.top_bar_ref.current:
            self.top_bar_ref.current.update()

    def build(self):
        user = self.page.session.get("user")
        user_name = user.get("name", "Guest") if isinstance(user, dict) else "Guest"

        self.new_job_count = self.get_new_job_count()
        
        user_menu = ft.PopupMenuButton(
            items=[
                ft.PopupMenuItem(
                    text=user_name,
                    disabled=True
                ),
                ft.PopupMenuItem(
                    text="Logout",
                    on_click=self.handle_logout,
                    disabled=not user
                )
            ],
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=24),
                ft.Text(user_name, color=ft.Colors.WHITE, size=14),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=18)
            ], spacing=5),
            tooltip="User Menu"
        )

        menubar = ft.MenuBar(
            style=ft.MenuStyle(
                alignment=ft.alignment.top_left,
                bgcolor="#4682B4",
                mouse_cursor={
                    ft.ControlState.HOVERED: ft.MouseCursor.ALIAS,
                    ft.ControlState.DEFAULT: ft.MouseCursor.BASIC
                }
            ),
            controls=[
                ft.SubmenuButton(
                    content=ft.Text("Menu", color=ft.Colors.WHITE),
                    leading=ft.Icon(ft.Icons.MENU, color=ft.Colors.WHITE),
                    style=ft.ButtonStyle(
                        bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_100}
                    ),
                    tooltip="Menu",
                    controls=[
                        ft.MenuItemButton(
                            content=ft.Text("JobCard"),
                            leading=ft.Icon(ft.Icons.CALL_ROUNDED),
                            style=ft.ButtonStyle(bgcolor={ft.ControlState.HOVERED: ft.Colors.BLUE_100}),
                            on_click=lambda e: self.page.go("/jobcard") if user else None,
                            disabled=not user
                        ),
                    ]
                )
            ]
        )

        self.controls = [
            ft.Container(
                bgcolor=self.bg_color,
                padding=ft.padding.symmetric(vertical=10, horizontal=15),
                height=self.height,
                shadow=ft.BoxShadow(
                    blur_radius=10,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
                ),
                content=ft.Column([
                    ft.Row([
                        ft.Divider(),
                        menubar,
                        ft.Container(expand=True),
                        ft.Row([
                            ft.Stack(
                                ref=self.bell_icon_ref,
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.NOTIFICATIONS,
                                        icon_color=ft.Colors.WHITE,
                                        icon_size=24,
                                        tooltip=f"New Job Cards ({self.new_job_count})",
                                        on_click=lambda e: self.page.go("/jobcard") if user else None,
                                        style=ft.ButtonStyle(
                                            bgcolor={"hovered": "#5A9BD5"},
                                            shape=ft.RoundedRectangleBorder(radius=8)
                                        ),
                                        disabled=not user
                                    ),
                                    ft.Container(
                                        content=ft.Text(str(self.new_job_count), size=12, color=ft.Colors.WHITE),
                                        width=20,
                                        height=20,
                                        bgcolor=ft.Colors.RED_600,
                                        border_radius=10,
                                        alignment=ft.alignment.center,
                                        visible=self.new_job_count > 0,
                                        right=0,
                                        top=0
                                    )
                                ]
                            ),
                            user_menu
                        ], spacing=10)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=5)
            )
        ]
        return self.controls[0]

    def update(self):
        """Rebuild the top bar to ensure fresh controls."""
        self.controls = [self.build()]
        super().update()
