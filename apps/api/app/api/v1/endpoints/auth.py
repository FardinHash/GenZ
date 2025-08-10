from fastapi import APIRouter

router = APIRouter()


@router.post("/signup")
async def signup():
    return {"detail": "signup not implemented"}


@router.post("/login")
async def login():
    return {"detail": "login not implemented"}


@router.post("/refresh")
async def refresh():
    return {"detail": "refresh not implemented"} 