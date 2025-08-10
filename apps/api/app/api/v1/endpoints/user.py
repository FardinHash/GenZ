from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_me():
    return {"detail": "me not implemented"}


@router.put("/me/settings")
async def update_settings():
    return {"detail": "update settings not implemented"} 