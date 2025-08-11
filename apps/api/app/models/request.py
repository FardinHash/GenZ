from datetime import datetime
import uuid
from urllib.parse import urlparse

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RequestRecord(Base):
    __tablename__ = "requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    model_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    @staticmethod
    def parse_domain_path(url: str | None) -> tuple[str | None, str | None]:
        if not url:
            return None, None
        try:
            p = urlparse(url)
            return p.netloc or None, p.path or None
        except Exception:
            return None, None 