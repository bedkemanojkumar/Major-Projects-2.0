import json

with open("../data/schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

print(type(schemes))
print("Total records:", len(schemes))

print("\nFirst record:")
print(json.dumps(schemes[0], indent=2)[:3000])
