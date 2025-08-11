from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserPublic
from app.models.request import RequestRecord

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


@router.get("/usage")
async def my_usage(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = (
        db.query(func.count(RequestRecord.id))
        .filter(RequestRecord.user_id == current_user.id)
        .scalar()
        or 0
    )
    tokens_in_sum = (
        db.query(func.coalesce(func.sum(RequestRecord.tokens_in), 0))
        .filter(RequestRecord.user_id == current_user.id)
        .scalar()
        or 0
    )
    tokens_out_sum = (
        db.query(func.coalesce(func.sum(RequestRecord.tokens_out), 0))
        .filter(RequestRecord.user_id == current_user.id)
        .scalar()
        or 0
    )
    cost_sum = (
        db.query(func.coalesce(func.sum(RequestRecord.cost_usd), 0.0))
        .filter(RequestRecord.user_id == current_user.id)
        .scalar()
        or 0.0
    )
    by_provider = (
        db.query(RequestRecord.model_provider, func.count(RequestRecord.id))
        .filter(RequestRecord.user_id == current_user.id)
        .group_by(RequestRecord.model_provider)
        .all()
    )
    return {
        "total": int(total),
        "tokens_in": int(tokens_in_sum),
        "tokens_out": int(tokens_out_sum),
        "cost_usd": float(cost_sum),
        "by_provider": [{"provider": p, "count": c} for p, c in by_provider],
    } 