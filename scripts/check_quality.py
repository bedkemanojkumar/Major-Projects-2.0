import json

with open(
    "enriched_schemes.json",
    "r",
    encoding="utf-8"
) as f:
    schemes = json.load(f)

missing_desc = 0
missing_benefits = 0
missing_eligibility = 0

for s in schemes:

    if not s["description"].strip():
        missing_desc += 1

    if not s["benefits"].strip():
        missing_benefits += 1

    if not s["eligibility"].strip():
        missing_eligibility += 1

print("Total Schemes:", len(schemes))
print("Missing Description:", missing_desc)
print("Missing Benefits:", missing_benefits)
print("Missing Eligibility:", missing_eligibility)