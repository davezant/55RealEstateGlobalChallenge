from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class SiteTextModel(Base):
    __tablename__ = "site_texts"

    __table_args__ = (UniqueConstraint("page", "field", name="uq_site_texts_page_field"),)

    text_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    page: Mapped[str] = mapped_column(String(40), nullable=False)

    field: Mapped[str] = mapped_column(String(40), nullable=False)

    value: Mapped[str] = mapped_column(Text, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
