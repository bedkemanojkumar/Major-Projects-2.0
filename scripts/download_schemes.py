import requests
import json
import time

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

all_schemes = []

for start in range(0, 200, 10):   # first 200 schemes

    url = f"https://api.myscheme.gov.in/search/v6/schemes?lang=en&q=%5B%5D&keyword=&sort=&from={start}&size=10"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Failed at:", start)
        break

    data = response.json()

    items = data["data"]["hits"]["items"]

    for item in items:

        fields = item["fields"]

        scheme = {
            "scheme_name": fields.get("schemeName"),
            "ministry": fields.get("nodalMinistryName"),
            "description": fields.get("briefDescription"),
            "tags": fields.get("tags", []),
            "slug": fields.get("slug"),
            "category": fields.get("schemeCategory", []),
            "state": fields.get("beneficiaryState", [])
        }

        all_schemes.append(scheme)

    print(f"Collected {len(all_schemes)} schemes")

    time.sleep(1)

with open("raw_schemes.json", "w", encoding="utf-8") as f:
    json.dump(all_schemes, f, indent=2, ensure_ascii=False)

print("Done!")