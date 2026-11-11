"""
Script de verificación visual y funcional con Playwright (SATA-UNSA).
Comprueba:
1. Pantalla de login: ausencia total de barra blanca vacía, carga de escudo y banners.
2. Reapertura del menú lateral (sidebar collapse / expand) en escritorio y móvil (~390px).
3. Autenticación y navegación del estudiante demo.
4. Cierre de sesión limpio.
"""
import os
import subprocess
import sys
import time

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = r"D:\ms-playwright"

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def test_ui_and_capture():
    # Iniciar Streamlit en proceso background
    print("[*] Iniciando servidor Streamlit en puerto 8501...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        time.sleep(5)  # Esperar que Streamlit inicialice
        with sync_playwright() as p:
            print("[*] Lanzando Chromium desde D:\\ms-playwright...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            print("[*] Navegando a http://localhost:8501...")
            page.goto("http://localhost:8501", timeout=60000)
            page.wait_for_selector(".unsa-header-banner", timeout=30000)
            time.sleep(2)

            # 1. Capturar pantalla de Login After
            login_after_path = os.path.join(SCREENSHOTS_DIR, "login_after.png")
            page.screenshot(path=login_after_path, full_page=True)
            print(f"[+] Captura de pantalla de Login guardada en: {login_after_path}")

            # Verificar que no exista elemento vacío entre banner/lema y pestañas
            empty_cards = page.locator(".unsa-card:empty").count()
            print(f"[*] Contenedores .unsa-card vacíos encontrados: {empty_cards} (debe ser 0)")
            assert empty_cards == 0, "Se encontraron tarjetas vacías en el DOM"

            # 2. Entrar como Estudiante Demo
            print("[*] Haciendo clic en 'Entrar como Estudiante Demo'...")
            btn_demo = page.get_by_role("button", name="Entrar como Estudiante Demo")
            btn_demo.click()

            page.wait_for_selector("[data-testid='stSidebar']", timeout=30000)
            time.sleep(2)

            # Verificar presencia de datos del estudiante en sidebar
            assert page.locator("text=ID Criptográfico").is_visible()
            print("[+] Estudiante Demo autenticado correctamente.")

            # 3. Probar colapso y reapertura del menú lateral en escritorio
            print("[*] Probando botón de colapso de la barra lateral...")
            page.locator("[data-testid='stSidebar']").hover()
            time.sleep(0.5)
            collapse_btn = page.locator("[data-testid='stSidebarCollapseButton'] button")
            collapse_btn.click(timeout=10000)
            time.sleep(1)

            collapsed_path = os.path.join(SCREENSHOTS_DIR, "sidebar_collapsed_desktop.png")
            page.screenshot(path=collapsed_path)
            print(f"[+] Captura con sidebar colapsado: {collapsed_path}")

            # Reabrir sidebar con el botón de expansión
            print("[*] Probando reapertura con botón Expand sidebar...")
            reopen_btn = page.locator("button[aria-label='Expand sidebar']")
            assert reopen_btn.is_visible(), "El botón de reapertura del sidebar no es visible!"
            reopen_btn.click()
            time.sleep(1)

            reopened_path = os.path.join(SCREENSHOTS_DIR, "sidebar_reopened_desktop.png")
            page.screenshot(path=reopened_path)
            print(f"[+] Captura con sidebar reabierto: {reopened_path}")

            # 4. Probar en viewport móvil (~390px)
            print("[*] Probando responsividad en ancho móvil (390 x 844)...")
            page.set_viewport_size({"width": 390, "height": 844})
            time.sleep(1.5)

            mobile_path = os.path.join(SCREENSHOTS_DIR, "sidebar_mobile_390px.png")
            page.screenshot(path=mobile_path)
            print(f"[+] Captura en resolución móvil guardada en: {mobile_path}")

            # En móvil, el botón expand sidebar debe existir para abrir el drawer
            mobile_expand_btn = page.locator("button[aria-label='Expand sidebar']")
            if mobile_expand_btn.is_visible():
                mobile_expand_btn.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "sidebar_mobile_opened.png"))
                print("[+] Barra lateral expandida exitosamente en móvil.")

            # 5. Volver a tamaño normal y probar Cerrar Sesión
            page.set_viewport_size({"width": 1280, "height": 900})
            time.sleep(1)

            # Si el sidebar se cerró al pasar a móvil, reabrirlo
            if not page.locator("[data-testid='stSidebar']").is_visible():
                page.locator("button[aria-label='Expand sidebar']").click()
                time.sleep(1)

            print("[*] Probando Cerrar Sesión...")
            btn_logout = page.get_by_role("button", name="Cerrar Sesión")
            btn_logout.click()
            page.wait_for_selector(".unsa-header-banner", timeout=20000)
            time.sleep(1)
            print("[+] Cierre de sesión verificado con éxito.")

            browser.close()
            print("[+] ¡Todas las pruebas de Playwright superadas con éxito!")

    finally:
        server_process.terminate()
        server_process.wait()
        print("[*] Proceso Streamlit finalizado.")


if __name__ == "__main__":
    test_ui_and_capture()
