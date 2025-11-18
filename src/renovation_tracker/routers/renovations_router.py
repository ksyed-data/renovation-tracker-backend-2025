from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from renovation_tracker.pydantic_models.renovations import (
    Renovation,
    RenovationRead,
    RenovationUpdate,
)
import renovation_tracker.models as models
from renovation_tracker.nlp_predict import extract
from renovation_tracker.database import get_db, Session

router = APIRouter(prefix="/renovations")
db_dependency = Annotated[Session, Depends(get_db)]


# CREATE Renovation
@router.post("/", response_model=RenovationRead, status_code=status.HTTP_201_CREATED)
async def create_renovation(
    renovation: Renovation, db: Annotated[Session, Depends(get_db)]
):
    db_renovation = models.Renovations(**renovation.dict())

    try:
        db.add(db_renovation)
        db.commit()
        db.refresh(db_renovation)
        return db_renovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error occurred while creating renovation {e}"
        )


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


@router.post("/predict-renovations", response_model=Renovation)
def predict_renovations(req: Renovation):
    """Accepts a property description and returns structured renovation info."""
    result = extract(req.description)
    return {"result": result}
