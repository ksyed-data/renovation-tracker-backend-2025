from fastapi import FastAPI, Depends
from database import engine, Session
from enum import StrEnum
import models
from pydantic import BaseModel, HttpUrl, Field
from pydantic_models import *
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
async def create_listing(listing:Listing, db: db_dependency):
    # TODO Page Scraping
    db_listing = models.Listing(**listing.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


# READ all Listings
@api.get("/listings/", response_model=list[ListingRead])
async def read_listing(db: db_dependency):
    allListings = db.query(models.Listing).all()
    return allListings


# READ single listing
@api.get("/listings/{listing_id}", response_model=ListingRead)
async def read_listing(listing_id: int, db: db_dependency):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    return listing


# UPDATE Listing
@api.put("/listings/{listing_id}", response_model=ListingRead)
async def update_listing(listing_id: int, listing:ListingUpdate, db: db_dependency):
    findListing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    update_listing = listing.dict(exclude_unset=True)
    for keys, value in update_listing.items():
        setattr(findListing,keys,value)
    db.commit()
    db.refresh(findListing)
    return findListing


# DELETE Listing
@api.delete("/listings/{listing_id}")
async def delete_item(listing_id: int, db: db_dependency):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    db.delete(listing)
    db.commit()
    return {"message": "Listing Deleted"}

# CREATE Renovation
@api.post("/renovations/", response_model=RenovationRead)
async def create_renovation(renovation: Renovation, db: db_dependency):
    db_renovation = models.Renovations(**renovation.dict())
    db.add(db_renovation)
    db.commit()
    db.refresh(db_renovation)
    return db_renovation

# READ renovations for given listing id
@api.get("/listings/{listing_id}/renovations", response_model=list[RenovationRead])
async def get_renovation(listing_id: int, db: db_dependency):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    return listing.renovations

# READ renovations for given renovation id
@api.get("/renovations/{renovation_id}", response_model=RenovationRead)
async def get_renovationWID(renovation_id: int, db: db_dependency):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    return renovation

# UPDATE Renovation
@api.put("/renovations/{renovation_id}", response_model=RenovationRead)
async def update_renovation(renovation_id: int, renovation: RenovationUpdate, db: db_dependency):
    findRenovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    update_renovation = renovation.dict(exclude_unset=True)
    for keys, value in update_renovation.items():
        setattr(findRenovation,keys,value)
    db.commit()
    db.refresh(findRenovation)
    return findRenovation

# DELETE Renovation
@api.delete("/renovations/{renovation_id}")
async def delete_renovation(renovation_id: int, db: db_dependency):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    db.delete(renovation)
    db.commit()
    return {"message": "Renovation Deleted"}

#Example web scrapping not completly implemented
@api.post("/example/")
async def scrape_web(url: str):
    with httpx.Client(follow_redirects=True, timeout=10) as client:
        response = client.get(url)
        print(response.status_code)
        return {"response:", response.text}

