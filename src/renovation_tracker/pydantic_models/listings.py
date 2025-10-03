from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


# Schema for listing base 
class Listing(BaseModel):
    url: str
    address: str
    description: str
    price: float
 #   photos: list[str]

# Schema for listing CREATE
class ListingCreate(BaseModel):
    url: HttpUrl

# Schema for listing READ
class ListingRead(Listing):
    listing_id:int

# Schema for listing UPDATE
class ListingUpdate(BaseModel):
    url: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

# Schema for listing DELETE
class ListingDelete(Listing):
    listing_id:str






