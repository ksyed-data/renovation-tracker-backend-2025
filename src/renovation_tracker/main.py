from __future__ import annotations
from fastapi import FastAPI
from renovation_tracker.database import engine
import renovation_tracker.models as models
from renovation_tracker.routers import listings_router
from renovation_tracker.routers import renovations_router
from renovation_tracker.routers import photos_router
from pydantic import BaseModel
from typing import Any, Dict
from renovation_tracker.nlp_predict import extract_renovations
from sqlalchemy import inspect


class PredictRequest(BaseModel):
    description: str


class PredictResponse(BaseModel):
    result: Dict[str, Any]


api = FastAPI()
api.include_router(listings_router.router)
api.include_router(renovations_router.router)
api.include_router(photos_router.router)


def create_tables():
    models.Base.metadata.create_all(bind=engine)


inspector = inspect(engine)
tables = inspector.get_table_names
if not tables:
    create_tables


@api.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@api.post("/predict-renovations", response_model=PredictResponse)
def predict_renovations(req: PredictRequest):
    """Accepts a property description and returns structured renovation info."""
    result = extract_renovations(req.description)
    return {"result": result}
