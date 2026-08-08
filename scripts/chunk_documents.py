import json

CHUNK_SIZE = 500

with open(
    "../data/clean_documents.json",
    "r",
    encoding="utf-8"
) as f:
    docs = json.load(f)

chunks = []

for doc in docs:

    text = doc["text"]

    words = text.split()

    for i in range(
        0,
        len(words),
        CHUNK_SIZE
    ):

        chunk = " ".join(
            words[i:i + CHUNK_SIZE]
        )

        chunks.append(
            {
                "scheme_name":
                    doc["metadata"]["scheme_name"],

                "slug":
                    doc["metadata"]["slug"],

                "text":
                    chunk
            }
        )

with open(
    "../data/chunks.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        chunks,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    "Created",
    len(chunks),
    "chunks"
)