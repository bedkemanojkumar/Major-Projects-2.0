import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

url = "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug=sui&lang=en"

data = requests.get(url, headers=headers).json()

print("\nSCHEMECONTENT KEYS:")
print(data["data"]["en"]["schemeContent"].keys())

print("\nELIGIBILITY KEYS:")
print(data["data"]["en"]["eligibilityCriteria"].keys())