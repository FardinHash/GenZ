from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.request import RequestRecord
from app.models.plan import Plan


def get_user_plan(db: Session, user: User) -> Plan:
    plan_name = user.plan_id or 'Basic'
    plan = db.query(Plan).filter(Plan.name == plan_name).first()
    if plan:
        return plan
    # default Basic if missing
    plan = Plan(name='Basic', monthly_price=0.0, token_quota=5000)
    db.add(plan)
    db.commit()
    return plan


def get_month_start(dt: datetime | None = None) -> datetime:
    now = dt or datetime.now(tz=timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def monthly_tokens_used(db: Session, user: User) -> int:
    start = get_month_start()
    total_in = (
        db.query(func.coalesce(func.sum(RequestRecord.tokens_in), 0))
        .filter(RequestRecord.user_id == user.id, RequestRecord.created_at >= start)
        .scalar()
        or 0
    )
    total_out = (
        db.query(func.coalesce(func.sum(RequestRecord.tokens_out), 0))
        .filter(RequestRecord.user_id == user.id, RequestRecord.created_at >= start)
        .scalar()
        or 0
    )
    return int(total_in) + int(total_out)


def quota_remaining(db: Session, user: User) -> int:
    plan = get_user_plan(db, user)
    used = monthly_tokens_used(db, user)
    return max(0, int(plan.token_quota) - used) 