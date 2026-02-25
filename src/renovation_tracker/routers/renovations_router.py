from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from renovation_tracker.pydantic_models.renovations import (
    Renovation,
    RenovationRead,
    RenovationUpdate,
    RenovationCreate,
)
import renovation_tracker.models as models
from renovation_tracker.database import get_db, Session
import yaml
from dotenv import load_dotenv
import openai
import os
from pathlib import Path


router = APIRouter(prefix="/renovations")
db_dependency = Annotated[Session, Depends(get_db)]
# load environment variables from .env file
load_dotenv()

# ensure client is intialized properly
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai.api_key)
yaml_path = Path(__file__).parent.parent / "prompt.yaml"
with open(yaml_path) as file:
    type_predictor = yaml.safe_load(file)


# CREATE Renovation with custom inputs
@router.post("/", response_model=RenovationRead, status_code=status.HTTP_201_CREATED)
async def create_renovation(
    renovation: Renovation, db: Annotated[Session, Depends(get_db)]
):
    db_renovation = models.Renovations(**renovation.model_dump)
    return renovation_helper(db_renovation, db)


# CREATE Renovation with listing id
@router.post(
    "/{listing_id}/create",
    response_model=RenovationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_renovation_id(
    listing_id: int, db: Annotated[Session, Depends(get_db)]
):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    renovation = extract(listing.description, listing_id)
    db_renovation = models.Renovations(**renovation.model_dump())
    return renovation_helper(db_renovation, db)


# READ renovations for given listing id
@router.get("/{listing_id}/read", response_model=list[RenovationRead])
async def get_renovation(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    # If no renovations found create new renovation
    if not listing.renovations:
        renovation = extract(listing.description, listing_id)
        db_renovation = models.Renovations(**renovation.model_dump())
        renovation_helper(db_renovation, db)
        db.refresh(listing)
    return listing.renovations


# READ renovations for given renovation id
@router.get("/{renovation_id}", response_model=RenovationRead)
async def get_renovation_by_id(
    renovation_id: int, db: Annotated[Session, Depends(get_db)]
):
    renovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if renovation is None:
        raise HTTPException(
            status_code=404, detail=f"Renovation with id {renovation_id} not found"
        )
    return renovation


# UPDATE Renovation
@router.put("/{renovation_id}", response_model=RenovationRead)
async def update_renovation(
    renovation_id: int,
    renovation: RenovationUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    findRenovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if findRenovation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Renovation to update with id {renovation_id} not found",
        )
    update_renovation = renovation.model_dump(exclude_unset=True)
    try:
        for keys, value in update_renovation.items():
            setattr(findRenovation, keys, value)
        db.commit()
        db.refresh(findRenovation)
        return findRenovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating renovation with id {renovation_id}",
        )


# DELETE Renovation
@router.delete("/{renovation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_renovation(
    renovation_id: int, db: Annotated[Session, Depends(get_db)]
):
    renovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if renovation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Renovation to delete with id {renovation_id} not found",
        )
    try:
        db.delete(renovation)
        db.commit()
        return {"message": "Renovation Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting renovation with id {renovation_id}",
        )


def extract(description: str, listing_id: int) -> RenovationCreate:
    # gets response from gpt-4o-mini model and predicts room types from description
    message = []
    for msg in type_predictor["messages"]:
        content = msg["content"].replace("{description}", description)
        message.append({"role": msg["role"], "content": content})

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=message,
        text_format=RenovationCreate,
    )
    renovation = Renovation(
        **response.output_parsed.model_dump(), listing_id=listing_id
    )
    return renovation


def renovation_helper(renovation: models.Renovations, db: Session):
    try:
        db.add(renovation)
        db.flush()
        db.refresh(renovation)
        db.commit()
        return renovation
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting renovation: {e}")
