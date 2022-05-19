from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import CNF

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://{}:{}@{}/{}".format(
    CNF.DB_USER, CNF.DB_PASSWORD, CNF.DB_HOST, CNF.DB_DATABASE
)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
