import os
import sys

# Add project root to Python path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

from src.tools.dataforthai_playwright import search_company_by_tax_id_playwright, TaxIDInput

if __name__ == "__main__":
    payload = TaxIDInput(tax_id="0105540008838")
    result = search_company_by_tax_id_playwright(payload)
    print(result)
