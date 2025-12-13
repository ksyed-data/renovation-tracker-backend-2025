from enum import StrEnum
from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional


# Enum for bedrooms in photos
class Room(StrEnum):
    LIVING_ROOM = "Livingroom"
    DINING_ROOM = "Dining"
    BEDROOM = "Bedroom"
    BATHROOM = "Bathroom"
    KITCHEN = "Kitchen"
    HOME_EXTERIOR = "HomeExterior"


# Schema for photos
class Photos(BaseModel):
    listing_id: int
    url: str
    room_type: Optional[Room]


class PhotosRead(Photos):
    photo_id: int
    model_config = ConfigDict(from_attributes=True)


class PhotosUpdate(BaseModel):
    url: Optional[str]
    room_type: Optional[Room]
