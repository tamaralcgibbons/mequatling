# backend/db/__init__.py
from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Single declarative Base used by ALL models
class Base(DeclarativeBase):
    pass

# Choose your DB URL (env, or fallback to local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./farm.db"

# SQLite needs this connect arg in single-threaded dev
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
