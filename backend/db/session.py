import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _database_url() -> str:
    """
    Use env DATABASE_URL if set.
    Defaults to a local SQLite file at backend/db/app.db.
    Examples:
      - sqlite:///backend/db/app.db
      - postgresql+psycopg2://user:pass@localhost:5432/herd
    """
    url = os.getenv("DATABASE_URL", "sqlite:///backend/db/app.db")
    # Ensure sqlite file directory exists
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return url

DATABASE_URL = "sqlite:///c:/Users/User/mequatling/farm.db"

# SQLite needs a special flag for multithreaded FastAPI use
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    future=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
