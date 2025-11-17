from playwright.sync_api import sync_playwright
import urllib.parse
from tools.dataforthai_crawl import crawl_dft_clean
from difflib import SequenceMatcher


def similarity_score(a: str, b: str) -> float:
    """คำนวณความคล้ายคลึงระหว่าง 2 strings (0-1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


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

        # ดึงผลลัพธ์ทั้งหมดพร้อมชื่อและ tax_id
        candidates = []
        for b in blocks:
            onclick_val = b.get_attribute("onclick")
            if not onclick_val:
                continue

            try:
                # onclick: show_company('0105540008838','ชื่อบริษัท')
                parts = onclick_val.split("'")
                tax_id = parts[1] if len(parts) > 1 else None
                company_name_in_result = parts[3] if len(parts) > 3 else ""
                
                if not tax_id:
                    continue
                
                # ดึงชื่อบริษัทจากหน้าเว็บ (ลองหลายวิธี)
                try:
                    # ลองหาจาก text ใน block
                    block_text = b.inner_text().strip()
                    if block_text:
                        # หา text ที่ไม่ใช่ tax_id และไม่ใช่ whitespace
                        lines = [line.strip() for line in block_text.split('\n') if line.strip()]
                        for line in lines:
                            if line and line != tax_id and len(line) > 3:
                                company_name_in_result = line
                                break
                except Exception:
                    pass
                
                # ถ้ายังไม่มีชื่อ ให้ใช้จาก onclick parameter
                if not company_name_in_result:
                    company_name_in_result = tax_id  # fallback

                candidates.append({
                    "tax_id": tax_id,
                    "company_name": company_name_in_result,
                    "similarity": similarity_score(company_name, company_name_in_result)
                })
            except Exception:
                continue

        browser.close()

        if not candidates:
            return {
                "error": "No clickable company result found",
                "search_url": search_url,
            }

        # เรียงตาม similarity score (สูงสุดก่อน)
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        
        # เลือกตัวที่ similarity สูงสุด
        selected = candidates[0]
        tax_id = selected["tax_id"]
        company_url = f"https://www.dataforthai.com/company/{tax_id}/"

        # ใช้ crawl_dft_clean เพื่อให้ได้ข้อมูลเท่ากับ search ด้วย tax_id
        details = crawl_dft_clean(tax_id=tax_id)

        # สร้าง response พื้นฐาน
        result = {
            "query": company_name,
            "search_url": search_url,
            "company_url": company_url,
            "clicked_tax_id": tax_id,
            "matched_company_name": selected["company_name"],
            "similarity_score": round(selected["similarity"], 3),
            **details,  # รวมข้อมูลทั้งหมดจาก crawl_dft_clean เข้าไปใน response
        }

        # ถ้ามีหลายตัว ให้เพิ่มข้อมูล candidates ไว้ด้วย
        if len(candidates) > 1:
            result["multiple_results"] = True
            result["total_found"] = len(candidates)
            result["other_candidates"] = [
                {
                    "tax_id": c["tax_id"],
                    "company_name": c["company_name"],
                    "similarity_score": round(c["similarity"], 3),
                    "url": f"https://www.dataforthai.com/company/{c['tax_id']}/"
                }
                for c in candidates[1:6]  # แสดงอีก 5 ตัวรอง (ไม่รวมตัวแรกที่เลือกแล้ว)
            ]
            result["note"] = f"Found {len(candidates)} results. Selected the most similar match (similarity: {result['similarity_score']}). Other candidates available in 'other_candidates' field."

        return result

