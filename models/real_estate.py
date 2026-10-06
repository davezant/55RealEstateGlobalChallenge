from .base import Base
from typing import List, Optional
from decimal import Decimal
from enum import Enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, ForeignKey, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

class RealEstateTypeEnum(str, Enum):
    APARTMENT = "apartamento"
    PENTHOUSE = "penthouse"
    VILLA = "villa"
    ESTATE = "estate"

class StatusEnum(str, Enum):
    DRAFT = "rascunho"
    PUBLISHED = "publicado"
    RESERVED = "reservado"
    SOLD = "vendido"
    ARCHIVED = "arquivado"

class CurrencyEnum(str, Enum):
    REAL = "BRL"
    DOLLAR = "USD"
    DIRHAM = "AED"

class RealEstateModel(Base):
    __tablename__ = "real_estate"

    real_estate_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ref: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    
    property_type: Mapped[RealEstateTypeEnum] = mapped_column(SQLEnum(RealEstateTypeEnum), nullable=False)
    
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    price_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    price_currency: Mapped[Optional[CurrencyEnum]] = mapped_column(SQLEnum(CurrencyEnum), nullable=True)     

    private_area: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    built_area: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    land_area: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parking_spaces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    partner: Mapped[str] = mapped_column(String(100), nullable=False)
    
    status: Mapped[StatusEnum] = mapped_column(
        SQLEnum(StatusEnum), nullable=False, default=StatusEnum.DRAFT
    )

    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    images: Mapped[List["RealEstatePhotoModel"]] = relationship(
        "RealEstatePhotoModel",
        back_populates="real_estate",
        cascade="all, delete-orphan",
        order_by="RealEstatePhotoModel.order"
    )

class RealEstatePhotoModel(Base):
    __tablename__ = "real_estate_photos"

    photo_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    real_estate_id: Mapped[int] = mapped_column(Integer, ForeignKey("real_estate.real_estate_id"), nullable=False)
    
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    alt: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    real_estate: Mapped["RealEstateModel"] = relationship(
        "RealEstateModel", 
        back_populates="images"
    )
