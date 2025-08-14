import os
from datetime import datetime
from typing import Tuple

from fastapi import UploadFile

# Base media folder is mounted at /media in main.py
MEDIA_BASE = os.environ.get("MEDIA_BASE", "backend/media")
ANIMAL_PHOTOS_DIR = os.path.join(MEDIA_BASE, "photos")


def ensure_dirs():
    os.makedirs(ANIMAL_PHOTOS_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
    # drop path separators, collapse spaces
    name = name.replace("\\", "_").replace("/", "_")
    return "_".join(name.split())


def save_upload_to_dir(upload: UploadFile, subdir: str, prefix: str = "") -> Tuple[str, str]:
    """
    Saves an UploadFile under MEDIA_BASE/<subdir>/ and returns (public_path, fs_path).
    public_path is suitable for serving via FastAPI StaticFiles mounted at /media.
    """
    ensure_dirs()
    abs_dir = os.path.join(MEDIA_BASE, subdir)
    os.makedirs(abs_dir, exist_ok=True)

    ts = int(datetime.utcnow().timestamp())
    raw_name = sanitize_filename(upload.filename or "file.bin")
    fname = f"{prefix}{ts}_{raw_name}" if prefix else f"{ts}_{raw_name}"
    fs_path = os.path.join(abs_dir, fname)
    with open(fs_path, "wb") as f:
        f.write(upload.file.read())

    # public path starts after MEDIA_BASE, exposed at /media
    rel = os.path.relpath(fs_path, MEDIA_BASE).replace("\\", "/")
    public_path = f"/media/{rel}"
    return public_path, fs_path


def save_animal_photo(upload: UploadFile, animal_id: int) -> str:
    """
    Saves an animal photo and returns the public URL path (e.g., /media/photos/123_...jpg).
    """
    public_path, _ = save_upload_to_dir(upload, subdir="photos", prefix=f"{animal_id}_")
    return public_path
