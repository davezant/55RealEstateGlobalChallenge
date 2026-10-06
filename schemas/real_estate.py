from enum import Enum
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

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

class RealEstateImageSchema(BaseModel):
    image_id: Optional[int] = Field(default=None)
    file_path: str = Field(..., min_length=1, max_length=255)
    alt: str = Field(..., min_length=1, max_length=255)
    is_cover: bool = Field(default=False)

class RealEstateBaseSchema(BaseModel):
    ref: str = Field(..., pattern=r"^[A-Z]{2}-\d{4}$")
    slug: str = Field(..., min_length=3, max_length=100)
    title: str = Field(..., min_length=3, max_length=100)
    property_type: RealEstateTypeEnum

    country: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=2, max_length=50)
    neighborhood: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10, max_length=1000)

    price_amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=12)
    price_currency: CurrencyEnum

    private_area: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=8)
    built_area: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=8)
    land_area: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=8)

    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    parking_spaces: Optional[int] = Field(default=None, ge=0)
    floor: Optional[int] = Field(default=None, ge=0)

    partner: str = Field(..., min_length=2, max_length=100)
    status: StatusEnum = Field(default=StatusEnum.DRAFT)
    images: List[RealEstateImageSchema] = Field(default_factory=list)


class RealEstateCreateSchema(RealEstateBaseSchema):
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100)


class RealEstateResponseSchema(RealEstateBaseSchema):
    real_estate_id: int

    class Config:
        from_attributes = True
