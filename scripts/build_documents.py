import json

with open(
    "../data/enriched_schemes.json",
    "r",
    encoding="utf-8"
) as f:
    schemes = json.load(f)

documents = []

for scheme in schemes:

    document = f"""
Scheme Name:
{scheme.get('scheme_name', '')}

Ministry:
{scheme.get('ministry', '')}

Description:
{scheme.get('description', '')}

Eligibility:
{scheme.get('eligibility', '')}

Benefits:
{scheme.get('benefits', '')}

Application Process:
{scheme.get('application_process', '')}

Tags:
{', '.join(scheme.get('tags', []))}
"""

    documents.append({
        "text": document,
        "metadata": {
            "scheme_name":
                scheme.get("scheme_name", ""),

            "slug":
                scheme.get("slug", "")
        }
    })

with open(
    "documents.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        documents,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    "Created",
    len(documents),
    "documents"
)