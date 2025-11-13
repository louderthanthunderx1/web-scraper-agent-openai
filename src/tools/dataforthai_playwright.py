from playwright.sync_api import sync_playwright
from pydantic import BaseModel
import time
import re


class TaxIDInput(BaseModel):
    tax_id: str


def search_company_by_tax_id_playwright(data: TaxIDInput):
    url = f"https://www.dataforthai.com/company/{data.tax_id}/"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )

        page = browser.new_page(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )

        # -------------------------
        # 1) Remove webdriver flag
        # -------------------------
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
        """)

        # -------------------------
        # 2) Fake chrome.runtime
        # -------------------------
        page.add_init_script("""
            window.chrome = { runtime: {} };
        """)

        # -------------------------
        # 3) Fake permissions
        # -------------------------
        page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );
        """)

        # -------------------------
        # 4) Fake plugins + languages
        # -------------------------
        page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1,2,3],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['th-TH', 'th', 'en-US']
            });
        """)

        # -------------------------
        # เข้าเว็บ
        # -------------------------
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(3)

        # optional reload
        if "เลือกประเภท" in page.inner_text("body"):
            page.reload()
            time.sleep(3)

        # ----- SAFE -----
        def safe(sel):
            try:
                el = page.locator(sel)
                if el.count():
                    return el.first.inner_text().strip()
            except:
                pass

        def find(label):
            try:
                row = page.locator(f"tr:has(td:has-text('{label}')) td:nth-child(2)")
                if row.count():
                    return row.first.inner_text().strip()
            except:
                pass

        # business
        def extract_business():
            try:
                cell = page.locator("tr:has(td:has-text('ธุรกิจ')) td:nth-child(2)").first
                html = cell.inner_html()
                plain = re.sub("<.*?>", "", html)

                business = plain.split("หมวดธุรกิจ")[0].strip()
                category = None
                business_latest = None

                if "หมวดธุรกิจ" in plain:
                    category = plain.split("หมวดธุรกิจ")[1].split("\n")[0].strip()
                if "ธุรกิจที่ส่งงบการเงินล่าสุด" in plain:
                    business_latest = plain.split("ธุรกิจที่ส่งงบการเงินล่าสุด")[-1].strip()

                return business, category, business_latest

            except:
                return None, None, None

        business, category, business_latest = extract_business()

        result = {
            "url": url,
            "tax_id": data.tax_id,
            "company_th": safe("h1"),
            "company_en": safe("h2"),
            "business": business,
            "category": category,
            "business_latest": business_latest,
            "status": find("สถานะ"),
            "registered_date": find("จดทะเบียน"),
            "updated_capital": find("ทุนจดทะเบียน"),
            "initial_capital": find("ทุนจดทะเบียนแรกตั้ง"),
            "capital_change_date": find("วันที่เปลี่ยนแปลงทุนล่าสุด"),
            "address": find("ที่ตั้งบริษัท"),
            "branch_count": find("จำนวนสาขา"),
        }

        browser.close()
        return result
