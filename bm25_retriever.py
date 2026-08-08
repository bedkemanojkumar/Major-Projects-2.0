import json
from pathlib import Path

from rank_bm25 import BM25Okapi


def _load_chunks(chunks_path: Path):
    with chunks_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Load the same chunks used by the FAISS retriever.
# data/chunks.json is produced by scripts/chunk_documents.py
_REPO_ROOT = Path(__file__).resolve().parent
_CHUNKS_PATH = _REPO_ROOT / "data" / "chunks.json"

chunk_texts_chunks = _load_chunks(_CHUNKS_PATH)
chunks = chunk_texts_chunks

chunk_texts = [c.get("text", "") for c in chunks]

# Build BM25 index
# NOTE: keep this structure aligned with the requirements.
tokenized_chunks = [
    chunk.lower().split()
    for chunk in chunk_texts
]

bm25 = BM25Okapi(tokenized_chunks)


def bm25_search(
    query,
    top_k=5
):
    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = [
        chunks[i]
        for i in top_indices
    ]



    return results


if __name__ == "__main__":
    results = bm25_search(
        "scholarship for students",
        top_k=5
    )

    for r in results:
        print(r["text"][:200])

