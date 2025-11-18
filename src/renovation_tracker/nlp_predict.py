# Victoria Castagnola
#
# This is a script that uses OpenAI model gpt-4o-mini to infer room type from a text description.11/14/25
# Will most likely add more functionality later on, including extracting renovation details.

# imports
from __future__ import annotations

import os

import openai
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

from renovation_tracker.pydantic_models.renovations import Renovation

# load environment variables from .env file
load_dotenv()

# ensure client is intialized properly
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai.api_key)
print("Client initialized:", client is not None)
with open("./src/renovation_tracker/prompt.yaml") as file:
    type_predictor = yaml.safe_load(file)


# pydantic model for renovation prediction
class RenovationPrediction(BaseModel):
    bedroom: bool = False
    kitchen: bool = False
    living_room: bool = False
    bathroom: bool = False
    basement: bool = False


def extract(description: str) -> Renovation:
    # gets response from gpt-4o-mini model and predicts room types from description
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[type_predictor["messages"]],
        text_format=RenovationPrediction,
    )
    event = response.output_parsed
    # prints out the predicted room types from the description
    print("Predicted room types from description:")
    print(event)
