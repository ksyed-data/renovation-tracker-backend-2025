# Victoria Castagnola
#
# This is a simple script to predict the category of a room using a pre-trained NLP model.
# It takes in the predicted input and returns the predicted output.
# docker file that manages dependencies and environment is needed, include instructions in readme if needed
# use virtual environment if needed click the bottom part where it says the number
"""nlp_predict -- ML-based extractor for renovated parts of a property."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, PositiveInt  # look up how to do this
import yaml
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL", "gpt-4o-mini"
)  # change if you prefer another model


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


# still kind of lame but to be honest i have been focusing on helper functions i might actually keep once vm is up and running
# create a pydantic model that had your model definition?
# python sdk for openai
# get it on a route


def extract_renovations(description: str) -> RenovationPrediction:
    # ver 0.2
    # still using gpt for now until we have our own model set up

    # docker compose file look into can set up db for you
    # mysql docker compose setup
    # look up containerizing for deployment
    messages = [{}]


class RenovationPrediction(BaseModel):
    bedroom: bool = False
    kitchen: bool = False
    living_room: bool = False
    bathroom: bool = False
    basement: bool = False
