import json
import faiss
import numpy as np

with open("../data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

index = faiss.read_index("../data/faiss_index.index")

print("Chunks:", len(chunks))
print("FAISS vectors:", index.ntotal)