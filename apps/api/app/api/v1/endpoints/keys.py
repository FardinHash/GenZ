from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.crypto import encrypt_value
from app.models.key import ApiKey
from app.models.user import User
from app.schemas.keys import ApiKeyCreate, ApiKeyPublic

router = APIRouter()


@router.post("", response_model=ApiKeyPublic, status_code=status.HTTP_201_CREATED)
async def create_key(payload: ApiKeyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    encrypted = encrypt_value(payload.key)
    rec = ApiKey(user_id=current_user.id, provider=payload.provider, key_encrypted=encrypted, key_type=payload.key_type)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("", response_model=list[ApiKeyPublic])
async def list_keys(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).order_by(ApiKey.created_at.desc()).all()
    return rows


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(key_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    db.delete(rec)
    db.commit()
    return None 