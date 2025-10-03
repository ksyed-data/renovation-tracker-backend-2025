from fastapi import FastAPI, Depends
from database import engine, Session
from enum import StrEnum
import models
from pydantic import BaseModel, HttpUrl, Field
from pydantic_models import *
from typing import Annotated


models.Base.metadata.create_all(bind = engine)
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


    
api = FastAPI()
# CREATE Listing
@api.post("/listings/", response_model=Listing)
async def create_listing(listing:Listing, db: db_dependency):
    # TODO Page Scraping
    db_listing = models.Listing(**listing.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)  # gets updated fields like auto-incremented id
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
    # TODO Query db for listing and update listing
    return findListing


# DELETE Listing
@api.delete("/listings/{listing_id}")
async def delete_item(listing_id: int, db: db_dependency):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    db.delete(listing)
    db.commit()
    return {"message": "Listing Deleted"}








