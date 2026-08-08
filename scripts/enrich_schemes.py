import requests
import json
import time

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.myscheme.gov.in",
    "User-Agent": "Mozilla/5.0",
    "x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
}

with open("raw_schemes.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

enriched = []

for i, scheme in enumerate(schemes):

    slug = scheme["slug"]

    url = (
        f"https://api.myscheme.gov.in/"
        f"schemes/v6/public/schemes?slug={slug}&lang=en"
    )

    try:

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print(f"Failed: {slug}")
            continue

        data = r.json()["data"]["en"]

        # -----------------------------
        # Safe ministry extraction
        # -----------------------------
        ministry = "Not Available"

        if data["basicDetails"].get("nodalMinistryName"):
            ministry = (
                data["basicDetails"]
                .get("nodalMinistryName", {})
                .get("label", "Not Available")
            )

        # -----------------------------
        # Safe application process
        # -----------------------------
        application_process = ""

        if data.get("applicationProcess"):
            application_process = (
                data["applicationProcess"][0]
                .get("process_md", "")
            )

        # -----------------------------
        # Benefits extraction
        # -----------------------------
        benefits = (
            data.get("schemeContent", {})
            .get("benefits_md", "")
        )

        if not benefits:

            benefits_list = (
                data.get("schemeContent", {})
                .get("benefits", [])
            )

            extracted = []

            for item in benefits_list:

                for child in item.get(
                    "children", []
                ):

                    text = child.get(
                        "text",
                        ""
                    )

                    if text.strip():
                        extracted.append(text)

            benefits = "\n".join(extracted)

        # -----------------------------
        # Create final record
        # -----------------------------
        record = {

            "scheme_name":
                data["basicDetails"].get(
                    "schemeName",
                    "Not Available"
                ),

            "ministry":
                ministry,

            "description":
                data.get(
                    "schemeContent",
                    {}
                ).get(
                    "detailedDescription_md",
                    ""
                ),

            "benefits":
                benefits,

            "eligibility":
                data.get(
                    "eligibilityCriteria",
                    {}
                ).get(
                    "eligibilityDescription_md",
                    ""
                ),

            "application_process":
                application_process,

            "tags":
                data["basicDetails"].get(
                    "tags",
                    []
                ),

            "slug":
                slug
        }

        enriched.append(record)

        print(
            f"{i+1}/{len(schemes)} Done: {slug}"
        )

        time.sleep(0.2)

    except Exception as e:

        print(
            f"ERROR in {slug}: {e}"
        )

        continue

with open(
    "enriched_schemes.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        enriched,
        f,
        indent=2,
        ensure_ascii=False
    )

print(
    "Saved",
    len(enriched),
    "schemes"
)