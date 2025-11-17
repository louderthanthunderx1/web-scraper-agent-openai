# Web Scraper Agent (Python + Playwright + Clawing Beutifulsoup)

### Installation

```
Install uv
pip install uv
```

### Install dependencies
```
uv sync
หรือ
uv add -r requirements.txt
```

### Install Playwright
```
uv run playwright install
```

### Configuration

สร้างไฟล์ `.env` ใน root directory และตั้งค่าดังนี้:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# DataForThai Login Configuration (Optional)
# DataForThai ใช้ Google OAuth login
# ถ้าต้องการใช้งาน login ให้ตั้งค่าต่อไปนี้:
DATAFORTHAI_REQUIRES_LOGIN=true
# DATAFORTHAI_LOGIN_URL=https://www.dataforthai.com/login  # (optional, มี default)
# DATAFORTHAI_USE_PERSISTENT_CONTEXT=true  # เก็บ cookies ไว้ใช้ต่อ (แนะนำ)
# DATAFORTHAI_CONTEXT_DIR=.playwright-context  # directory สำหรับเก็บ cookies (optional)
```

**หมายเหตุ:** 
- DataForThai ใช้ **Google OAuth login** (ไม่ใช่ username/password)
- ถ้าไม่ตั้งค่า `DATAFORTHAI_REQUIRES_LOGIN=true` ระบบจะทำงานแบบไม่ login
- ถ้าตั้งค่าแล้ว ระบบจะเปิด browser และให้คุณ login ด้วย Google account เอง
- **แนะนำให้ตั้งค่า `DATAFORTHAI_USE_PERSISTENT_CONTEXT=true`** เพื่อเก็บ cookies ไว้ใช้ต่อ (ไม่ต้อง login ทุกครั้ง)
- Login รองรับเฉพาะ `dataforthai_playwright.py` เท่านั้น (Google OAuth ต้องใช้ browser)
- `dataforthai_crawl.py` ไม่รองรับ login (ใช้ requests ธรรมดา)