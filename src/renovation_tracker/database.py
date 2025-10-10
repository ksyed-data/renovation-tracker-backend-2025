from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

URL = 'mysql+pymysql://root:renovation_tracker2025@localhost:3306/renovation_trackerdb'

engine = create_engine(URL)

Session = sessionmaker(bind=engine, autoflush=True)
Base = declarative_base()