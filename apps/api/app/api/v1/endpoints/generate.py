from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.crypto import decrypt_value
from app.models.key import ApiKey
from app.models.user import User
from app.schemas.generate import GenerationRequest, GenerationResponse
from app.services.adapters import get_adapter

router = APIRouter()


@router.post("/generate", response_model=GenerationResponse)
async def generate(req: GenerationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if req.use_user_key:
        key_row = (
            db.query(ApiKey)
            .filter(ApiKey.user_id == current_user.id, ApiKey.provider == req.model_provider)
            .order_by(ApiKey.created_at.desc())
            .first()
        )
        if not key_row:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user key found for provider")
        api_key = decrypt_value(key_row.key_encrypted)
    else:
        # Server-managed keys are out of scope for this step
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server key flow not configured")

    adapter = get_adapter(req.model_provider)
    try:
        result = adapter.generate(current_user, req, api_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return result


@router.get("/generate/{request_id}/status")
async def generate_status(request_id: str):
    return {"detail": f"status for {request_id} not implemented"} 