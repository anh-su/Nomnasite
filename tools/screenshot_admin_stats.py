from playwright.sync_api import sync_playwright
import time

BASE        = "http://localhost:8501"
ADMIN_EMAIL = "mrcauut007@gmail.com"
ADMIN_NAME  = "Admin"
ADMIN_URL   = f"{BASE}/?user={ADMIN_EMAIL}&name={ADMIN_NAME}&page=admin"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 2000})

    page.goto(ADMIN_URL, wait_until="networkidle", timeout=30000)
    time.sleep(7)  # cho Streamlit reload code moi

    # Chup tab Nguoi dung
    users_tab = page.locator("button[role='tab']:has-text('Người dùng')")
    if users_tab.count() > 0:
        users_tab.first.click()
        time.sleep(3)
        page.screenshot(path="tools/ss_users_tab.png", full_page=False)
        print("Da chup tab Nguoi dung")

    browser.close()
