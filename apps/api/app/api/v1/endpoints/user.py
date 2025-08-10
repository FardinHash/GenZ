from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/settings", response_model=UserPublic)
async def update_settings(payload: dict[str, Any], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.settings = payload
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user 