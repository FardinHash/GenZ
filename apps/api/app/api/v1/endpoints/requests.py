from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.request import RequestRecord
from app.models.user import User
from app.schemas.requests import RequestPublic

router = APIRouter()


@router.get("", response_model=list[RequestPublic])
async def list_my_requests(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(RequestRecord)
        .filter(RequestRecord.user_id == current_user.id)
        .order_by(RequestRecord.created_at.desc())
        .limit(max(1, min(200, limit)))
        .all()
    )
    return rows 