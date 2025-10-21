from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


# Enum for bedrooms in photos
class Room(StrEnum):
    LIVING_ROOM = "living room"
    DINING_ROOM = "dining room"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    BASEMENT = "basement"

#Schema for photos
class Photos(BaseModel):
    listing_id: int
    url: str
    room_type: Room 

