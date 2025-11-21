from __future__ import annotations
from fastapi import FastAPI
from renovation_tracker.database import engine, Session
import renovation_tracker.models as models
from renovation_tracker.routers import listings_router
from renovation_tracker.routers import renovations_router
from renovation_tracker.routers import photos_router
from pydantic import BaseModel
from typing import Any, Dict
from renovation_tracker.nlp_predict import extract_renovations
from sqlalchemy import inspect


class PredictRequest(BaseModel):
    description: str


class PredictResponse(BaseModel):
    result: Dict[str, Any]


api = FastAPI()
api.include_router(listings_router.router)
api.include_router(renovations_router.router)
api.include_router(photos_router.router)


def create_tables():
    models.Base.metadata.create_all(bind=engine)


def drop_tables():
    models.Base.metadata.drop_all(bind=engine)


def reset_db():
    drop_tables()
    create_tables()


def seed_data():
    session = Session()
    listings = [
        models.Listing(
            url="https://www.homes.com/property/12301-fawn-lake-pkwy-spotsylvania-va/2s8v31qvw8527",
            address="12301 Fawn Lake Pkwy Spotsylvania, VA 22551",
            description="Luxury meets lake living at 12301 Fawn Lake Parkway — a turnkey colonial that feels brand new and beautifully balanced between comfort and sophistication. Set within a popular community that lives like a resort, this home captures modern design, timeless detail, and the ease of everyday lake life. Tucked on over half an acre across from the water in Fawn Lake, this Corsica model by Ryan Homes is a sought-after floor plan. Every inch feels purposeful and current — from the stone-accented façade to the refined interiors that balance livable warmth with luxury detail. Just a three-minute stroll from the lake itself, this address delivers both serenity and convenience. Fawn Lake’s resort-style amenities include an Arnold Palmer-designed golf course, clubhouse and restaurant, community pool, tennis and pickleball center, walking trails, and the breathtaking 288-acre private lake at the heart of it all. The curb appeal is striking — dark blue siding contrasted by natural stone, a deep burgundy front door, and newly landscaped gardens framed by crepe myrtles, fresh seed and aeration, and privacy evergreens. The side-loading two-car garage and widened asphalt driveway make daily living effortless, while the rear deck opens to tall trees and peaceful privacy. Inside, light luxury vinyl plank flooring, upgraded hardware, and custom details set a refined tone. A French-door office sits near the entry — perfect for work-from-home days — while the open main living space centers around a stone gas fireplace. The family room transitions seamlessly into the show-stopping kitchen: a massive island with white quartzite counters, full-height, custom backsplash, under-cabinet lighting, stainless appliances, and a walk-in pantry built for real life. Four spacious bedrooms anchor the upper level, including a primary suite that feels like a private spa. Dual walk-ins, a Roman shower, dual vanities, and a private water closet create a daily retreat. Two of the secondary bedrooms — and the loft just outside them — capture tranquil lake views that frame the sunrise beautifully. The upstairs laundry room (complete with sink and conveying appliances) adds practical luxury. The fully finished lower level offers an additional dimension of living: a true media room with theater ambiance, a large recreation room, full bath, and fifth bedroom. Designer accent walls in cyber gray keep the look fresh and modern, and the walk-out access brings in natural light. Beyond the gates, Route 3 and everyday conveniences are minutes away, while Downtown Fredericksburg, Orange, and Culpeper are within half an hour. Yet at home, you’ll feel a world apart — surrounded by lake breezes, tall trees, and the quiet confidence that comes with a property built right and maintained perfectly. This is a rare opportunity to live across from the lake, surrounded by resort-level amenities, in a home that feels as fresh as the day it was built.",
            price=925000,
            bedroom=5,
            bathroom=4.5,
            year_built=2022,
        ),
        models.Listing(
            url="https://www.homes.com/property/5832-red-fox-dr-spotsylvania-va/cxqxmj13js52m",
            address="5832 Red Fox Dr  Spotsylvania, VA  22551  ",
            description="Set on 2.37 beautifully landscaped acres with mature trees, this private retreat combines country serenity with modern comfort. A wide front porch frames the home and offers an ideal spot for quiet mornings and relaxing evenings. Inside, the family room centers around a cozy gas log fireplace, and the kitchen with gas cooking flows into the dining area and a bright sunroom suited for year-round enjoyment. The main-level owner’s suite includes a spacious ensuite bath with a jetted soaking tub and separate shower. Upstairs, two oversized bedrooms provide flexible space for family, guests, or home office needs. Outdoor living is a highlight, featuring a Trex deck, above-ground pool, and hot tub surrounded by natural privacy. Two storage sheds and a whole-home generator add everyday practicality. The location feels tucked away yet remains minutes to I-95 and a short drive to Fredericksburg, Richmond, Lake Anna, Dominion Raceway, and the future Kalahari Resort slated for Fall 2026. A newly renovated property offering peaceful country living with convenient access to major destinations.",
            price=500000,
            bedroom=3,
            bathroom=2.5,
            year_built=2009,
        ),
    ]
    session.add_all(listings)
    session.commit()
    session.close()


inspector = inspect(engine)
tables = inspector.get_table_names()
if not tables:
    create_tables()


@api.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@api.post("/predict-renovations", response_model=PredictResponse)
def predict_renovations(req: PredictRequest):
    """Accepts a property description and returns structured renovation info."""
    result = extract_renovations(req.description)
    return {"result": result}
