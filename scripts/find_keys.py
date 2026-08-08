import json

with open("sui_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

found = set()

def scan(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.add(k)
            scan(v)

    elif isinstance(obj, list):
        for item in obj:
            scan(item)

scan(data)

for k in sorted(found):
    print(k)