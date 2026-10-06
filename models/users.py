from enum import Enum
from datetime import date, datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Date, DateTime, Boolean, Enum as SQLEnum
from .base import Base

class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    username: Mapped[str] = mapped_column(String(126), unique=True, index=True, nullable=False)

    email: Mapped[str] = mapped_column(String(126), unique=True, index=True, nullable=False)

    hash_pwd: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

class RevokedTokenModel(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

