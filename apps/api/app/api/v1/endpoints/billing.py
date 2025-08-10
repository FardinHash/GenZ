from fastapi import APIRouter

router = APIRouter()


@router.post("/subscribe")
async def subscribe():
    return {"detail": "subscribe not implemented"}


@router.post("/webhook")
async def webhook():
    return {"detail": "webhook not implemented"} 