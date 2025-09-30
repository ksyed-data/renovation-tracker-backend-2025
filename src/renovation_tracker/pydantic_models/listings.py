from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


# Schema for listing base 
class Listing(BaseModel):
    url: HttpUrl
    address: str
    description: str
    price: float
    photos: list[str]

# Schema for listing CREATE
class ListingCreate(BaseModel):
    url: HttpUrl

# Schema for listing READ
class ListingRead(Listing):
    listing_id:str

# Schema for listing UPDATE
class ListingUpdate(BaseModel):
    listing_id: Optional[int] 
    url: Optional[str] 
    address: Optional[str]
    description: Optional[str]

# Schema for listing DELETE
class ListingDelete(Listing):
    listing_id:str






