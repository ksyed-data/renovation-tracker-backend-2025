from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict

from renovation_tracker.nlp_predict import extract_renovations


class PredictRequest(BaseModel):
    description: str


class PredictResponse(BaseModel):
    result: Dict[str, Any]


app = FastAPI(title="Renovation Tracker API")


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@app.post("/predict-renovations", response_model=PredictResponse)
def predict_renovations(req: PredictRequest):
    """Accepts a property description and returns structured renovation info."""
    result = extract_renovations(req.description)
    return {"result": result}


def main():
    print("This module exposes a FastAPI app. Run with: uvicorn renovation_tracker.main:app --reload")


if __name__ == "__main__":
    main()
