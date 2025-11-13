from playwright.sync_api import sync_playwright
import urllib.parse

def get_company_details(page, company_url):
    page.goto(company_url, timeout=30000)
    page.wait_for_load_state("networkidle")

    def safe(selector):
        loc = page.locator(selector)
        if loc.count() > 0:
            return loc.first.inner_text().strip()
        return None

    def find(label):
        loc = page.locator(f"td:has-text('{label}') + td")
        if loc.count() > 0:
            return loc.first.inner_text().strip()
        return None

    return {
        "url": company_url,
        "company_th": safe("h1.noselect"),
        "company_en": safe("h2.noselect"),
        "tax_id": find("ทะเบียน"),
        "business": find("ธุรกิจ"),
        "status": find("สถานะ"),
        "registered_date": find("จดทะเบียน"),
        "capital": find("ทุนจดทะเบียน"),
        "address": safe("table a.noselect"),
    }


def search_and_get_details(company_name: str):
    keyword = urllib.parse.quote(company_name)
    search_url = f"https://www.dataforthai.com/business/search/{keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        page.goto(search_url, timeout=30000)
        page.wait_for_load_state("networkidle")

        # ดึงทุกผลลัพธ์
        blocks = page.locator("div.resultrec").all()

        if not blocks:
            return {"error": "No results found", "search_url": search_url}

        tax_id = None
        company_url = None

        # 🔥 LOOP หาตัวแรกที่มี onclick ถูกต้อง
        for b in blocks:
            onclick_val = b.get_attribute("onclick")
            if not onclick_val:
                continue  # <-- ถ้าไม่มี onclick ให้ข้าม

            # onclick: show_company('0105540008838','ชื่อบริษัท')
            try:
                tax_id = onclick_val.split("'")[1]
                break
            except Exception:
                continue  # ถ้า parse ไม่ได้ ให้ข้ามตัวนี้

        # ถ้าหาไม่ได้เลย
        if not tax_id:
            return {
                "error": "No clickable company result found",
                "search_url": search_url,
            }

        company_url = f"https://www.dataforthai.com/company/{tax_id}/"

        # STEP 2: load detail
        details = get_company_details(page, company_url)

        browser.close()

        return {
            "query": company_name,
            "search_url": search_url,
            "company_url": company_url,
            "clicked_tax_id": tax_id,
            "details": details,
        }

