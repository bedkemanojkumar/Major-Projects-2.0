import json

with open(
    "../data/chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

count = 0

for i, chunk in enumerate(chunks):

    if chunk["scheme_name"] == "Stand-Up India":

        count += 1

        print("\nFOUND at index:", i)

        print("\nScheme Name:")
        print(chunk["scheme_name"])

        print("\nChunk Preview:")
        print(chunk["text"][:500])

        print("\n" + "=" * 80)

print("\nTotal Stand-Up India chunks found:", count)