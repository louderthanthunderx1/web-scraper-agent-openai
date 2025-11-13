import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.company_lookup import search_and_get_details

print(search_and_get_details("TSPACE DIGITAL"))
