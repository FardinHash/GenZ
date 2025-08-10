from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate():
    return {"detail": "generation not implemented"}


@router.get("/generate/{request_id}/status")
async def generate_status(request_id: str):
    return {"detail": f"status for {request_id} not implemented"} 