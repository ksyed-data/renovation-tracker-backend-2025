import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from renovation_tracker.pydantic_models.photos import Photos, PhotosRead, PhotosUpdate
import renovation_tracker.models as models
from renovation_tracker.database import get_db, Session
from PIL import Image
import requests
from io import BytesIO
import importlib.resources as resources
from ultralytics import YOLO
import openai
import os

router = APIRouter(prefix="/photos")
db_dependency = Annotated[Session, Depends(get_db)]
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai.api_key)
with resources.path("renovation_tracker.yolo_models", "final.pt") as model_path:
    yolo_model = YOLO(model_path)


# CREATE Photo Entry with custom input
@router.post("/", response_model=PhotosRead, status_code=status.HTTP_201_CREATED)
async def create_photo(photo: Photos, db: Annotated[Session, Depends(get_db)]):
    db_photos = models.Photos(**photo.dict())
    try:
        db.add(db_photos)
        db.commit()
        db.refresh(db_photos)
        return db_photos
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting photo: {e}")


# READ photos for given listing id
@router.get("/{listing_id}/read", response_model=list[PhotosRead])
async def get_photos(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    return listing.photos


# READ photo given photo id
@router.get("/{photo_id}", response_model=PhotosRead)
async def get_photo_by_id(photo_id: int, db: Annotated[Session, Depends(get_db)]):
    get_photo = (
        db.query(models.Photos).filter(models.Photos.photo_id == photo_id).first()
    )
    if get_photo is None:
        raise HTTPException(
            status_code=404, detail=f"Photo with id {photo_id} not found"
        )

    return get_photo


# Photo inference function to return roomtype given photoid
@router.put("/inference")
async def photo_inference(photo_id: int, db: Annotated[Session, Depends(get_db)]):
    findPhoto = (
        db.query(models.Photos).filter(models.Photos.photo_id == photo_id).first()
    )
    if findPhoto is None:
        raise HTTPException(
            status_code=404, detail=f"Photo with id {photo_id} not found"
        )
    if findPhoto.room_type is None:
        try:
            room = get_room(findPhoto.url)
            setattr(findPhoto, "room_type", room)
            db.commit()
            db.refresh(findPhoto)
            return room
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error occurred while updating photo with id {photo_id} error: {e}",
            )
    else:
        return findPhoto.room_type


@router.put("/inferenceAll")
async def photo_inference_all(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    photos = listing.photos

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_photo = {
            executor.submit(get_room, photo.url): photo
            for photo in photos
            if photo.room_type is None
        }
        for future in as_completed(future_to_photo):
            photo = future_to_photo[future]
            try:
                room = future.result()
                setattr(photo, "room_type", room)
                db.commit()
                db.refresh(photo)
            except Exception as e:
                db.rollback()
                print(
                    f"Error occurred while updating photo with id {photo.photo_id} error: {e}"
                )
    return listing.photos


# Update Photo Entry with custom input
@router.put("/{photo_id}", response_model=PhotosRead)
async def update_photo(
    photo_id: int, photo: PhotosUpdate, db: Annotated[Session, Depends(get_db)]
):
    find_photo = (
        db.query(models.Photos).filter(models.Photos.photo_id == photo_id).first()
    )
    if find_photo is None:
        raise HTTPException(
            status_code=404, detail=f"Photo to update with id {photo_id} not found"
        )
    db_photos = photo.model_dump(exclude_unset=True)
    try:
        for keys, value in db_photos.items():
            setattr(find_photo, keys, value)
        db.commit()
        db.refresh(find_photo)
        return find_photo
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating photo {photo_id} {e}",
        )


# DELETE Photo
@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: int, db: Annotated[Session, Depends(get_db)]):
    find_photo = (
        db.query(models.Photos).filter(models.Photos.photo_id == photo_id).first()
    )
    if find_photo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Photo to delete with id {photo_id} not found",
        )
    try:
        db.delete(find_photo)
        db.commit()
        return {"message": "Photo Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting photo with id {photo_id} error: {e}",
        )


# Helper function to obtain top matching room classification given image url
def get_room(url: str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    getImage = requests.get(url, headers=headers, stream=True, timeout=10)
    image = Image.open(BytesIO(getImage.content))
    results = yolo_model.predict(image)
    confidence = results[0].probs.top1conf.item()
    top1 = results[0].probs.top1
    print(confidence)
    if confidence < 0.5:
        print("low confidence, using LLM")
        return get_room_LLM(getImage.content)
    return results[0].names[top1]


def get_room_LLM(image):
    img_base64 = base64.b64encode(image).decode("utf-8")
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Classify the image into exactly one room type from this list: Livingroom, Dining, Bedroom, Bathroom, Kitchen, HomeExterior, Hallway, Laundry, Other. Return only the room type."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{img_base64}",
                    },
                ],
            }
        ],
    )
    return response.output_text
