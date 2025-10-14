from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import DATABASE_URL

URL = DATABASE_URL

engine = create_engine(URL)

Session = sessionmaker(bind=engine, autoflush=True)
Base = declarative_base()