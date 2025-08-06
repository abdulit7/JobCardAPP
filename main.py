import os
os.environ["FLET_SECRET_KEY"] = "mysecret123"
import flet as ft
import urllib.parse
import socket
import errno
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
            print(f"[VIEW_POP] Only one view left, staying on current route: {page.route}")
            page.update()

    def on_route_change(e: ft.RouteChangeEvent):
        route = e.route
        print(f"[ROUTING] Navigating to: {route}, session: {page.session.get('user')}, views: {len(page.views)}")

        # Clear page state
        page.controls.clear()
        if page.views and route != page.views[-1].route and any(isinstance(c, ft.AlertDialog) for c in page.overlay):
            page.overlay.clear()
        page.snack_bar = None

        protected_routes = ["/jobcard"]
        user = page.session.get("user")
        if route in protected_routes and (not user or not user.get('emp_id')):
            print(f"[ROUTING] Session invalid, redirecting to /login")
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
            print(f"[ROUTING] Unknown route: {route}")
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
print(f"Initialized TEMP_DIR: {temp_dir}, writable: {os.access(temp_dir, os.W_OK)}")

os.environ["FLET_LOG_LEVEL"] = "DEBUG"

async def run_flet_app():
    port = 8000
    fallback_ports = [8001, 8002, 8003]
    ports_tried = [port]
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                print(f"Successfully bound to port {port}")
                sock.close()
            except socket.error as e:
                print(f"Socket bind error on port {port}: {e} (errno: {e.errno})")
                sock.close()
                if e.errno == errno.EACCES:
                    print("Permission denied: Ensure the process has sufficient privileges or port is not restricted by firewall/antivirus")
                elif e.errno == errno.EADDRINUSE:
                    print(f"Port {port} is already in use. Check for other processes using 'netstat -aon | findstr :{port}'")
                if ports_tried[-1] != fallback_ports[-1]:
                    port = fallback_ports[ports_tried.index(port) + 1 if port in ports_tried else 0]
                    ports_tried.append(port)
                    print(f"Retrying with fallback port {port}")
                    continue
                else:
                    print("All fallback ports failed")
                    raise
            await ft.app_async(
                target=main,
                #view=ft.WEB_BROWSER,
                assets_dir="assets",
                upload_dir=temp_dir,
                route_url_strategy="hash",
            )
            break
        except asyncio.CancelledError:
            print("Flet app was cancelled")
            break
        except Exception as e:
            print(f"Error running Flet app on port {port}: {e}")
            if ports_tried[-1] != fallback_ports[-1]:
                port = fallback_ports[ports_tried.index(port) + 1 if port in ports_tried else 0]
                ports_tried.append(port)
                print(f"Retrying with fallback port {port}")
                continue
            else:
                print("All fallback ports failed")
                raise

async def main_entry():
    try:
        await run_flet_app()
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        print(f"Main entry error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main_entry())