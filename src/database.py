from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_USER = environ.get('DB_USER')
DB_PASSWD = environ.get('DB_PASSWD')
DB_NAME = environ.get('DB_NAME')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWD}@postgres:5432/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
