"""Temporary tests for Phase 5: metadata_filter utilities.

Run:
    python scripts/test_metadata_filter.py

This file is only for validating the Phase 5 utilities locally.
"""

from __future__ import annotations

import sys
import os

# Ensure repo root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from metadata_filter import extract_tags, filter_schemes_by_tags



def run():
    # Minimal synthetic dataset
    schemes = [
        {
            "scheme_name": "A",
            "tags": ["Widow", "Medical"],
        },
        {
            "scheme_name": "B",
            "tags": ["Loan", "Finance"],
        },
        {
            "scheme_name": "C",
            "tags": [],
        },
        {
            "scheme_name": "D",
            "tags": ["Scholarship", "Student"],
        },
    ]

    q1 = "I am a widow and need medical help"
    tags1 = extract_tags(q1)
    filtered1 = filter_schemes_by_tags(schemes, tags1)

    assert "Widow" in tags1
    assert len(filtered1) == 1
    assert filtered1[0]["scheme_name"] == "A"

    q2 = "Looking for scholarship for student"
    tags2 = extract_tags(q2)
    filtered2 = filter_schemes_by_tags(schemes, tags2)

    assert "Scholarship" in tags2
    assert "Student" in tags2
    assert len(filtered2) == 1
    assert filtered2[0]["scheme_name"] == "D"

    q3 = "employment loan"
    tags3 = extract_tags(q3)
    filtered3 = filter_schemes_by_tags(schemes, tags3)

    assert "Loan" in tags3
    assert "Employment" in tags3
    # Overlap: scheme B has Loan; none has Employment
    assert len(filtered3) == 1
    assert filtered3[0]["scheme_name"] == "B"

    q4 = "nothing relevant"
    tags4 = extract_tags(q4)
    filtered4 = filter_schemes_by_tags(schemes, tags4)

    assert tags4 == []
    assert filtered4 == []

    print("metadata_filter tests passed")


if __name__ == "__main__":
    run()

