# database.py
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database credentials
DB_USER = 'root'
DB_PASSWORD = '09644373'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'test'

# First, connect to MySQL server (without specifying DB) to create the DB if it doesn't exist
connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    port=int(DB_PORT)
)

with connection.cursor() as cursor:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    print(f"✅ Database '{DB_NAME}' checked/created successfully.")
connection.close()

# Now connect using SQLAlchemy to the specified database
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)

# Create SessionLocal for use in other modules
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
