from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from renovation_tracker.pydantic_models.listings import (
    Listing,
    ListingRead,
    ListingUpdate,
)
import renovation_tracker.models as models
from renovation_tracker.database import get_db, Session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from bs4 import BeautifulSoup


router = APIRouter(prefix="/listings")
db_dependency = Annotated[Session, Depends(get_db)]


# Create listing with custom inputs
@router.post("/", response_model=ListingRead)
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
@router.post("/url", response_model=ListingRead)
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
@router.get("/", response_model=list[ListingRead])
async def read_listing(db: Annotated[Session, Depends(get_db)], limit: int = 25):
    allListings = db.query(models.Listing).limit(limit).all()
    return allListings


# READ single listing
@router.get("/{listing_id}", response_model=ListingRead)
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
@router.put("/{listing_id}", response_model=ListingRead)
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
@router.delete("/{listing_id}")
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


# Helper function to launch web driver used in selenium
def get_source(url: str):
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )
        driver.get(url)

        page_source = driver.page_source

        # slides = []
        # time.sleep(2)
        # slider = driver.find_elements(
        #     By.CSS_SELECTOR, "div[class^='primary-carousel-slide']"
        # )
        #  print(str(len(slider)) + "J")
        #  for current in driver.find_elements(
        #      By.CSS_SELECTOR, "div[class^='primary-carousel-slide']"
        #  ):
        #     print("KF")
        #      time.sleep(1)

        # while True:
        #      slide = driver.find_element(
        #         By.CSS_SELECTOR, "div[class^='primary-carousel-slide']"
        #      )
        #     slidess = driver.find_elements(
        #          By.CSS_SELECTOR, "div[class^='primary-carousel-slide']"
        #      )
        #    print(str(len(slidess)) + "L")
        #    slide_html = slide.get_attribute("data-slide")
        #    if slide_html not in slides:
        #        slides.append(slide_html)
        #    else:
        #        print("found")
        #        break
        #    next_btn = driver.find_element(
        #        By.CSS_SELECTOR, "button.primary-carousel-right-nav.right-nav"
        #    )
        #   if next_btn:
        #        next_btn.click()
        #    else:
        #        print("no button")
        #       break
        #    time.sleep(1)
        # print(str(len(slides)))
        return page_source
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping error {e}")
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


@router.get("/example/")
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
        + " "
    }
