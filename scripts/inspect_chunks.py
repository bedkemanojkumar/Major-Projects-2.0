import json

with open("../data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("Total chunks:", len(chunks))
print("\nFirst chunk:\n")
print(json.dumps(chunks[0], indent=2))