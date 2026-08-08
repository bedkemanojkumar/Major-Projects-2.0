import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from bm25_retriever import bm25_search


_REPO_ROOT = Path(__file__).resolve().parent
_CHUNKS_PATH = _REPO_ROOT / "data" / "chunks.json"
_FAISS_INDEX_PATH = _REPO_ROOT / "data" / "faiss_index.index"


def _load_chunks():
    with _CHUNKS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# Load chunks (shared with retrieval)
chunks: List[Dict[str, Any]] = _load_chunks()


# Embedding model (must match app.py behavior)
_embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def faiss_search(query: str, top_k: int = 5) -> tuple[list[dict[str, Any]], list[float]]:
    """Return FAISS top-k chunks and their similarity scores.

    Similarity score is taken directly from FAISS output (_distances) which
    corresponds to inner product on normalized vectors.
    """

    index = faiss.read_index(str(_FAISS_INDEX_PATH))

    query_embedding = _embed_model.encode(
        [query],
        convert_to_numpy=True,
    )
    query_embedding = np.array(query_embedding, dtype=np.float32)
    faiss.normalize_L2(query_embedding)

    # FAISS index returns distances + indices
    distances, indices = index.search(query_embedding, top_k)

    results: list[dict[str, Any]] = []
    scores: list[float] = []
    for dist, idx in zip(distances[0].tolist(), indices[0].tolist()):
        if 0 <= idx < len(chunks):
            results.append(chunks[idx])
            scores.append(float(dist))

    return results, scores





def hybrid_search(
    query: str,
    candidate_chunks: List[Dict[str, Any]] | None = None,
    top_k: int = 5,
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    """Hybrid search (FAISS semantic + BM25 lexical).

    If candidate_chunks is provided, both retrieval steps are restricted to those chunks.
    """

    metadata: List[Dict[str, Any]] = []

    # -------------------------
    # Global behavior (unchanged)
    # -------------------------
    if candidate_chunks is None:

        faiss_results, faiss_scores = faiss_search(
            query,
            top_k=top_k,
        )

        bm25_results = bm25_search(
            query,
            top_k=top_k,
        )




        combined = (
            faiss_results + bm25_results
        )

        unique: List[Dict[str, Any]] = []
        seen = set()

        for chunk in combined:
            text = chunk.get("text", "")
            if text and text not in seen:
                seen.add(text)
                unique.append(chunk)
            elif not text:
                # Skip empty text chunks to avoid collapsing unrelated empty entries.
                continue

        # Attach retrieval metadata to each returned chunk (without changing selection order)

        final_results = unique[:top_k]

        faiss_map = {r.get("text"): s for r, s in zip(faiss_results, faiss_scores)}

        # Build BM25 score map for the returned BM25 chunks.

        # We intentionally do NOT change retrieval selection logic.
        # We only compute scores for the exact returned chunk texts.
        from rank_bm25 import BM25Okapi

        all_chunk_texts = [c.get("text", "") for c in chunks]
        tokenized_chunks = [t.lower().split() for t in all_chunk_texts]
        bm25_all = BM25Okapi(tokenized_chunks)

        query_tokens = query.lower().split()
        bm25_all_scores = bm25_all.get_scores(query_tokens)

        bm25_score_map: dict[str, float] = {}
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if text in {r.get("text", "") for r in bm25_results}:
                bm25_score_map[text] = float(bm25_all_scores[i])

        rank = 1
        for chunk in final_results:
            text = chunk.get("text", "")
            scheme_name = chunk.get("scheme_name")

            if text in faiss_map:
                retrieval_method = "FAISS"
                similarity_score = faiss_map.get(text)
                bm25_score = None
            elif text in bm25_score_map:
                retrieval_method = "BM25"
                similarity_score = None
                bm25_score = bm25_score_map.get(text)
            else:
                retrieval_method = "Hybrid"
                similarity_score = None
                bm25_score = None


            reason: list[str] = []
            if bm25_score is not None and bm25_score > 0:
                reason.append("Matched query keywords")
            if similarity_score is not None and similarity_score > 0.50:
                reason.append("High semantic similarity")
            # Global mode: do NOT add "Matched metadata filter".


            metadata.append(
                {
                    "text": text,
                    "scheme_name": scheme_name,
                    "retrieval_method": retrieval_method,
                    "rank": rank,
                    "similarity_score": similarity_score,
                    "bm25_score": bm25_score,
                    "reason": reason,
                }
            )
            rank += 1

        print("\n========== RETRIEVAL METADATA ==========")
        for m in metadata:
            print(m)
        print("=======================================\n")

        return final_results, metadata



    # -------------------------

    # Candidate-chunk constrained retrieval
    # -------------------------
    from rank_bm25 import BM25Okapi

    # Build candidate-local BM25 index
    candidate_texts = [c.get("text", "") for c in candidate_chunks]
    tokenized_candidate_texts = [t.lower().split() for t in candidate_texts]
    bm25_local = BM25Okapi(tokenized_candidate_texts)

    query_tokens = query.lower().split()
    bm25_scores = bm25_local.get_scores(query_tokens)
    top_bm25_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True,
    )[:top_k]

    bm25_results = [candidate_chunks[i] for i in top_bm25_indices]

    # Compute embeddings only for candidate chunks and run FAISS search over them.
    candidate_embeddings = _embed_model.encode(
        candidate_texts,
        convert_to_numpy=True,
    )
    candidate_embeddings = np.array(candidate_embeddings, dtype=np.float32)
    faiss.normalize_L2(candidate_embeddings)

    # Build a temporary FAISS index (inner product on normalized vectors == cosine similarity)
    dim = candidate_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(candidate_embeddings)

    query_embedding = _embed_model.encode(
        [query],
        convert_to_numpy=True,
    )
    query_embedding = np.array(query_embedding, dtype=np.float32)
    faiss.normalize_L2(query_embedding)

    _distances, indices = index.search(query_embedding, top_k)
    faiss_results = [candidate_chunks[i] for i in indices[0].tolist() if 0 <= i < len(candidate_chunks)]

    combined = faiss_results + bm25_results


    # Merge + deduplicate by chunk text
    unique: List[Dict[str, Any]] = []
    seen = set()
    for chunk in combined:
        text = chunk.get("text", "")
        if text and text not in seen:
            seen.add(text)
            # Preserve original chunk fields so downstream UI can access retrieval metadata.
            # NOTE: The metadata fields are attached later when building `metadata`.
            # Here we only avoid dropping existing chunk fields.
            unique.append(chunk)
        elif not text:
            continue

    final_results = unique[:top_k]


    # Build BM25 score map (same scores already computed above for candidate mode)
    bm25_score_map: dict[str, float] = {}
    for idx in top_bm25_indices:
        text = candidate_chunks[idx].get("text", "")
        bm25_score_map[text] = float(bm25_scores[idx])

    # Similarity score map from FAISS restricted search
    faiss_score_map: dict[str, float] = {}
    for local_rank, idx in enumerate(indices[0].tolist()):
        if 0 <= idx < len(candidate_chunks):
            text = candidate_chunks[idx].get("text", "")
            # _distances for candidate-mode FAISS are returned by index.search
            faiss_score_map[text] = float(_distances[0][local_rank])

    metadata = []
    rank = 1
    for chunk in final_results:
        text = chunk.get("text", "")
        scheme_name = chunk.get("scheme_name")

        if text in faiss_score_map:
            retrieval_method = "FAISS"
            similarity_score = faiss_score_map.get(text)
            bm25_score = bm25_score_map.get(text)
        elif text in bm25_score_map:
            retrieval_method = "BM25"
            similarity_score = None
            bm25_score = bm25_score_map.get(text)
        else:
            retrieval_method = "Hybrid"
            similarity_score = None
            bm25_score = None

        # Requirement: if unavailable, set to None
        if retrieval_method == "FAISS" and bm25_score is None:
            bm25_score = None

        reason: list[str] = []
        if bm25_score is not None and bm25_score > 0:
            reason.append("Matched query keywords")
        if similarity_score is not None and similarity_score > 0.50:
            reason.append("High semantic similarity")
        # Candidate-chunk constrained retrieval is active in this branch.
        reason.append("Matched metadata filter")

        metadata.append(
            {
                "text": text,
                "scheme_name": scheme_name,
                "retrieval_method": retrieval_method,
                "rank": rank,
                "similarity_score": similarity_score,
                "bm25_score": bm25_score,
                "reason": reason,
            }
        )
        rank += 1

    return final_results, metadata




