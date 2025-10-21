# Victoria Castagnola
#
# This is a simple script to predict the category of a room using a pre-trained NLP model.
# It takes in the predicted input and returns the predicted output.
# docker file that manages dependencies and environment is needed, include instructions in readme if needed
#Tools needed: yolo, darknet, potentially other NLP libraries
#use virtual environment if needed click the bottom part where it says the number
"""nlp_predict -- ML-based extractor for renovated parts of a property.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple
from datetime import datetime
import os
import json
from dotenv import load_dotenv
import openai #get rid of if/when we get vcu custom llm?

# load .env from project root (adjust if needed)
load_dotenv()

# simple config: name of model and api key read from env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you prefer another model


#want to add more error catching and handling here!
def parse_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to fix common JSON issues
        text = re.sub(r",\s*}", "}", text)  # Remove trailing commas before }
        text = re.sub(r",\s*]", "]", text)  # Remove trailing commas before ]
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nOriginal text: {text}")

#still kind of lame but to be honest i have been focusing on helper functions i might actually keep once vm is up and running
def extract_renovations(data_from_json):
#ver 0.2
#still using gpt for now until we have our own model set up
    messages = [
    {
        "role": "system",
        "content": (
            "You are an assistant that extracts renovation information from a property description. "
            "RETURN ONLY VALID JSON (no extra text). The JSON MUST follow this schema:\n\n"
            "{\n"
            '  "items": [\n'
            "    {\n"
            '      "name": string,                # canonical category e.g. kitchen\n'
            '      "renovated": boolean,         # true if renovated\n'
            '      "details": [string],          # up to 3 example sentences/snippets\n'
            '      "confidence": number|null,    # 0.0-1.0, round to 2 decimals\n'
            '      "last_renovated_year": int|null # year if mentioned, otherwise null\n'
            "    }\n"
            "  ],\n"
            '  "summary": [string],              # list of names where renovated=true\n'
            '  "raw_text": string,               # original description\n'
            '  "generated_at": string            # ISO-8601 UTC timestamp\n'
            "}\n\n"
            "Rules:\n"
            "- Use canonical categories only. Common examples: kitchen, bathroom, roof, windows, flooring, HVAC, plumbing, electrical, exterior, landscaping, garage, basement.\n"
            "- Include at most 3 detail sentences per item.\n"
            "- If the sentence contains negation (e.g. 'not renovated', 'no', 'never'), set renovated=false for that category.\n"
            "- If the model is uncertain, set renovated=false or set confidence <= 0.6. Use higher confidence (>=0.85) for explicit verbs like 'renovated', 'replaced', 'fully remodeled'.\n"
            "- Round confidence to two decimals. If no information, return items as an empty list and summary as an empty list.\n"
            "- Do not invent years; only fill last_renovated_year when a 4-digit year is present in a matched sentence.\n"
            "- Do not include any keys outside the schema above.\n"
        ),
    },
    {
        "role": "user",
        "content": "Description:\n{description}\n\nReturn the JSON only."
    },
]
