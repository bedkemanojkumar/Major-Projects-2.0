import json
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

with open(
    "../data/chunks.json",
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

texts = [
    chunk["text"]
    for chunk in chunks
]

embeddings = model.encode(
    texts,
    convert_to_numpy=True
)

print(
    f"Creating embeddings for {len(texts)} chunks..."
)

embeddings = model.encode(
    texts,
    show_progress_bar=True
)

embeddings = np.array(
    embeddings,
    dtype="float32"
)

faiss.normalize_L2(
    embeddings
)

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embeddings
)

faiss.write_index(
    index,
    "../data/faiss_index.index"
)

np.save(
    "../data/embeddings.npy",
    embeddings
)

print(
    "Embeddings saved."
)

print(
    "FAISS index saved."
)