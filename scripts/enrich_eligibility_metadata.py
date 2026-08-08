import json
import re
from pathlib import Path

INPUT_PATH = Path("data/enriched_schemes.json")


def _clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"<br\s*/?>", " ", str(s), flags=re.IGNORECASE)


def _lower(s: str) -> str:
    return _clean_text(s).lower()


def infer_eligibility_metadata(scheme: dict) -> dict:
    """Infer eligibility_metadata from scheme content.

    Rules implemented (heuristics):
    - Use keywords over (eligibility + description + scheme_name + tags).
    - Only set fields when strongly indicated by keyword matches.
    """

    # Source text
    parts = [
        scheme.get("scheme_name", ""),
        scheme.get("description", ""),
        scheme.get("eligibility", ""),
        " ".join(scheme.get("tags", []) or []),
    ]
    text = _lower("\n".join(parts))

    metadata: dict = {}

    def has_any(*patterns: str) -> bool:
        return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)

    # Widow
    if has_any(r"\bwidow\b", r"widowed", r"widows"):
        metadata["widow"] = True

    # Ex-serviceman
    if has_any(
        r"\bex[- ]?serviceman\b",
        r"ex serviceman",
        r"ex[- ]?servicemen",
        r"\bres serviceman\b",
        r"\besm\b",
        r"\bex[- ]?servicemen\b",
        r"ex servicemen",
        r"ex[- ]?serviceman\/widow",
    ):
        metadata["ex_serviceman"] = True

    # Student
    if has_any(r"\bstudent\b", r"\bstudents\b", r"\bstudent\/|\bstudents?\b"):
        # Avoid false positives like "distinguished" etc.
        if not has_any(r"distinguished"):
            metadata["student"] = True

    # Farmer
    if has_any(r"\bfarm(er)?\b", r"\bfarmers\b", r"krishi", r"\bcultivation\b"):
        metadata["farmer"] = True

    # Woman
    if has_any(r"\bwoman\b", r"\bwomen\b", r"\bfemale\b", r"\bmahila\b", r"\bwomen entrepreneur"):
        metadata["woman"] = True

    # Senior citizen
    if has_any(r"senior\s*citizen", r"old\s*age", r"senior\b", r"\bold\b", r"\belderly\b", r"60\s*(years|year)\b"):
        metadata["senior_citizen"] = True

    # Disability
    if has_any(
        r"divyang",
        r"\bdisab(led|ility)\b",
        r"\bpwd\b",
        r"\bperson(s)?\s+with\s+disabil",
        r"\bhandicap(pe)?rson\b",
        r"\bdisabled\b",
        r"\bdisability\b",
    ):
        metadata["disability"] = True

    # Caste (SC/ST)
    caste = None
    if has_any(r"\bsc\b", r"scheduled\s*caste", r"schedule\s*d\s*caste", r"schedule\s*d\s*caste"):
        caste = "SC"
    if has_any(r"\bst\b", r"scheduled\s*tribe", r"schedule\s*d\s*tribe"):
        caste = "ST"
    if caste:
        metadata["caste"] = caste

    # State (for the required example states; otherwise leave unset)
    # Heuristic: look for "state of X" or "resident of X".
    state = None
    # Commonly mentioned in dataset; add more if needed.
    states = [
        "assam",
        "haryana",
        "delhi",
        "madhya pradesh",
        "madhya",
        "maharashtra",
        "gujarat",
        "west bengal",
        "west bengal",
        "jharkhand",
        "nagaland",
        "sikkim",
        "himachal pradesh",
        "himachal",
        "karnataka",
        "punjab",
        "tripura",
        "uttar pradesh",
        "chhattisgarh",
        "arunachal pradesh",
        "manipur",
        "jammu and kashmir",
        "jammu",
        "kashmir",
        "odisha",
        "bihar",
    ]

    # Normalize some aliases
    alias_map = {
        "himachal": "Himachal Pradesh",
        "himachal pradesh": "Himachal Pradesh",
        "madhya": "Madhya Pradesh",
        "west bengal": "West Bengal",
        "arunachal pradesh": "Arunachal Pradesh",
        "jammu": "Jammu and Kashmir",
        "jammu and kashmir": "Jammu and Kashmir",
        "kashmir": "Jammu and Kashmir",
        "uttar pradesh": "Uttar Pradesh",
        "haryana": "Haryana",
        "delhi": "Delhi",
        "assam": "Assam",
        "bihar": "Bihar",
        "gujarat": "Gujarat",
        "maharashtra": "Maharashtra",
        "karnataka": "Karnataka",
        "punjab": "Punjab",
        "tripura": "Tripura",
        "sikkim": "Sikkim",
        "nagaland": "Nagaland",
        "manipur": "Manipur",
        "tripura": "Tripura",
        "jharkhand": "Jharkhand",
        "chhattisgarh": "Chhattisgarh",
        "odisha": "Odisha",
    }

    for st in states:
        st_l = st.lower()
        if re.search(r"\bstate\s+of\s+" + re.escape(st_l) + r"\b", text) or re.search(
            r"\bresident\s+of\s+" + re.escape(st_l) + r"\b", text
        ) or re.search(r"\bdomicile\s+of\s+" + re.escape(st_l) + r"\b", text) or re.search(
            r"\bdomicile\b.*\b" + re.escape(st_l) + r"\b", text
        ):
            state = alias_map.get(st_l, st.title())
            break

    # Fallback: detect "resident of Assam" etc without "state of"
    if not state:
        for st_l, st_name in alias_map.items():
            if re.search(r"\bresident\s+(of|in)\s+" + re.escape(st_l) + r"\b", text):
                state = st_name
                break

    if state:
        metadata["state"] = state

    return metadata


def main():
    if not INPUT_PATH.exists():
        raise SystemExit(f"Missing input file: {INPUT_PATH}")

    schemes = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    processed = 0
    generated = 0
    still_missing = 0

    for scheme in schemes:
        processed += 1
        # If already has eligibility_metadata and it's non-empty, keep as-is.
        existing = scheme.get("eligibility_metadata")
        if existing:
            continue

        inferred = infer_eligibility_metadata(scheme)
        if inferred:
            scheme["eligibility_metadata"] = inferred
            generated += 1
        else:
            still_missing += 1

    INPUT_PATH.write_text(json.dumps(schemes, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Eligibility metadata enrichment completed")
    print(f"schemes processed: {processed}")
    print(f"metadata generated: {generated}")
    print(f"schemes still missing metadata: {still_missing}")


if __name__ == "__main__":
    main()

