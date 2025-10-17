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

def extract_renovations(data_from_json):
#ver 0.1 placeholder
    messages = [
        {"role": "system", "content": "You are an expert at extracting renovation information from property descriptions."},]
