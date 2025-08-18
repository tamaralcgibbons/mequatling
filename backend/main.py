from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
import os

from backend.db import Base, engine
from backend.routers import animals, camps, groups, stats, stocks, uploads, history
from backend.routers.weights import router as weights_router
from backend.routers.vaccinations import router as vaccinations_router
from backend.models.animal import Animal
from backend.models.history import AnimalHistory
from backend.routers.vaccines import router as vaccines_router

app = FastAPI()

# CORS: keep dev origins; when serving the SPA from the same origin (8001), CORS won’t be used by the app itself
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static media (for uploaded photos) ---
app.mount("/media", StaticFiles(directory="backend/media"), name="media")

# --- DB schema (create if not exists) ---
Base.metadata.create_all(bind=engine)

# ---------------- API under /api ----------------
api = APIRouter(prefix="/api")

api.include_router(stats.router)
api.include_router(animals.router)
api.include_router(camps.router)
api.include_router(groups.router)
api.include_router(stocks.router)
app.include_router(vaccinations_router, prefix="/api/vaccinations")
api.include_router(uploads.router)
api.include_router(history.router)
app.include_router(weights_router, prefix="/api/weights")
app.include_router(vaccines_router, prefix="/api/vaccines")

# Optional health check at /api/health
@api.get("/health")
def health():
    return {"ok": True}

app.include_router(api)

# -------------- Serve built frontend --------------
# Adjust this path if your repo layout differs:
# repo/
#   backend/
#     main.py  <-- this file
#   frontend/
#     dist/    <-- after `npm run build`
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if not os.path.isdir(frontend_dir):
    raise RuntimeError(f"Frontend build not found: {frontend_dir}. Run `npm run build` in the frontend.")

# Serve the SPA at root
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# SPA fallback for client-side routes (anything not matched above and not starting with /api)
@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api"):
        return {"detail": "Not Found"}  # API routes are handled by routers above
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# -------------- Debug: print registered routes --------------
from fastapi.routing import APIRoute
print("\nRegistered routes:")
for r in app.routes:
    if isinstance(r, APIRoute):
        methods = ",".join(sorted(r.methods))
        print(f"{methods:7s} {r.path}")
print()
