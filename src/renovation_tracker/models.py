from sqlalchemy import Column, Integer, String, Boolean, Double, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Listing(Base):
    __tablename__ = "listings"

    listing_id = Column(Integer, primary_key=True,index=True, autoincrement=True)
    url = Column(String(100),nullable=False)
    address = Column(String(100),unique=True,nullable=False)
    description = Column(String(2000),nullable=False)
    price = Column(Double)
    renovations = relationship('Renovations', back_populates='listing')
    photos = relationship('Photos', back_populates='listing')

class Renovations(Base):
    __tablename__ = "renovations"
    renovation_id = Column(Integer, primary_key = True, index = True, autoincrement=True)
    bedroom = Column(Boolean, default = False)
    kitchen = Column(Boolean, default = False)
    living_room = Column(Boolean, default = False)
    bathroom = Column(Boolean, default = False)
    basement = Column(Boolean, default = False)
    listing_id = Column(Integer, ForeignKey('listings.listing_id'))
    listing = relationship('Listing', back_populates = 'renovations')

class Photos(Base):
    __tablename__ = "photos"
    photo_id = Column(Integer,primary_key=True, index = True)
    url = Column(String(100),nullable=False)
    room_type= Column(String(100))
    listing_id = Column(Integer, ForeignKey('listings.listing_id'))
    listing = relationship('Listing', back_populates = 'photos')
