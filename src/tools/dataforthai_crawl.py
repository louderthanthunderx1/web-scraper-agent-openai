import requests
from bs4 import BeautifulSoup
from config.settings import DATAFORTHAI_REQUIRES_LOGIN


def get_session():
    """
    สร้าง session สำหรับ requests
    หมายเหตุ: DataForThai ใช้ Google OAuth login ซึ่งไม่สามารถทำได้ด้วย requests
    ถ้าต้องการ login ต้องใช้ dataforthai_playwright.py แทน
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    if DATAFORTHAI_REQUIRES_LOGIN:
        print("Warning: Login is required but dataforthai_crawl.py doesn't support Google OAuth login.")
        print("Please use dataforthai_playwright.py instead for login functionality.")
    
    return session


def crawl_dft(tax_id: str):
    url = f"https://www.dataforthai.com/company/{tax_id}/"
    session = get_session()
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # ชื่อบริษัท
    company_th = soup.select_one("h1").get_text(strip=True)
    company_en = soup.select_one("h2").get_text(strip=True)

    # ดึงตารางข้อมูลทั้งหมด
    rows = soup.select("table tr")

    data = {
        "url": url,
        "tax_id": tax_id,
        "company_th": company_th,
        "company_en": company_en
    }

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) == 2:
            label, value = cols
            data[label] = value

    return data


def crawl_dft_clean(tax_id: str):
    url = f"https://www.dataforthai.com/company/{tax_id}/"
    session = get_session()
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # -------------------------
    # COMPANY NAME
    # -------------------------
    company_th = soup.select_one("h1").get_text(strip=True)
    company_en = soup.select_one("h2").get_text(strip=True)

    # -------------------------
    # ADDRESS (อยู่ใน a.noselect)
    # -------------------------
    address = None
    address_tag = soup.select_one("a.noselect")
    if address_tag:
        address = address_tag.get_text(" ", strip=True)

    # -------------------------
    # TABLE PARSE
    # -------------------------
    rows = soup.select("table tr")
    raw = {}
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) == 2:
            label = tds[0].get_text(strip=True)
            value = tds[1].get_text(" ", strip=True)
            raw[label] = value

    # -------------------------
    # LABEL MAPPING
    # -------------------------
    mapping = {
        "สถานะ": "status",
        "จดทะเบียน": "registered_date",
        "วันที่จดทะเบียน": "registered_date",
        "เลขทะเบียน": "tax_id",
        "ทะเบียน": "tax_id",
        "ทุนจดทะเบียน": "capital",
        "ประกอบธุรกิจ": "business_raw",
        "ธุรกิจ": "business_raw",
    }

    data = {
        "url": url,
        "tax_id": tax_id,
        "company_th": company_th,
        "company_en": company_en,
        "address": address,
    }

    for label, value in raw.items():
        if label in mapping:
            data[mapping[label]] = value

    # -------------------------
    # BUSINESS BLOCK EXTRACT
    # -------------------------
    if "business_raw" in data:
        txt = data["business_raw"]

        business = txt.split("หมวดธุรกิจ")[0].strip()

        category = None
        if "หมวดธุรกิจ" in txt:
            category = txt.split("หมวดธุรกิจ :")[1].split("ธุรกิจที่ส่งงบ")[0].strip()

        business_latest = None
        if "ธุรกิจที่ส่งงบการเงินล่าสุด" in txt:
            business_latest = txt.split("ธุรกิจที่ส่งงบการเงินล่าสุด")[-1].strip()

        data["business"] = business
        data["category"] = category
        data["business_latest"] = business_latest

        del data["business_raw"]

    return data