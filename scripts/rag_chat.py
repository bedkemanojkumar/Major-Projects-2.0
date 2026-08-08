import json
import faiss
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

# -------------------------
# Gemini Setup
# -------------------------
import os
genai.configure(api_key=os.getenv("GENAI_API_KEY"))


llm = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# -------------------------
# Load Embedding Model
# -------------------------
print("Loading embedding model...")

embed_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# -------------------------
# Load Chunks
# -------------------------
print("Loading chunks...")

with open(
    "../data/chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

# -------------------------
# Load FAISS Index
# -------------------------
print("Loading FAISS index...")

index = faiss.read_index(
    "../data/faiss_index.index"
)

print("\nCitizenRAG is Ready!")
print("Type 'exit' to stop.\n")

# -------------------------
# Chat Loop
# -------------------------
while True:

    query = input("You: ")

    if query.lower() == "exit":
        break

    # -------------------------
    # Create Query Embedding
    # -------------------------
    query_embedding = embed_model.encode(
        [query]
    )

    # -------------------------
    # Retrieve Top 3 Chunks
    # -------------------------
    distances, indices = index.search(
        np.array(
            query_embedding,
            dtype=np.float32
        ),
        3
    )

    context = ""
    sources = []

    print("\nRetrieved Sources:")

    for idx in indices[0]:

        print(
            "-",
            chunks[idx]["scheme_name"]
        )

        context += (
            chunks[idx]["text"]
            + "\n\n"
        )

        sources.append(
            chunks[idx]["scheme_name"]
        )

    # -------------------------
    # Prompt for Gemini
    # -------------------------
    prompt = f"""
You are CitizenRAG, an assistant that helps Indian citizens understand government schemes.

Use ONLY the information provided in the context below.

If the answer cannot be found in the context, say:
"I could not find sufficient information in the retrieved schemes."

Context:
{context}

Question:
{query}

Answer:
"""

    # -------------------------
    # Generate Answer
    # -------------------------
    response = llm.generate_content(
        prompt
    )

    print("\nCitizenRAG:\n")

    print(response.text)

    print("\nSources:")

    for source in set(sources):
        print("-", source)

    print("\n" + "=" * 80 + "\n")