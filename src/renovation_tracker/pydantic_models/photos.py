from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


# Enum for bedrooms in photos
class Room(StrEnum):
    LIVING_ROOM = "Livingroom"
    DINING_ROOM = "Dining"
    BEDROOM = "Bedroom"
    BATHROOM = "Bathroom"
    KITCHEN = "Kitchen"


# Schema for photos
class Photos(BaseModel):
    listing_id: int
    url: str
    room_type: Optional[Room]


class PhotosRead(Photos):
    photo_id: int

    class Config:
        orm_mode = True
