"""User profile endpoints."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import UserUpdate, UserOut, UserDLUpdate, MessageResponse
from app.services.file_service import save_upload

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/dl", response_model=UserOut)
def update_dl(
    payload: UserDLUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.dl_number = payload.dl_number
    user.dl_verified = False  # admin re-verification required
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/dl-image", response_model=UserOut)
def upload_dl_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rel = save_upload(file, "dl")
    user.dl_image = rel
    user.dl_verified = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/profile-image", response_model=UserOut)
def upload_profile_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rel = save_upload(file, "profile")
    user.profile_image = rel
    db.commit()
    db.refresh(user)
    return user
