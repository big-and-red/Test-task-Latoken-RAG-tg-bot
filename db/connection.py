from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.config import config

engine = create_engine(config.db.url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
