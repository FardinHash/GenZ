from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_db
from app.core.crypto import decrypt_value
from app.models.key import ApiKey
from app.models.user import User
from app.schemas.generate import GenerationRequest, GenerationResponse
from app.services.adapters import get_adapter

router = APIRouter()


def _resolve_user_key(db: Session, user_id, provider: str) -> str:
  key_row = (
      db.query(ApiKey)
      .filter(ApiKey.user_id == user_id, ApiKey.provider == provider)
      .order_by(ApiKey.created_at.desc())
      .first()
  )
  if not key_row:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user key found for provider")
  return decrypt_value(key_row.key_encrypted)


@router.post("/generate", response_model=GenerationResponse)
async def generate(req: GenerationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not req.use_user_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server key flow not configured")

    api_key = _resolve_user_key(db, current_user.id, req.model_provider)
    adapter = get_adapter(req.model_provider)
    try:
        result = adapter.generate(current_user, req, api_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return result


@router.post("/generate/stream")
async def generate_stream(req: GenerationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not req.use_user_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server key flow not configured")

    api_key = _resolve_user_key(db, current_user.id, req.model_provider)
    adapter = get_adapter(req.model_provider)

    def event_gen():
        try:
            for delta in adapter.generate_stream(current_user, req, api_key):
                yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/generate/{request_id}/status")
async def generate_status(request_id: str):
    return {"detail": f"status for {request_id} not implemented"} 