from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.request import RequestRecord

router = APIRouter()


def verify_admin(x_admin_secret: str | None = Header(default=None)):
    settings = get_settings()
    if not x_admin_secret or x_admin_secret != settings.admin_api_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")


@router.get("/usage")
async def usage(db: Session = Depends(get_db), _=Depends(verify_admin)):
    total = db.query(func.count(RequestRecord.id)).scalar() or 0
    by_provider = (
        db.query(RequestRecord.model_provider, func.count(RequestRecord.id))
        .group_by(RequestRecord.model_provider)
        .all()
    )
    by_model = (
        db.query(RequestRecord.model, func.count(RequestRecord.id))
        .group_by(RequestRecord.model)
        .order_by(func.count(RequestRecord.id).desc())
        .limit(20)
        .all()
    )
    tokens_in_sum = db.query(func.coalesce(func.sum(RequestRecord.tokens_in), 0)).scalar() or 0
    tokens_out_sum = db.query(func.coalesce(func.sum(RequestRecord.tokens_out), 0)).scalar() or 0
    cost_sum = db.query(func.coalesce(func.sum(RequestRecord.cost_usd), 0.0)).scalar() or 0.0
    return {
        "total": total,
        "tokens_in": int(tokens_in_sum),
        "tokens_out": int(tokens_out_sum),
        "cost_usd": float(cost_sum),
        "by_provider": [{"provider": p, "count": c} for p, c in by_provider],
        "by_model": [{"model": m, "count": c} for m, c in by_model],
    }


@router.get("/requests")
async def requests():
    return {"detail": "requests not implemented"} 