import requests
import json

url = "https://www.myscheme.gov.in/_next/data/ogqeeipEXMk71f8jfOOm1/en/schemes/rmewf.json?slug=rmewf"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("content-type"))

print(response.text[:1000])

with open("scheme_response.json", "w", encoding="utf-8") as f:
    f.write(response.text)