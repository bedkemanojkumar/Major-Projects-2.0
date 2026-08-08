import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

slug = "sui"

url = f"https://api.myscheme.gov.in/schemes/v6/public/schemes?slug={slug}&lang=en"

r = requests.get(url, headers=headers)

print("Status:", r.status_code)

data = r.json()

print("\nMain Keys:")
for key in data["data"]["en"].keys():
    print(key)