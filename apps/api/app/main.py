from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.db.base import Base
from app.db.session import engine
from app.models.plan import Plan

# Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

REQUEST_COUNT = Counter("api_requests_total", "Total API requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "API request latency", ["method", "path"])

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, integrations=[FastApiIntegration()], environment=settings.environment, release=settings.version)

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


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method
    start = time.time()
    try:
        response = await call_next(request)
        status_code = getattr(response, "status_code", 500)
        REQUEST_COUNT.labels(method=method, path=path, status=str(status_code)).inc()
        return response
    finally:
        duration = time.time() - start
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


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