from fastapi import APIRouter, HTTPException, Depends, Query, status
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
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from bs4 import BeautifulSoup


router = APIRouter(prefix="/listings")
db_dependency = Annotated[Session, Depends(get_db)]


# Create listing with custom inputs
@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
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
@router.post("/url", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_url_listing(url: str, db: Annotated[Session, Depends(get_db)]):
    # Create listing object using web scraping helper function
    url_return = url_listing(url)
    try:
        db.add(url_return["listing"])
        db.flush()
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
async def read_listing(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=25, le=100, description="limit amount of listings read"),
):
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

    update_listing = listing.model_dump(exclude_unset=True)

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
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
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


#


# Helper function to launch web driver used in selenium
def get_source(url: str):
    driver = None
    try:
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )
        driver.set_page_load_timeout(15)
        driver.get(url)

        page_source = driver.page_source

        return page_source
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping error {e}")
    finally:
        if driver:
            driver.quit()


# helpers.py or at top of your routes file
def scrape_carousel_images(driver):
    image_list = {}
    visited_slides = set()

    # Get the next button
    next_btn = driver.find_element(
        By.CSS_SELECTOR, "button.primary-carousel-right-nav.right-nav"
    )

    while True:
        # Find all slide containers
        slides = driver.find_elements(By.CSS_SELECTOR, "div.primary-carousel-slide")

        found_new_slide = False

        for slide in slides:
            slide_num = slide.get_attribute("data-slide")

            # Skip if slide_num missing (shouldn’t happen) or already visited
            if not slide_num or slide_num in visited_slides:
                continue

            # Mark new slide detected
            found_new_slide = True
            visited_slides.add(slide_num)

            # Extract all images inside this slide
            imgs = slide.find_elements(
                By.CSS_SELECTOR, "img.primary-carousel-slide-img"
            )

            for img in imgs:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                idx = img.get_attribute("data-index")
                if src and idx:
                    image_list[idx] = src

        # No new slide found → we're looping, so stop
        if not found_new_slide:
            break

        # Click next and wait for the slide to change
        try:
            driver.execute_script("arguments[0].click();", next_btn)

            # Wait for new slide to appear (data-slide changes)
            WebDriverWait(driver, 5).until(
                lambda d: any(
                    s.get_attribute("data-slide") not in visited_slides
                    for s in d.find_elements(
                        By.CSS_SELECTOR, "div.primary-carousel-slide"
                    )
                )
            )
            time.sleep(0.4)

        except Exception:
            break

    return list(image_list.values())


# Helper function that takes url and returns listing object to be inerted into db and list of photo urls to be added as photos
def url_listing(url: str):
    # Web Scraping
    response = get_source(url)
    # Uses beautifulsoup to obtain info from html
    soup = BeautifulSoup(response, "html.parser")

    # Webscraping Address (Required)
    address = soup.find("span", {"class": "property-info-address-main"})
    if not address:
        raise NoSuchElementException("Address not found likely not a valid URL")
    city_state = soup.find("span", {"class": "property-info-address-citystatezip"})
    city_state_zip = ""
    if not city_state:
        raise NoSuchElementException("Address not found likely not a valid URL")
    for child in city_state:
        city_state_zip += child.get_text(strip=True) + " "

    # Scraping description (Required)
    description = soup.find("p", {"class": "ldp-description-text"})
    if not description:
        raise NoSuchElementException("Description not found likely not a valid URL")

    # Scraping Price (Optional)
    price = soup.find("span", {"class": "property-info-price"})
    price_numeric = (
        float(price.get_text(strip=True).replace("$", "").replace(",", ""))
        if price
        else None
    )

    # Scraping number of bedrooms and bathroom (Optional)
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

    # Scraping year built (Optional)
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

    # Scraping images (Optional)
    image_list = []
    image_container = soup.find(
        "div", {"class": "embla__container primary-carousel-container"}
    )
    slides = image_container.find_all("div") if image_container else None
    if slides is not None:
        for div in slides:
            images = div.find_all(
                "img", {"class": "primary-carousel-slide-img carousel-item"}
            )
        for img in images:
            image_list.append(img["src"])

    # Creating listing object
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


# Example web scraping for testing
@router.get("/example/")
async def scrape_web(url: str):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(15)
    driver.get(url)
    # response = get_source(url)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
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
        year_built = None
        if year_container:
            year_built = (
                re.search(r"Built in\s+(\d+)", year_container.get_text(strip=True))
            ).group(1)

        # scrape images dynamically
        images = scrape_carousel_images(driver)
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
            + str(year_built or "")
            + " "
            + str(len(images))
            + " "
        }
    finally:
        driver.quit()
