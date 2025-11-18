from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional


# Schema for listing base
class Listing(BaseModel):
    url: str
    address: str
    description: str
    price: Optional[float] = None
    bedroom: Optional[float] = None
    bathroom: Optional[float] = None
    year_built: Optional[int] = None


#   photos: list[str]


# Schema for listing CREATE
class ListingCreate(BaseModel):
    url: HttpUrl


# Schema for listing READ / Delete
class ListingRead(Listing):
    listing_id: int
    model_config = ConfigDict(from_attributes=True)


# Schema for listing UPDATE
class ListingUpdate(BaseModel):
    url: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    bedroom: Optional[float] = None
    bathroom: Optional[float] = None
    year_built: Optional[int] = None
