import requests
import json

url = "https://api.myscheme.gov.in/search/v6/schemes?lang=en&q=%5B%5D&keyword=&sort=&from=0&size=10"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

response = requests.get(url, headers=headers)

data = response.json()

print(type(data["data"]["hits"]))

print(json.dumps(data["data"]["hits"], indent=2)[:3000])