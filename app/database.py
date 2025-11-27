from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    from fastapi import Depends

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return Depends(_get_db)
