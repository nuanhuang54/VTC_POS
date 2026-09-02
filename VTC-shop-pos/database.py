#database.py - Sets up connection pool to PostgreSQL 
# and maps structural product data tables.
#
import os
from sqlalchemy import create_engine, Column, String, Integer, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import uuid

# Configuration string: database://user:password@host:port/database_name
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:VTCg4m3s@localhost:5432/pos_db")

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sku = Column(String, unique=True, nullable=False, index=True) # Barcode
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Integer, default=0, nullable=False)
    woo_product_id = Column(Integer, unique=True, index=True)

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    woo_product_id = Column(Integer, nullable=False)
    new_stock_qty = Column(Integer, nullable=False)
    status = Column(String, default="PENDING") # PENDING, FAILED, COMPLETED
    attempts = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Generates tables inside database if they don't exist yet
def init_db():
    Base.metadata.create_all(bind=engine)
