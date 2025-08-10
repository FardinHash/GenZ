from fastapi import APIRouter

router = APIRouter()


@router.get("/usage")
async def usage():
    return {"detail": "usage not implemented"}


@router.get("/requests")
async def requests():
    return {"detail": "requests not implemented"} 