import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rich import print
import json
from src.tools.dataforthai_claw import crawl_dft, crawl_dft_clean

result = crawl_dft_clean("0105540008838")
print(json.dumps(result, indent=4, ensure_ascii=False))
