import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_engine():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("❌ ERROR CRÍTICO: DATABASE_URL no encontrada en el sistema.")

    return create_engine(url)

engine = None
SessionLocal = None

def init_db():
    global engine, SessionLocal
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.models import Company, FastTrack
    Base.metadata.create_all(bind=engine)