"""Chụp màn hình tab Thống kê trên trang Admin."""
from playwright.sync_api import sync_playwright
import time, os

URL = "http://localhost:8501"
OUT = "tools/screenshot_stats_tab.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    print("Dang mo trang admin...")
    page.goto(URL, wait_until="networkidle", timeout=30000)
    time.sleep(3)

    # Chup toan trang ban dau
    page.screenshot(path="tools/screenshot_home.png", full_page=False)
    print("Da chup: screenshot_home.png")

    # Tim sidebar de chon Admin
    # Streamlit sidebar navigation
    try:
        # Tim link "Admin" hoac "Quan tri" trong sidebar
        admin_links = page.locator("text=Admin").all()
        print(f"Tim thay {len(admin_links)} link co chu 'Admin'")

        # Thu click vao muc sidebar
        sidebar = page.locator("[data-testid='stSidebar']")
        sidebar_text = sidebar.inner_text() if sidebar.count() > 0 else "N/A"
        print(f"Sidebar text (100 chars): {sidebar_text[:200]}")

        # Chup sidebar
        if sidebar.count() > 0:
            sidebar.screenshot(path="tools/screenshot_sidebar.png")
            print("Da chup sidebar")

    except Exception as e:
        print(f"Loi sidebar: {e}")

    # Thu navigate thang den admin page neu co
    try:
        page.goto(URL, wait_until="networkidle", timeout=20000)
        time.sleep(2)

        # Tim tat ca cac selectbox, radio va link
        all_text = page.locator("body").inner_text()[:500]
        print(f"Body text (500 chars): {all_text}")

    except Exception as e:
        print(f"Loi navigate: {e}")

    # Chup toan trang
    page.screenshot(path=OUT, full_page=True)
    print(f"Da chup toan trang: {OUT}")

    browser.close()
    print("Xong!")
