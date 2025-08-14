from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.db import Base, engine
from backend.routers import animals, camps, groups, stats, stocks, uploads, vaccinations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # or ["*"] for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static media (for uploaded photos) ---
app.mount("/media", StaticFiles(directory="backend/media"), name="media")

# --- DB schema (create if not exists) ---
Base.metadata.create_all(bind=engine)

# --- Routers ---
app.include_router(stats.router)
app.include_router(animals.router)
app.include_router(camps.router)
app.include_router(groups.router)
app.include_router(stocks.router)
app.include_router(vaccinations.router)
app.include_router(uploads.router)

@app.get("/")
def root():
    return {"ok": True}

from fastapi.routing import APIRoute
print("\nRegistered routes:")
for r in app.routes:
    if isinstance(r, APIRoute):
        methods = ",".join(sorted(r.methods))
        print(f"{methods:7s} {r.path}")
print()