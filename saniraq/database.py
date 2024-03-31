from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLA_DB_URL = "sqlite:///./sql_app.db"

engine = create_engine(SQLA_DB_URL, connect_args = {"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()