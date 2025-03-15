# app/core/config.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Update with your PostgreSQL credentials and database name.
SQLALCHEMY_DATABASE_URL = "postgresql://thanikella_nikhil:nikhil123@localhost/mydb"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()