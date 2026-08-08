import json

with open("sui_full.json", "r", encoding="utf-8") as f:
    text = f.read()

keywords = [
    "faq",
    "document",
    "documents",
    "required",
    "requiredDocuments",
    "documentRequired",
    "frequently",
]

for k in keywords:
    if k.lower() in text.lower():
        print("FOUND:", k)