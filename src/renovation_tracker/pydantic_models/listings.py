from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


# Schema for listing base 
class Listing(BaseModel):
    url: str
    address: str
    description: str
    price: float
    bedroom: float
    bathroom: float
    year_built: int
 #   photos: list[str]

# Schema for listing CREATE
class ListingCreate(BaseModel):
    url: HttpUrl

# Schema for listing READ / Delete
class ListingRead(Listing):
    listing_id:int
    class Config:
        orm_mode = True 

# Schema for listing UPDATE
class ListingUpdate(BaseModel):
    url: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    bedroom: Optional[float] = None
    bathroom: Optional[float] = None
    date_built: Optional[int] = None







