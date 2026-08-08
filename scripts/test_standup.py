import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

with open("../data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

index = faiss.read_index("../data/faiss_index.index")

query = "Stand-Up India"

query_embedding = model.encode(
    [query],
    convert_to_numpy=True
)

query_embedding = np.array(
    query_embedding,
    dtype=np.float32
)

faiss.normalize_L2(query_embedding)

distances, indices = index.search(
    query_embedding,
    10
)

for rank, (idx, score) in enumerate(
    zip(indices[0], distances[0]),
    start=1
):

    print(f"\nRank {rank}")
    print("Score:", score)
    print("Scheme:", chunks[idx]["scheme_name"])