from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token

router = APIRouter()


@router.post("/signup")
async def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=str(payload.email), password_hash=get_password_hash(payload.password), plan_id="Basic")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
        "token_type": "bearer",
    }


@router.post("/login")
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
        "token_type": "bearer",
    }


@router.post("/token")
async def oauth_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    token = authorization.split(" ", 1)[1]
    payload = decode_refresh_token(token)
    if not payload or payload.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {
        "access_token": create_access_token(subject=str(user_id)),
        "token_type": "bearer",
    } 