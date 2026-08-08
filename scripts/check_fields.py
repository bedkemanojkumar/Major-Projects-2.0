import json

with open(
    "../data/chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

print(
    chunks[0].keys()
)