import json

with open(
    "enriched_schemes.json",
    "r",
    encoding="utf-8"
) as f:
    schemes = json.load(f)

for s in schemes:

    if not s["benefits"].strip():

        print("\nMissing Benefits:")
        print(s["scheme_name"])
        print("Slug:", s["slug"])

        break