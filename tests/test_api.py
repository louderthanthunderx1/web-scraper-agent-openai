import requests
import json

API_KEY = "YOUR_API_KEY"
juristic_id = "0105540008838"

url = f"https://openapi.dbd.go.th/api/v1/juristic_person/{juristic_id}"

headers = {
    "X-API-KEY": API_KEY
}

response = requests.get(url, headers=headers)
data = response.json()

print(json.dumps(data, indent=2, ensure_ascii=False))
