from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

URL = os.getenv("DATABASE_URL")

engine = create_engine(URL)

Session = sessionmaker(bind=engine, autoflush=True)
Base = declarative_base()
