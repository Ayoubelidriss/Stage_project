from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL, READONLY_DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
readonly_engine = create_engine(READONLY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadonlySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=readonly_engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_readonly_db():
    db = ReadonlySessionLocal()
    try:
        yield db
    finally:
        db.close()
