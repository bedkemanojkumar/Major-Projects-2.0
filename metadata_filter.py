"""Utilities for Phase 5: Metadata Filtering using existing `tags`.

Dataset assumptions:
- Every scheme in the dataset already contains a `tags` field.
- We intentionally do NOT create or use `retrieval_metadata`.

This module provides:
- extract_tags(question)
- filter_schemes_by_tags(schemes, extracted_tags)

"""

from __future__ import annotations

import re
from typing import Iterable, List, Dict, Any, Set


TAG_KEYWORDS: Dict[str, str] = {
    "scholarship": "Scholarship",
    "student": "Student",
    "widow": "Widow",
    "ex-serviceman": "Ex-Servicemen",
    "farmer": "Farmer",
    "loan": "Loan",
    "health": "Health",
    "medical": "Medical",
    "employment": "Employment",
}


def _normalize_text(s: str) -> str:
    # Keep hyphens; lowercasing + whitespace normalization is enough here.
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def extract_tags(question: str) -> List[str]:
    """Return matching tags found in the query.

    Matching uses a keyword->tag mapping. For each keyword, if it appears in the
    question (case-insensitive), we include the mapped tag.

    Returns:
        List[str]: unique mapped tags in encounter order.
    """

    q = _normalize_text(question)
    if not q:
        return []

    extracted: List[str] = []
    seen: Set[str] = set()

    for keyword, mapped_tag in TAG_KEYWORDS.items():
        # Use word-boundary matching for word-like keywords.
        # For keywords with hyphens (e.g., ex-serviceman), also try boundary match.
        kw = _normalize_text(keyword)

        # Prefer whole-word / token match; fall back to substring match.
        if re.search(rf"\b{re.escape(kw)}\b", q):
            if mapped_tag not in seen:
                extracted.append(mapped_tag)
                seen.add(mapped_tag)
            continue

        if kw.replace("-", " ") in q or kw in q:
            if mapped_tag not in seen:
                extracted.append(mapped_tag)
                seen.add(mapped_tag)

    return extracted



def filter_schemes_by_tags(
    schemes: Iterable[Dict[str, Any]],
    extracted_tags: Iterable[str],
) -> List[Dict[str, Any]]:
    """Return schemes whose tags overlap with extracted tags.

    A scheme matches if ANY extracted tag appears in scheme['tags'].

    Notes:
    - Does not create/require retrieval_metadata.
    - If scheme has no tags, it will never match.
    """

    extracted_set = {t for t in (extracted_tags or []) if t}
    if not extracted_set:
        filtered: List[Dict[str, Any]] = []
        return filtered


    filtered: List[Dict[str, Any]] = []

    for scheme in schemes:
        tags = scheme.get("tags", []) or []
        # overlap check
        if any(tag in extracted_set for tag in tags):
            filtered.append(scheme)

    return filtered


