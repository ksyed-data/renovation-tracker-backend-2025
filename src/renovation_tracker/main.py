from __future__ import annotations
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from renovation_tracker.database import engine, Session
import renovation_tracker.models as models
from renovation_tracker.pydantic_models.listings import (
    Listing,
    ListingRead,
    ListingUpdate,
)
from renovation_tracker.pydantic_models.renovations import (
    Renovation,
    RenovationRead,
    RenovationUpdate,
)
from renovation_tracker.pydantic_models.photos import Photos, PhotosRead, PhotosUpdate
from typing import Annotated
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import re
from PIL import Image
import requests
from io import BytesIO
from pydantic import BaseModel
from typing import Any, Dict
from ultralytics import YOLO
from renovation_tracker.nlp_predict import extract_renovations
import importlib.resources as resources
from sqlalchemy import inspect


class PredictRequest(BaseModel):
    description: str


class PredictResponse(BaseModel):
    result: Dict[str, Any]


# app = FastAPI(title="Renovation Tracker API")
api = FastAPI()
with resources.path("renovation_tracker.yolo_models", "best.pt") as model_path:
    yolo_model = YOLO(model_path)


@api.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@api.post("/predict-renovations", response_model=PredictResponse)
def predict_renovations(req: PredictRequest):
    """Accepts a property description and returns structured renovation info."""
    result = extract_renovations(req.description)
    return {"result": result}


def create_tables():
    models.Base.metadata.create_all(bind=engine)


inspector = inspect(engine)
tables = inspector.get_table_names()
if not tables:
    create_tables()


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# Create listing with custom inputs
@api.post("/listings/", response_model=ListingRead)
async def create_listing(listing: Listing, db: Annotated[Session, Depends(get_db)]):
    # Create listing using user input
    db_listing = models.Listing(**listing.dict())
    try:
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting listing: {e}")


# CREATE Listing with URL also creates Photos
@api.post("/listings/url", response_model=ListingRead)
async def create_url_listing(url: str, db: Annotated[Session, Depends(get_db)]):
    # Create listing object using web scraping helper function
    url_return = url_listing(url)
    try:
        db.add(url_return["listing"])
        db.commit()
        db.refresh(url_return["listing"])
        for img_url in url_return["photos_list"]:
            db_photo = models.Photos(
                url=img_url, listing_id=url_return["listing"].listing_id
            )
            db.add(db_photo)
        db.commit()
        return url_return["listing"]
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting listing: {e}")


# READ all Listings
@api.get("/listings/", response_model=list[ListingRead])
async def read_listing(db: Annotated[Session, Depends(get_db)], limit: int = 25):
    allListings = db.query(models.Listing).limit(limit).all()
    return allListings


# READ single listing
@api.get("/listings/{listing_id}", response_model=ListingRead)
async def list_listing(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )

    return listing


# UPDATE Listing
@api.put("/listings/{listing_id}", response_model=ListingRead)
async def update_listing(
    listing_id: int, listing: ListingUpdate, db: Annotated[Session, Depends(get_db)]
):
    findListing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if findListing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing to update with id {listing_id} not found"
        )

    update_listing = listing.dict(exclude_unset=True)

    try:
        for keys, value in update_listing.items():
            setattr(findListing, keys, value)

        db.commit()
        db.refresh(findListing)
        return findListing
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating listing {listing_id} {e}",
        )


# DELETE Listing
@api.delete("/listings/{listing_id}")
async def delete_item(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing to delete with id {listing_id} not found"
        )
    try:
        db.delete(listing)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting listing {listing_id}",
        )
    return {"message": "Listing Deleted"}


# CREATE Renovation
@api.post("/renovations/", response_model=RenovationRead)
async def create_renovation(
    renovation: Renovation, db: Annotated[Session, Depends(get_db)]
):
    db_renovation = models.Renovations(**renovation.dict())

    try:
        db.add(db_renovation)
        db.commit()
        db.refresh(db_renovation)
        return db_renovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error occurred while creating renovation"
        )


# READ renovations for given listing id
@api.get("/listings/{listing_id}/renovations", response_model=list[RenovationRead])
async def get_renovation(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = (
        db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    return listing.renovations


# READ renovations for given renovation id
@api.get("/renovations/{renovation_id}", response_model=RenovationRead)
async def get_renovation_by_id(
    renovation_id: int, db: Annotated[Session, Depends(get_db)]
):
    renovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if renovation is None:
        raise HTTPException(
            status_code=404, detail=f"Renovation with id {renovation_id} not found"
        )
    return renovation


# UPDATE Renovation
@api.put("/renovations/{renovation_id}", response_model=RenovationRead)
async def update_renovation(
    renovation_id: int,
    renovation: RenovationUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    findRenovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if findRenovation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Renovation to update with id {renovation_id} not found",
        )
    update_renovation = renovation.dict(exclude_unset=True)
    try:
        for keys, value in update_renovation.items():
            setattr(findRenovation, keys, value)
        db.commit()
        db.refresh(findRenovation)
        return findRenovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating renovation with id {renovation_id}",
        )


# DELETE Renovation
@api.delete("/renovations/{renovation_id}")
async def delete_renovation(
    renovation_id: int, db: Annotated[Session, Depends(get_db)]
):
    renovation = (
        db.query(models.Renovations)
        .filter(models.Renovations.renovation_id == renovation_id)
        .first()
    )
    if renovation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Renovation to delete with id {renovation_id} not found",
        )
    try:
        db.delete(renovation)
        db.commit()
        return {"message": "Renovation Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting renovation with id {renovation_id}",
        )


# CREATE Photo Entry with custom input
@api.post("/photos/", response_model=PhotosRead)
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
@api.get("/listings/{listing_id}/photos", response_model=list[PhotosRead])
async def get_photos(
    listing_id: int, db: Annotated[Session, Depends(get_db)], limit: int = 120
):
    listing = (
        db.query(models.Listing)
        .filter(models.Listing.listing_id == listing_id)
        .limit(limit)
        .first()
    )
    if listing is None:
        raise HTTPException(
            status_code=404, detail=f"Listing with id {listing_id} not found"
        )
    return listing.photos


# READ photo given photo id
@api.get("/photos/{photo_id}", response_model=PhotosRead)
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
@api.put("/photos/inference")
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
                detail=f"Error occurred while updating photo with id {photo_id}",
            )
    else:
        return findPhoto.room_type


# Update Photo Entry with custom input
@api.put("/photos/{photo_id}", response_model=PhotosRead)
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
    db_photos = photo.dict(exclude_unset=True)
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
@api.delete("/photos/{photo_id}")
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
            detail=f"Error occurred while deleting photo with id {photo_id}",
        )


# Helper function to obtain top matching room classification given image url
def get_room(url: str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    getImage = requests.get(url, headers=headers, stream=True, timeout=10)
    image = Image.open(BytesIO(getImage.content))
    results = yolo_model.predict(image)
    top1 = results[0].probs.top1
    return results[0].names[top1]


# Helper function to launch web driver used in selenium
def get_source(url: str):
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )
        driver.get(url)
        page_source = driver.page_source
        return page_source
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping error")
    finally:
        driver.quit()


# Helper function that takes url and returns listing object to be inerted into db and list of photo urls to be added as photos
def url_listing(url: str):
    # Web Scraping
    response = get_source(url)
    # Uses beautifulsoup to obtain info from html
    soup = BeautifulSoup(response, "html.parser")
    address = soup.find("span", {"class": "property-info-address-main"})
    city_state = soup.find("span", {"class": "property-info-address-citystatezip"})
    city_state_zip = ""
    for child in city_state:
        city_state_zip += child.get_text(strip=True) + " "
    description = soup.find("p", {"class": "ldp-description-text"})
    price = soup.find("span", {"class": "property-info-price"})
    price_numeric = (
        float(price.get_text(strip=True).replace("$", "").replace(",", ""))
        if price
        else None
    )
    bedroom_bathroom = soup.find_all("span", {"class": "property-info-feature"})
    bedroom = (
        float(
            bedroom_bathroom[0]
            .find("span", {"class": "property-info-feature-detail"})
            .get_text(strip=True)
        )
        if bedroom_bathroom
        and bedroom_bathroom[0].find("span", {"class": "feature-beds"})
        else None
    )
    bathroom = (
        float(
            bedroom_bathroom[1]
            .find("span", {"class": "property-info-feature-detail"})
            .get_text(strip=True)
        )
        if bedroom_bathroom
        and bedroom_bathroom[1].find("span", {"class": "feature-baths"})
        else None
    )
    year_container = soup.find(
        lambda tag: tag.name == "li"
        and "amenities-detail" in tag.get("class", [])
        and "Built in" in tag.text
    )
    year_built = None
    if year_container:
        year_built = re.search(
            r"Built in\s+(\d+)", year_container.get_text(strip=True)
        ).group(1)

    image_list = []
    image_container = soup.find(
        "div", {"class": "embla__container primary-carousel-container"}
    )
    slides = image_container.find_all("div") if image_container else None
    for div in slides:
        images = div.find_all(
            "img", {"class": "primary-carousel-slide-img carousel-item"}
        )
        for img in images:
            image_list.append(img["src"])

    db_listing = models.Listing(
        url=url,
        address=address.get_text(strip=True) + " " + city_state_zip,
        description=description.get_text(strip=True),
        price=price_numeric,
        bedroom=bedroom,
        bathroom=bathroom,
        year_built=year_built,
    )
    return {"listing": db_listing, "photos_list": image_list}


# Example web scrapping for testing
@api.get("/example/")
async def scrape_web(url: str):
    response = get_source(url)
    soup = BeautifulSoup(response, "html.parser")
    title_tag = soup.find("h1")
    address = soup.find("span", {"class": "property-info-address-main"})
    city_state = soup.find("span", {"class": "property-info-address-citystatezip"})
    city_state_zip = ""
    for child in city_state:
        city_state_zip += child.get_text(strip=True) + " "
    description = soup.find("p", {"class": "ldp-description-text"})
    price = soup.find("span", {"class": "property-info-price"})
    bedroom_bathroom = soup.find_all("span", {"class": "property-info-feature"})
    bedroom = bedroom_bathroom[0].find(
        "span", {"class": "property-info-feature-detail"}
    )
    bathroom = bedroom_bathroom[1].find(
        "span", {"class": "property-info-feature-detail"}
    )
    year_container = soup.find(
        lambda tag: tag.name == "li"
        and "amenities-detail" in tag.get("class", [])
        and "Built in" in tag.text
    )
    year_built = re.search(r"Built in\s+(\d+)", year_container.get_text(strip=True))
    image_list = []
    image_container = soup.find(
        "div", {"class": "embla__container primary-carousel-container"}
    )
    slides = image_container.find_all("div")
    for div in slides:
        images = div.find_all(
            "img", {"class": "primary-carousel-slide-img carousel-item"}
        )
        for img in images:
            image_list.append(img["src"])

    return {
        "response": address.get_text(strip=True)
        + " "
        + city_state_zip
        + " "
        + description.get_text(strip=True)
        + " "
        + price.get_text(strip=True)
        + " "
        + bedroom.get_text(strip=True)
        + " "
        + bathroom.get_text(strip=True)
        + " "
        + year_built.group(1)
        + " "
        + str(len(image_list))
    }
