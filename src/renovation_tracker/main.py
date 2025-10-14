from fastapi import FastAPI, Depends, HTTPException
from database import engine, Session
import models
from pydantic_models.listings import Listing, ListingRead, ListingUpdate
from pydantic_models.renovations import Renovation, RenovationRead, RenovationUpdate
from typing import Annotated
import httpx



models.Base.metadata.create_all(bind = engine)
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
api = FastAPI()

# CREATE Listings
@api.post("/listings/", response_model=ListingRead)
async def create_listing(listing:Listing, db: Annotated[Session, Depends(get_db)]):
    # TODO Page Scraping
    db_listing = models.Listing(**listing.dict())
    try:
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error inserting listing"
        )
   

# READ all Listings
@api.get("/listings/", response_model=list[ListingRead])
async def read_listing(db: Annotated[Session, Depends(get_db)]):
    allListings = db.query(models.Listing).all()
    return allListings


# READ single listing
@api.get("/listings/{listing_id}", response_model=ListingRead)
async def list_listing(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail='Listing with id {listing_id} not found')
    
    return listing


# UPDATE Listing
@api.put("/listings/{listing_id}", response_model=ListingRead)
async def update_listing(listing_id: int, listing:ListingUpdate, db: Annotated[Session, Depends(get_db)]):
    findListing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if findListing is None:
        raise HTTPException(status_code=404,detail='Listing to update with id {listing_id} not found')
    
    update_listing = listing.dict(exclude_unset=True)

    try:
        for keys, value in update_listing.items():
            setattr(findListing,keys,value)

        db.commit()
        db.refresh(findListing)
        return findListing
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating listing {listing_id}"
        )



# DELETE Listing
@api.delete("/listings/{listing_id}")
async def delete_item(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail=f"Listing to delete with id {listing_id} not found")
    try:
        db.delete(listing)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting listing {listing_id}"
        )
    return {"message": "Listing Deleted"}

# CREATE Renovation
@api.post("/renovations/", response_model=RenovationRead)
async def create_renovation(renovation: Renovation, db: Annotated[Session, Depends(get_db)]):
    db_renovation = models.Renovations(**renovation.dict())

    try:
        db.add(db_renovation)
        db.commit()
        db.refresh(db_renovation)
        return db_renovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while creating renovation"
        )

# READ renovations for given listing id
@api.get("/listings/{listing_id}/renovations", response_model=list[RenovationRead])
async def get_renovation(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail=f"Listing with id {listing_id} not found")
    return listing.renovations

# READ renovations for given renovation id
@api.get("/renovations/{renovation_id}", response_model=RenovationRead)
async def get_renovationWID(renovation_id: int, db: Annotated[Session, Depends(get_db)]):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if renovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation with id {renovation_id} not found")
    return renovation

# UPDATE Renovation
@api.put("/renovations/{renovation_id}", response_model=RenovationRead)
async def update_renovation(renovation_id: int, renovation: RenovationUpdate, db: Annotated[Session, Depends(get_db)]):
    findRenovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if findRenovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation to update with id {renovation_id} not found")
    update_renovation = renovation.dict(exclude_unset=True)
    try:
        for keys, value in update_renovation.items():
            setattr(findRenovation,keys,value)
        db.commit()
        db.refresh(findRenovation)
        return findRenovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating renovation with id {renovation_id}"
        )

    

# DELETE Renovation
@api.delete("/renovations/{renovation_id}")
async def delete_renovation(renovation_id: int, db: Annotated[Session, Depends(get_db)]):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if renovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation to delete with id {renovation_id} not found")
    try:
        db.delete(renovation)
        db.commit()
        return {"message": "Renovation Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting renovation with id {renovation_id}"
        )

#Example web scrapping not completly implemented
@api.post("/example/")
async def scrape_web(url: str):
    with httpx.Client(follow_redirects=True, timeout=10) as client:
        response = client.get(url)
        return {"response:", response.text}

