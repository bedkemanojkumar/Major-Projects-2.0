import json

with open("data/enriched_schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

with_tags = sum(
    1 for s in schemes
    if s.get("tags")
)

print("Total schemes:", len(schemes))
print("Schemes with tags:", with_tags)