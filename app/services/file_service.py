"""File upload utilities."""
import os
import uuid
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile, HTTPException
from app.core.config import settings


ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}


def save_upload(file: UploadFile, subfolder: str) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type {ext}")

    folder = Path(settings.UPLOAD_DIR) / subfolder
    folder.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = folder / fname

    size_limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    written = 0
    with fpath.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            written += len(chunk)
            if written > size_limit:
                out.close()
                fpath.unlink(missing_ok=True)
                raise HTTPException(400, f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB")
            out.write(chunk)

    rel = f"/uploads/{subfolder}/{fname}"
    return rel
