from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from database import engine, Session
import models
from pydantic_models.listings import Listing, ListingRead, ListingUpdate
from pydantic_models.renovations import Renovation, RenovationRead, RenovationUpdate
from typing import Annotated
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import re

from pydantic import BaseModel
from typing import Any, Dict

from nlp_predict import extract_renovations


class PredictRequest(BaseModel):
    description: str


class PredictResponse(BaseModel):
    result: Dict[str, Any]


app = FastAPI(title="Renovation Tracker API")


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@app.post("/predict-renovations", response_model=PredictResponse)
def predict_renovations(req: PredictRequest):
    """Accepts a property description and returns structured renovation info."""
    result = extract_renovations(req.description)
    return {"result": result}


def main():
    print("This module exposes a FastAPI app. Run with: uvicorn renovation_tracker.main:app --reload")



models.Base.metadata.create_all(bind = engine)
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
api = FastAPI()

# CREATE Listings
@api.post("/listings/", response_model=ListingRead)
async def create_listing(url: str, db: Annotated[Session, Depends(get_db)]):
    # Web Scraping
    response = get_source(url)
    # Uses beautifulsoup to obtain info from html
    soup = BeautifulSoup(response, 'html.parser')
    address = soup.find("span", {"class": "property-info-address-main"})
    city_state = soup.find("span",{"class": "property-info-address-citystatezip"})
    city_state_zip = ""
    for child in city_state:
        city_state_zip+= (child.get_text(strip=True)+" ")
    description = soup.find("p",{"class": "ldp-description-text"})
    price = soup.find("span",{"class": "property-info-price"})
    price_numeric = float(price.get_text(strip = True).replace("$", "").replace(",", ""))
    bedroom_bathroom = soup.find_all("span",{"class": "property-info-feature"})
    bedroom = bedroom_bathroom[0].find("span",{"class": "property-info-feature-detail"})
    bathroom = bedroom_bathroom[1].find("span",{"class": "property-info-feature-detail"})
    year_container = soup.find(lambda tag: tag.name == "li" and "amenities-detail" in tag.get("class", []) and "Built in" in tag.text)
    year_built = re.search(r"Built in\s+(\d+)", year_container.get_text(strip=True))

    # Create listing object from scraped data and add to db
    db_listing = models.Listing(
        url=url,
        address=address.get_text(strip=True) + " " + city_state_zip,
        description=description.get_text(strip=True),
        price=price_numeric,
        bedroom = float(bedroom.get_text(strip=True)),
        bathroom = float(bathroom.get_text(strip=True)),
        year_built = year_built.group(1)
    )
    try:
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)
        return db_listing
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error inserting listing: {e}"
        )
   

# READ all Listings
@api.get("/listings/", response_model=list[ListingRead])
async def read_listing(db: Annotated[Session, Depends(get_db)]):
    allListings = db.query(models.Listing).all()
    return allListings


# READ single listing
@api.get("/listings/{listing_id}", response_model=ListingRead)
async def list_listing(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail='Listing with id {listing_id} not found')
    
    return listing


# UPDATE Listing
@api.put("/listings/{listing_id}", response_model=ListingRead)
async def update_listing(listing_id: int, listing:ListingUpdate, db: Annotated[Session, Depends(get_db)]):
    findListing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if findListing is None:
        raise HTTPException(status_code=404,detail='Listing to update with id {listing_id} not found')
    
    update_listing = listing.dict(exclude_unset=True)

    try:
        for keys, value in update_listing.items():
            setattr(findListing,keys,value)

        db.commit()
        db.refresh(findListing)
        return findListing
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating listing {listing_id}"
        )



# DELETE Listing
@api.delete("/listings/{listing_id}")
async def delete_item(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail=f"Listing to delete with id {listing_id} not found")
    try:
        db.delete(listing)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting listing {listing_id}"
        )
    return {"message": "Listing Deleted"}

# CREATE Renovation
@api.post("/renovations/", response_model=RenovationRead)
async def create_renovation(renovation: Renovation, db: Annotated[Session, Depends(get_db)]):
    db_renovation = models.Renovations(**renovation.dict())

    try:
        db.add(db_renovation)
        db.commit()
        db.refresh(db_renovation)
        return db_renovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while creating renovation"
        )

# READ renovations for given listing id
@api.get("/listings/{listing_id}/renovations", response_model=list[RenovationRead])
async def get_renovation(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if listing is None:
        raise HTTPException(status_code=404,detail=f"Listing with id {listing_id} not found")
    return listing.renovations

# READ renovations for given renovation id
@api.get("/renovations/{renovation_id}", response_model=RenovationRead)
async def get_renovationWID(renovation_id: int, db: Annotated[Session, Depends(get_db)]):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if renovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation with id {renovation_id} not found")
    return renovation

# UPDATE Renovation
@api.put("/renovations/{renovation_id}", response_model=RenovationRead)
async def update_renovation(renovation_id: int, renovation: RenovationUpdate, db: Annotated[Session, Depends(get_db)]):
    findRenovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if findRenovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation to update with id {renovation_id} not found")
    update_renovation = renovation.dict(exclude_unset=True)
    try:
        for keys, value in update_renovation.items():
            setattr(findRenovation,keys,value)
        db.commit()
        db.refresh(findRenovation)
        return findRenovation
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while updating renovation with id {renovation_id}"
        )

    

# DELETE Renovation
@api.delete("/renovations/{renovation_id}")
async def delete_renovation(renovation_id: int, db: Annotated[Session, Depends(get_db)]):
    renovation = db.query(models.Renovations).filter(models.Renovations.renovation_id == renovation_id).first()
    if renovation is None:
        raise HTTPException(status_code=404,detail=f"Renovation to delete with id {renovation_id} not found")
    try:
        db.delete(renovation)
        db.commit()
        return {"message": "Renovation Deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while deleting renovation with id {renovation_id}"
        )

# Helper function to launch web driver used in selenium
def get_source(url: str):
    try:
        driver = webdriver.Chrome(service = ChromeService(ChromeDriverManager().install()))
        driver.get(url)
        page_source = driver.page_source
        return page_source
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping error")
    finally:
        driver.quit()
    


#Example web scrapping for testing
@api.get("/example/")
async def scrape_web(url: str):
    
    response = get_source(url)
    soup = BeautifulSoup(response, 'html.parser')
    title_tag = soup.find("h1")
    address = soup.find("span", {"class": "property-info-address-main"})
    city_state = soup.find("span",{"class": "property-info-address-citystatezip"})
    city_state_zip = ""
    for child in city_state:
        city_state_zip+= (child.get_text(strip=True)+" ")
    description = soup.find("p",{"class": "ldp-description-text"})
    price = soup.find("span",{"class": "property-info-price"})
    bedroom_bathroom = soup.find_all("span",{"class": "property-info-feature"})
    bedroom = bedroom_bathroom[0].find("span",{"class": "property-info-feature-detail"})
    bathroom = bedroom_bathroom[1].find("span",{"class": "property-info-feature-detail"})
    year_container = soup.find(lambda tag: tag.name == "li" and "amenities-detail" in tag.get("class", []) and "Built in" in tag.text)
    year_built = re.search(r"Built in\s+(\d+)", year_container.get_text(strip=True))

    return {"response": address.get_text(strip=True)+" "+ city_state_zip+ " "+ description.get_text(strip=True)+" "+price.get_text(strip=True)+ " "+bedroom.get_text(strip=True)+" "+bathroom.get_text(strip=True)+" "+year_built.group(1)}

