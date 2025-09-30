# Victoria Castagnola
#
# This is a simple script to predict the category of a room using a pre-trained NLP model.
# It takes in the predicted input and returns the predicted output.
# docker file that manages dependencies and environment is needed, include instructions in readme if needed
#Tools needed: yolo, darknet, potentially other NLP libraries
#use virtual environment if needed click the bottom part where it says the number
"""nlp_predict -- simple, rule-based extractor for renovated parts of a property.

This module provides a lightweight `extract_renovations(text)` function that scans
property descriptions for renovation mentions and returns a structured object
describing which parts were renovated, details, and a simple confidence score.

The implementation is intentionally rule-based (keyword + sentence extraction)
so it works without any heavy ML dependencies and is easy to extend.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple
from datetime import datetime

RENOVATION_CATEGORIES: Dict[str, List[str]] = {
    "kitchen": ["kitchen", "cabinets", "countertop", "countertops", "island"],
    "bathroom": ["bathroom", "bath", "shower", "vanity", "toilet"],
    "roof": ["roof", "re-roof", "re roof", "shingles"],
    "windows": ["window", "windows", "skylight", "double pane", "double-pane"],
    "flooring": ["floor", "flooring", "hardwood", "laminate", "tile", "carpet"],
    "plumbing": ["plumb", "plumbing", "pipes", "drain"],
    "electrical": ["electrical", "wiring", "wires", "outlets", "panel"],
    "hvac": ["hvac", "heating", "air conditioning", "ac", "furnace", "boiler"],
    "exterior": ["exterior", "siding", "painted exterior", "facade", "façade"],
    "basement": ["basement", "finished basement", "unfinished basement"],
    "landscaping": ["landscape", "landscaping", "yard", "garden", "fence"],
    "doors": ["door", "doors", "front door", "storm door"],
    "gutters": ["gutter", "gutters"],
    "foundation": ["foundation", "footings", "crawl space"],
    "attic": ["attic", "insulation"],
}

STRONG_VERBS = ["renovated", "remodeled", "rebuilt", "replaced", "installed", "added", "refinished", "gut rehab", "gut-rehab"]
MEDIUM_VERBS = ["updated", "updated", "refreshed", "upgraded", "modernized", "altered"]


def _find_sentences_with_keywords(text: str, keywords: List[str]) -> List[str]:
    text_lower = text.lower()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    matches: List[str] = []
    for s in sentences:
        s_l = s.lower()
        for kw in keywords:
            if kw in s_l:
                matches.append(s.strip())
                break
    return matches


def _estimate_confidence(sentence: str) -> float:
    s = sentence.lower()
    for strong in STRONG_VERBS:
        if strong in s:
            return 0.92
    for med in MEDIUM_VERBS:
        if med in s:
            return 0.75
    # weak signals like "painted" or "new" alone are lower
    if "new" in s or "brand new" in s:
        return 0.85
    return 0.6


def extract_renovations(text: str) -> Dict[str, object]:
    """Extract renovation mentions from a property description.

    Returns a dictionary with:
      - items: list of {name, renovated(bool), details(list[str]), confidence(float)}
      - summary: list of names detected
      - raw_text: original text
      - generated_at: ISO timestamp
    """
    if not text or not text.strip():
        return {
            "items": [],
            "summary": [],
            "raw_text": text,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    items = []
    detected = []

    for name, keywords in RENOVATION_CATEGORIES.items():
        sentences = _find_sentences_with_keywords(text, keywords + [name])
        if sentences:
            # dedupe and keep up to 3 details
            uniq = []
            for s in sentences:
                if s not in uniq:
                    uniq.append(s)
                if len(uniq) >= 3:
                    break
            confidences = [_estimate_confidence(s) for s in uniq]
            confidence = max(confidences) if confidences else 0.6
            items.append({
                "name": name,
                "renovated": True,
                "details": uniq,
                "confidence": round(confidence, 2),
            })
            detected.append(name)
        else:
            items.append({
                "name": name,
                "renovated": False,
                "details": [],
                "confidence": 0.0,
            })

    result = {
        "items": items,
        "summary": detected,
        "raw_text": text,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    return result


if __name__ == "__main__":
    # quick manual smoke test
    sample = (
        "The kitchen was completely renovated in 2022 with new cabinets and countertops. "
        "Bathrooms were updated, the roof was replaced last year and new windows were installed."
    )
    import json

    print(json.dumps(extract_renovations(sample), indent=2))
