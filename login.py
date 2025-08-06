import flet as ft
import mysql.connector
from mysql.connector import Error
import sqlite3
from jobcard_client import JobCardPage  # Import JobCardPage for sync

def login_page(page: ft.Page):
    page.title = "Job Card System - Login"
    page.window_title = "Job Card System - Login"
    page.window.maximized = False
    page.window.resizable = True
    page.window.width = 400
    page.window.height = 700
    page.padding = 0

    # Session management
    page.session.set("user", None)

    # Initialize snackbar
    snack_bar = ft.SnackBar(
        content=ft.Text("", size=14, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
        bgcolor=ft.Colors.BLACK,
        duration=4000,
        show_close_icon=True,
        behavior=ft.SnackBarBehavior.FLOATING,
        width=340,
        padding=10,
        margin=ft.margin.only(bottom=10),
        shape=ft.RoundedRectangleBorder(radius=8)
    )
    page.overlay.append(snack_bar)

    # Initialize SQLite database for departments and users
    sqlite_db_path = "job_cards.db"
    def init_sqlite_db():
        """Initialize SQLite database and create department and users tables."""
        conn = None
        cursor = None
        try:
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            # Enable foreign key support
            cursor.execute("PRAGMA foreign_keys = ON")
            # Create department table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS department (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
                    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
                )
            ''')
            # Create users table with foreign key to department
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    emp_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    department_name TEXT NOT NULL,
                    can_login INTEGER NOT NULL,
                    FOREIGN KEY (department_name) REFERENCES department(name) ON DELETE RESTRICT
                )
            ''')
            conn.commit()
            snack_bar.content.value = "Database initialized successfully!"
            snack_bar.bgcolor = ft.Colors.TEAL_600
            snack_bar.open = True
            page.update()
        except sqlite3.Error as e:
            snack_bar.content.value = f"Error initializing database: {e}"
            snack_bar.bgcolor = ft.Colors.RED_800
            snack_bar.open = True
            page.update()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    init_sqlite_db()

    # Form fields with enhanced styling for mobile
    emp_id_field = ft.TextField(
        label="EMP ID",
        hint_text="Enter your EMP ID",
        border_color="blue",
        icon="person",
        width=280,
        text_size=16,
        filled=True,
        fill_color="white",
        border_radius=8,
        content_padding=ft.padding.all(12),
    )
    password_field = ft.TextField(
        label="Password",
        hint_text="Enter your password",
        border_color="blue",
        icon="lock",
        password=True,
        width=280,
        text_size=16,
        filled=True,
        fill_color="white",
        border_radius=8,
        content_padding=ft.padding.all(12),
    )

    def sync_users(e):
        """Sync departments and users with can_login = 1 from MySQL to SQLite."""
        db_config = {
            "host": "200.200.200.23",
            "user": "root",
            "password": "Pak@123",
            "database": "asm_sys",
            "auth_plugin": "mysql_native_password"
        }
        conn_mysql = None
        cursor_mysql = None
        conn_sqlite = None
        cursor_sqlite = None
        try:
            # Connect to MySQL
            conn_mysql = mysql.connector.connect(**db_config)
            cursor_mysql = conn_mysql.cursor(dictionary=True)

            # Sync departments from MySQL to SQLite
            cursor_mysql.execute("SELECT id, name, description, created_at, updated_at FROM department")
            departments = cursor_mysql.fetchall()
            conn_sqlite = sqlite3.connect(sqlite_db_path)
            cursor_sqlite = conn_sqlite.cursor()
            cursor_sqlite.execute("PRAGMA foreign_keys = ON")
            cursor_sqlite.execute("DELETE FROM department")
            conn_sqlite.commit()
            for dept in departments:
                cursor_sqlite.execute("""
                    INSERT OR REPLACE INTO department (id, name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    dept["id"],
                    dept["name"],
                    dept["description"],
                    dept["created_at"].strftime('%Y-%m-%d %H:%M:%S') if dept["created_at"] else None,
                    dept["updated_at"].strftime('%Y-%m-%d %H:%M:%S') if dept["updated_at"] else None
                ))
            conn_sqlite.commit()

            # Sync users from MySQL to SQLite
            cursor_mysql.execute(
                "SELECT emp_id, password, name, department_name, can_login FROM users WHERE can_login = 1"
            )
            users = cursor_mysql.fetchall()
            cursor_sqlite.execute("DELETE FROM users")
            conn_sqlite.commit()
            for user in users:
                cursor_sqlite.execute("""
                    INSERT OR REPLACE INTO users (emp_id, password, name, department_name, can_login)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user["emp_id"],
                    user["password"],
                    user["name"],
                    user["department_name"],
                    user["can_login"]
                ))
            conn_sqlite.commit()

            snack_bar.content.value = f"Synced {len(departments)} departments and {len(users)} users successfully!"
            snack_bar.bgcolor = ft.Colors.TEAL_600
            snack_bar.duration = 4000
            snack_bar.open = True
        except mysql.connector.Error as e:
            snack_bar.content.value = f"Error syncing data: {e}"
            snack_bar.bgcolor = ft.Colors.RED_800
            snack_bar.duration = 4000
            snack_bar.open = True
        except sqlite3.Error as e:
            snack_bar.content.value = f"Error saving data to SQLite: {e}"
            snack_bar.bgcolor = ft.Colors.RED_800
            snack_bar.duration = 4000
            snack_bar.open = True
        finally:
            if cursor_mysql:
                cursor_mysql.close()
            if conn_mysql:
                conn_mysql.close()
            if cursor_sqlite:
                cursor_sqlite.close()
            if conn_sqlite:
                conn_sqlite.close()
            page.update()

    def login(e):
        emp_id = emp_id_field.value.strip()
        password = password_field.value.strip()

        if not emp_id or not password:
            snack_bar.content.value = "Please fill in all fields."
            snack_bar.bgcolor = ft.Colors.RED_800
            snack_bar.duration = 4000
            snack_bar.open = True
            page.update()
            return

        conn = None
        cursor = None
        try:
            # Connect to SQLite for user authentication
            conn = sqlite3.connect(sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute(
                "SELECT emp_id, password, name, department_name, can_login FROM users WHERE emp_id = ? AND password = ?",
                (emp_id, password)
            )
            user = cursor.fetchone()

            if user and user["can_login"] == 1:
                page.session.set("user", {
                    "emp_id": user["emp_id"],
                    "can_login": user["can_login"],
                    "name": user["name"],
                    "department_name": user["department_name"]
                })
                # Initialize JobCardPage and sync job cards
                job_card_page = JobCardPage(page)
                page.views.append(ft.View("/jobcard", [job_card_page]))
                page.go("/jobcard")
                # Trigger sync after navigation
                page.run_task(job_card_page.sync_from_mysql, None)
                snack_bar.content.value = f"Login successful as {user['name']}. Syncing job cards..."
                snack_bar.bgcolor = ft.Colors.TEAL_600
                snack_bar.duration = 4000
                snack_bar.open = True
            else:
                snack_bar.content.value = "User not found or incorrect password. Please sync users or enter correct credentials."
                snack_bar.bgcolor = ft.Colors.RED_800
                snack_bar.duration = 6000
                snack_bar.open = True
        except sqlite3.Error as e:
            snack_bar.content.value = f"Database error: {e}"
            snack_bar.bgcolor = ft.Colors.RED_800
            snack_bar.duration = 4000
            snack_bar.open = True
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            page.update()

    # Sync Users button
    sync_users_button = ft.ElevatedButton(
        text="Sync Users",
        bgcolor="green",
        color="white",
        on_click=sync_users,
        width=280,
        height=45,
        elevation=6,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    # Logo-like title with department name
    logo_text = ft.Row(
        [
            ft.Icon(name="computer", color="blue", size=32),
            ft.Text(
                "Gujranwala Food Industries\nIT Department",
                size=20,
                weight=ft.FontWeight.BOLD,
                color="blue",
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )

    # Login form with card optimized for mobile
    login_form = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    logo_text,
                    ft.Container(height=20),
                    ft.Text("Login", size=18, weight=ft.FontWeight.BOLD, color="blue", font_family="Athelas"),
                    ft.Container(height=15),
                    emp_id_field,
                    ft.Container(height=15),
                    password_field,
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        text="Login",
                        bgcolor="blue",
                        color="white",
                        on_click=login,
                        width=280,
                        height=45,
                        elevation=6,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                    ft.Container(height=15),
                    sync_users_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=ft.padding.all(20),
            bgcolor="white",
            width=360,
            height=500,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=8,
                color="blue",
                offset=ft.Offset(0, 4),
            ),
        ),
    )

    # Page layout with full background
    return ft.Container(
        content=login_form,
        alignment=ft.alignment.center,
        expand=True,
        bgcolor="lightcyan",
    )
