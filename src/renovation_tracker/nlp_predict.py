# Victoria Castagnola
#
# This is a simple script to predict the category of a room using a pre-trained NLP model.
# It takes in the predicted input and returns the predicted output.
# docker file that manages dependencies and environment is needed, include instructions in readme if needed
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
from pydantic import BaseModel, EmailStr, PositiveInt
import yaml
import openai #get rid of if/when we get vcu custom llm?

# load .env from project root (adjust if needed)
load_dotenv()

# simple config: name of model and api key read from env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you prefer another model

#yaml file setup attempt xD


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

#look into changing message into yaml file
#create a pydantic model that had your model definition?
#python sdk for openai
#get it on a route

def extract_renovations(data_from_json):
#ver 0.2
#still using gpt for now until we have our own model set up

#docker compose file look into can set up db for you
#mysql docker compose setup
#look up containerizing for deployment
    messages = [
    {
        
    }
]
