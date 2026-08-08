import requests
import json

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

url = "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug=rmewf&lang=en"

r = requests.get(url, headers=headers)

data = r.json()["data"]["en"]

print("\nSCHEMECONTENT KEYS:")
print(data["schemeContent"].keys())

print("\nFULL SCHEMECONTENT:")
print(
    json.dumps(
        data["schemeContent"],
        indent=2,
        ensure_ascii=False
    )
)