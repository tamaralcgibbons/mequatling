# backend/routers/uploads.py
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, status

router = APIRouter(prefix="/animals", tags=["uploads"])

MEDIA_BASE = Path("backend/media")
GENERIC_UPLOADS_DIR = MEDIA_BASE / "uploads"
GENERIC_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

_filename_re = re.compile(r"[^A-Za-z0-9._-]+")

def safe_segment(s: str) -> str:
    # keep only alnum, dot, underscore, dash
    s = _filename_re.sub("_", s.strip())
    return s or "file"

def safe_filename(name: str) -> str:
    # strip any path; normalize weird chars
    base = os.path.basename(name or "upload.bin")
    return safe_segment(base)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def generic_upload(
    file: UploadFile = File(...),
    kind: Optional[str] = Form(default="file"),
):
    """
    Generic file upload. Returns a public path under /media/uploads/.
    - kind: optional subfolder hint (e.g., 'document', 'image')
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    safe_kind = safe_segment(kind or "file")
    subdir = GENERIC_UPLOADS_DIR / safe_kind
    subdir.mkdir(parents=True, exist_ok=True)

    ts = int(datetime.utcnow().timestamp())
    fname = f"{ts}_{safe_filename(file.filename)}"
    dest_path = subdir / fname

    # Save the file
    with dest_path.open("wb") as f:
        f.write(file.file.read())

    # public URL path (be sure main.py mounts /media to backend/media)
    public_path = f"/media/uploads/{safe_kind}/{fname}"
    return {"path": public_path}
