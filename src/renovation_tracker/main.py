from fastapi import FastAPI
from database import engine, Session
from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from pydantic_models import *


def get_db():
    
api = FastAPI()
# CREATE Listing
@api.post("/listings/", response_model=listings.ListingCreate)
async def create_listing():
    # TODO Query db for URL if found return listing
    # Else do page scrapping and add to db
    return {}


# READ all Listings
@api.get("/listings/", response_model=list[listings.ListingRead])
async def read_listing():
    # TODO Query db for listings
    # Return list of listings
    return {"message": "All listings on db"}


# READ single listing
@api.get("/listings/{listing_id}", response_model=listings.ListingRead)
async def read_listing(listing_id: int):
    # TODO Query db for listing with id 
    return {}

# UPDATE Listing
@api.put("/listings/{listing_id}", response_model=listings.ListingUpdate)
async def update_listing(listing_id: int):
    # TODO Query db for listing and update listing
    return{}


# DELETE Listing
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    #TODO Find listing and delete
    return {"message": "Listing Deleted"}








