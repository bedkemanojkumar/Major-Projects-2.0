import json
import re

with open(
    "../data/documents.json",
    "r",
    encoding="utf-8"
) as f:
    docs = json.load(f)

cleaned = []

for doc in docs:

    text = doc["text"]

    text = re.sub(r"<br>", " ", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)

    doc["text"] = text.strip()

    cleaned.append(doc)

with open(
    "../data/clean_documents.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        cleaned,
        f,
        indent=2,
        ensure_ascii=False
    )

print("Cleaned", len(cleaned), "documents")