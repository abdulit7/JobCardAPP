import os
os.environ["FLET_SECRET_KEY"] = "mysecret123"
import flet as ft
import urllib.parse
import asyncio
from login import login_page
from jobcard_client import JobCardPage
from sidebar import TopBar

# Routing map with only login and jobcard routes
def get_route_map(page):
    return {
        "/login": lambda: login_page(page),
        "/jobcard": lambda: JobCardPage(page),
    }

# Main entry point for Flet app
def main(page: ft.Page):
    page.title = "Job Card System"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 0
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.window_maximized = True
    page.top_bar_ref = ft.Ref[TopBar]()

    def on_resize(e):
        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)
        else:
            page.update()

    def on_route_change(e: ft.RouteChangeEvent):
        route = e.route

        # Clear page state
        page.controls.clear()
        if page.views and route != page.views[-1].route and any(isinstance(c, ft.AlertDialog) for c in page.overlay):
            page.overlay.clear()
        page.snack_bar = None

        protected_routes = ["/jobcard"]
        user = page.session.get("user")
        if route in protected_routes and (not user or not user.get('emp_id')):
            page.views.clear()
            page.views.append(ft.View(
                route="/login",
                controls=[login_page(page)],
                padding=0,
                bgcolor=ft.Colors.WHITE
            ))
            page.snack_bar = ft.SnackBar(ft.Text("Session expired. Please log in again."), duration=4000)
            page.snack_bar.open = True
            page.update()
            return

        if route == "/login":
            page.views.clear()
            page.views.append(ft.View(
                route="/login",
                controls=[login_page(page)],
                padding=0,
                bgcolor=ft.Colors.WHITE
            ))
            page.update()
            return

        route_map = get_route_map(page)
        content_builder = route_map.get(route)
        if content_builder is None:
            content = ft.Text("404 - Page Not Found", color=ft.Colors.RED_600)
        else:
            content = content_builder()

        top_bar = TopBar(page, top_bar_ref=page.top_bar_ref)
        page.top_bar_ref.current = top_bar
        layout = ft.Column(
            controls=[
                ft.Container(content=top_bar.build()),
                ft.Container(content=content, expand=True, padding=20)
            ],
            expand=True,
            spacing=0
        )

        page.views.clear()
        page.views.append(ft.View(
            route=route,
            controls=[layout],
            padding=0,
            bgcolor=ft.Colors.WHITE
        ))
        page.update()

    page.on_resize = on_resize
    page.on_view_pop = view_pop
    page.on_route_change = on_route_change
    page.go("/login")

temp_dir = os.path.join(os.getcwd(), "temp")
os.makedirs(temp_dir, exist_ok=True)

async def run_flet_app():
    try:
        await ft.app_async(
            target=main,
            assets_dir="assets",
            upload_dir=temp_dir,
            route_url_strategy="hash",
            #port=8000
        )
    except asyncio.CancelledError:
        pass
    except Exception:
        pass

async def main_entry():
    try:
        await run_flet_app()
    except KeyboardInterrupt:
        pass
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main_entry())
