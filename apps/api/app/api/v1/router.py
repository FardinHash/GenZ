from fastapi import APIRouter

from app.api.v1.endpoints import auth, user, keys, generate, billing, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(keys.router, prefix="/keys", tags=["keys"])
api_router.include_router(generate.router, tags=["generate"])  # /generate
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) 