import json
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

index = faiss.read_index(
    "../data/faiss_index.index"
)

with open(
    "../data/chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

query = input("Ask a question: ")

query_embedding = model.encode(
    [query]
).astype("float32")

k = 5

distances, indices = index.search(
    query_embedding,
    k
)

print("\nTOP RESULTS\n")

for idx in indices[0]:

    print("=" * 80)

    print(
        "Scheme:",
        chunks[idx]["scheme_name"]
    )

    print()

    print(
        chunks[idx]["text"][:1000]
    )

    print("\n")