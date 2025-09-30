from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

# Schema for renovations base
class Renovation(BaseModel):
    listing_id: int
    bathroom: bool = Field(default=False)
    kitchen: bool = Field(default=False)
    living_room: bool = Field(default=False)
    bedroom: bool = Field(default=False)
    basement: bool = Field(default=False)

# Schema for renovations CREATE
class RenovationCreate(BaseModel):
    pass

# Schema for renovations READ
class RenovationRead(Renovation):
    renovation_id: int 

#Schema for renovations UPDATE
class RenovationUpdate(BaseModel):
    listing_id: int
    bathroom: Optional[bool]
    kitchen: Optional[bool]
    living_room: Optional[bool]
    bedroom: Optional[bool]
    basement: Optional[bool]

#Schema for renovations DELETE
class RenovationsDelete(Renovation):
    renovation_id: str
