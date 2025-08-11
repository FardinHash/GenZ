from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user, get_db
from app.core.crypto import decrypt_value
from app.core.rate_limit import check_rate_limit
from app.core.billing import estimate_tokens, compute_cost_usd
from app.models.key import ApiKey
from app.models.user import User
from app.models.request import RequestRecord
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
    allowed, remaining = check_rate_limit(str(current_user.id))
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    if not req.use_user_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server key flow not configured")

    api_key = _resolve_user_key(db, current_user.id, req.model_provider)
    adapter = get_adapter(req.model_provider)

    url_str = str(req.context.url) if (req.context and req.context.url) else None
    domain, path = RequestRecord.parse_domain_path(url_str)
    rec = RequestRecord(user_id=current_user.id, domain=domain, path=path, model=req.model, model_provider=req.model_provider, status="started")
    db.add(rec)
    db.commit()
    db.refresh(rec)

    try:
        result = adapter.generate(current_user, req, api_key)
        # token and cost estimation
        prompt_text = (req.prompt or "")
        if req.context and req.context.selected_text:
            prompt_text += "\n\nSelected:\n" + req.context.selected_text
        tin = estimate_tokens(req.model_provider, prompt_text, req.model)
        tout = estimate_tokens(req.model_provider, result.output_text, req.model)
        rec.tokens_in = tin
        rec.tokens_out = tout
        rec.cost_usd = compute_cost_usd(req.model_provider, req.model, tin, tout)
        rec.status = "success"
        db.add(rec)
        db.commit()
        return result
    except Exception as e:
        rec.status = "error"
        db.add(rec)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/generate/stream")
async def generate_stream(req: GenerationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed, remaining = check_rate_limit(str(current_user.id))
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    if not req.use_user_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Server key flow not configured")

    api_key = _resolve_user_key(db, current_user.id, req.model_provider)
    adapter = get_adapter(req.model_provider)

    url_str = str(req.context.url) if (req.context and req.context.url) else None
    domain, path = RequestRecord.parse_domain_path(url_str)
    rec = RequestRecord(user_id=current_user.id, domain=domain, path=path, model=req.model, model_provider=req.model_provider, status="streaming")
    db.add(rec)
    db.commit()

    # pre-estimate prompt tokens as above
    prompt_text = (req.prompt or "")
    if req.context and req.context.selected_text:
        prompt_text += "\n\nSelected:\n" + req.context.selected_text
    rec.tokens_in = estimate_tokens(req.model_provider, prompt_text, req.model)
    db.add(rec)
    db.commit()

    def event_gen():
        out_total = 0
        try:
            for delta in adapter.generate_stream(current_user, req, api_key):
                out_total += estimate_tokens(req.model_provider, delta, req.model)
                yield f"data: {delta}\n\n"
            yield "data: [DONE]\n\n"
            rec.tokens_out = out_total
            rec.cost_usd = compute_cost_usd(req.model_provider, req.model, rec.tokens_in or 0, rec.tokens_out or 0)
            rec.status = "success"
            db.add(rec)
            db.commit()
        except Exception as e:
            rec.status = "canceled" if out_total > 0 else "error"
            db.add(rec)
            db.commit()
            if out_total == 0:
                yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/generate/{request_id}/status")
async def generate_status(request_id: str):
    return {"detail": f"status for {request_id} not implemented"} 