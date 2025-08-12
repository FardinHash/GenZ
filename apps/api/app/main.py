from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.db.base import Base
from app.db.session import engine
from app.models.plan import Plan


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url=f"{settings.api_v1_prefix}/docs",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import Session

    with Session(engine) as db:
      existing = {p.name for p in db.query(Plan).all()}
      seeds = [
        ("Basic", 0.0, 5000),
        ("Pro", 9.0, 100000),
        ("Premium", 29.0, 500000),
      ]
      for name, price, quota in seeds:
        if name not in existing:
          db.add(Plan(name=name, monthly_price=price, token_quota=quota))
      db.commit()


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"} 