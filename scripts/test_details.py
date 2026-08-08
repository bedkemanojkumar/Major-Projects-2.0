import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

url = "https://api.myscheme.gov.in/search/v6/schemes?slug=sui&lang=en"

r = requests.get(url, headers=headers)

data = r.json()

with open("sui_full.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved")