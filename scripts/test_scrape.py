import requests

url = "https://www.myscheme.gov.in/search"

response = requests.get(url)

print(response.status_code)

with open("page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved")