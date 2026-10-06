import os
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import quote

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain import status as situation
from domain.money import Money, sort_key_usd
from domain.real_estate import PLACES, rule_errors, typology_for
from models.real_estate import (
    CurrencyEnum,
    RealEstateModel,
    RealEstatePhotoModel,
    RealEstateTypeEnum,
    StatusEnum,
)
from schemas.real_estate import RealEstateCreateSchema
from services import media
from services.errors import NotFound, ValidationFailed

ORDER_OPTIONS = ("recentes", "preco_asc", "preco_desc")

CANONICAL_TO_SCHEMA = {
    "ref": "ref",
    "slug": "slug",
    "titulo": "title",
    "tipologia": "property_type",
    "pais": "country",
    "cidade": "city",
    "bairro": "neighborhood",
    "descricao": "description",
    "preco_valor": "price_amount",
    "preco_moeda": "price_currency",
    "area_privativa": "private_area",
    "area_construida": "built_area",
    "area_terreno": "land_area",
    "quartos": "bedrooms",
    "banheiros": "bathrooms",
    "vagas": "parking_spaces",
    "andar": "floor",
    "parceiro": "partner",
}

SCHEMA_TO_CANONICAL = {value: key for key, value in CANONICAL_TO_SCHEMA.items()}

API_TO_CANONICAL = {
    "areaPrivativa": "area_privativa",
    "areaConstruida": "area_construida",
    "areaTerreno": "area_terreno",
}

CANONICAL_TO_API = {
    "area_privativa": "areaPrivativa",
    "area_construida": "areaConstruida",
    "area_terreno": "areaTerreno",
    "preco_valor": "preco",
    "preco_moeda": "preco",
}

DECIMAL_FIELDS = ("preco_valor", "area_privativa", "area_construida", "area_terreno")

INTEGER_FIELDS = ("quartos", "banheiros", "vagas", "andar")

TEXT_FIELDS = ("ref", "slug", "titulo", "tipologia", "pais", "cidade", "bairro", "descricao", "preco_moeda", "parceiro")

PYDANTIC_CODES = {
    "missing": "obrigatorio",
    "string_too_short": "muito_curto",
    "string_too_long": "muito_longo",
    "greater_than": "deve_ser_positivo",
    "greater_than_equal": "nao_negativo",
    "string_pattern_mismatch": "formato_invalido",
    "decimal_max_places": "casas_decimais",
    "decimal_max_digits": "digitos_demais",
    "decimal_whole_digits": "digitos_demais",
}

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

INVALID = "__invalido__"

def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:100].strip("-")

def decimal_text(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return INVALID

def integer_value(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return INVALID

def text_value(value):
    if value is None or isinstance(value, str):
        return value
    return INVALID

def from_api(body: dict) -> dict:
    data = {}

    for key, value in body.items():
        if key == "preco":
            if value is None:
                data["preco_valor"] = None
            elif isinstance(value, dict):
                if "valor" in value:
                    data["preco_valor"] = decimal_text(value["valor"])
                if "moeda" in value:
                    data["preco_moeda"] = text_value(value["moeda"])
            else:
                data["preco_valor"] = INVALID
            continue

        name = API_TO_CANONICAL.get(key, key)

        if name in DECIMAL_FIELDS:
            data[name] = decimal_text(value)
        elif name in INTEGER_FIELDS:
            data[name] = integer_value(value)
        elif name in TEXT_FIELDS:
            data[name] = text_value(value)

    return data

def from_form(form: dict) -> dict:
    data = {}

    for name in CANONICAL_TO_SCHEMA:
        if name not in form:
            continue
        value = form[name]
        value = value.strip() if isinstance(value, str) else value
        data[name] = value or None

    if data.get("ref"):
        data["ref"] = data["ref"].upper()

    return data

def error_field_for_api(field: str) -> str:
    return CANONICAL_TO_API.get(field, field)

def to_canonical(prop: RealEstateModel) -> dict:
    return {
        "ref": prop.ref,
        "slug": prop.slug,
        "titulo": prop.title,
        "tipologia": prop.property_type.value,
        "pais": prop.country,
        "cidade": prop.city,
        "bairro": prop.neighborhood,
        "descricao": prop.description,
        "preco_valor": None if prop.price_amount is None else str(prop.price_amount),
        "preco_moeda": None if prop.price_currency is None else prop.price_currency.value,
        "area_privativa": None if prop.private_area is None else str(prop.private_area),
        "area_construida": None if prop.built_area is None else str(prop.built_area),
        "area_terreno": None if prop.land_area is None else str(prop.land_area),
        "quartos": prop.bedrooms,
        "banheiros": prop.bathrooms,
        "vagas": prop.parking_spaces,
        "andar": prop.floor,
        "parceiro": prop.partner,
    }

def validate(db: Session, data: dict, complete: bool, current: RealEstateModel | None) -> dict:
    data = dict(data)
    errors: list[tuple[str, str]] = []

    if data.get("pais") in PLACES and not data.get("preco_moeda"):
        data["preco_moeda"] = PLACES[data["pais"]].currency

    if not data.get("slug") and data.get("titulo") and data.get("ref"):
        data["slug"] = slugify(f"{data['titulo']} {data['ref']}")

    payload = {
        CANONICAL_TO_SCHEMA[name]: value
        for name, value in data.items()
        if name in CANONICAL_TO_SCHEMA
    }

    parsed = None
    try:
        parsed = RealEstateCreateSchema.model_validate(payload)
    except ValidationError as exc:
        for error in exc.errors():
            schema_name = str(error["loc"][0]) if error["loc"] else ""
            field = SCHEMA_TO_CANONICAL.get(schema_name, schema_name)
            errors.append((field, PYDANTIC_CODES.get(error["type"], "invalido")))

    errors.extend(rule_errors(data, complete))

    slug = data.get("slug")
    if slug and not SLUG_PATTERN.match(slug):
        errors.append(("slug", "formato_invalido"))

    if data.get("ref"):
        stmt = select(RealEstateModel.real_estate_id).where(RealEstateModel.ref == data["ref"])
        found = db.scalar(stmt)
        if found is not None and (current is None or found != current.real_estate_id):
            errors.append(("ref", "ref_duplicada"))

    if slug:
        stmt = select(RealEstateModel.real_estate_id).where(RealEstateModel.slug == slug)
        found = db.scalar(stmt)
        if found is not None and (current is None or found != current.real_estate_id):
            errors.append(("slug", "slug_duplicado"))

    unique = list(dict.fromkeys(errors))
    if unique or parsed is None:
        raise ValidationFailed(unique)

    cleaned = parsed.model_dump(exclude={"images", "status"})
    cleaned["property_type"] = RealEstateTypeEnum(parsed.property_type.value)
    cleaned["price_currency"] = CurrencyEnum(parsed.price_currency.value)

    return cleaned

def create_property(db: Session, data: dict) -> RealEstateModel:
    cleaned = validate(db, data, complete=False, current=None)

    prop = RealEstateModel(**cleaned, status=StatusEnum.DRAFT)
    db.add(prop)
    db.commit()
    db.refresh(prop)

    return prop

def update_property(db: Session, prop: RealEstateModel, changes: dict) -> RealEstateModel:
    data = {**to_canonical(prop), **changes}
    complete = situation.is_visible(prop.status.value)

    cleaned = validate(db, data, complete=complete, current=prop)

    for name, value in cleaned.items():
        setattr(prop, name, value)

    db.commit()
    db.refresh(prop)

    return prop

def get_by_id(db: Session, real_estate_id: int) -> RealEstateModel:
    prop = db.get(RealEstateModel, real_estate_id)
    if prop is None:
        raise NotFound()
    return prop

def get_by_slug(db: Session, slug: str) -> RealEstateModel:
    stmt = select(RealEstateModel).where(RealEstateModel.slug == slug)
    prop = db.scalar(stmt)
    if prop is None or not situation.is_visible(prop.status.value):
        raise NotFound()
    return prop

def change_status(db: Session, prop: RealEstateModel, target: str) -> RealEstateModel:
    current = prop.status.value
    was_sold = prop.sold_at is not None

    reason = situation.transition_error(current, target, was_sold)
    if reason:
        raise ValidationFailed([("situacao", reason)])

    if current == target:
        return prop

    if situation.is_visible(target):
        data = to_canonical(prop)
        errors = rule_errors(data, complete=True)
        photo_error = situation.publication_error([photo.alt for photo in prop.images])
        if photo_error:
            errors.append(("imagens", photo_error))
        if errors:
            raise ValidationFailed(errors)

    prop.status = StatusEnum(target)
    if target == "vendido":
        prop.sold_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prop)

    return prop

def add_photo(db: Session, prop: RealEstateModel, file_storage, alt: str | None, upload_dir: str) -> RealEstatePhotoModel:
    alt = (alt or "").strip()

    if not alt:
        raise ValidationFailed([("alt", "obrigatorio")])
    if len(alt) > 255:
        raise ValidationFailed([("alt", "muito_longo")])
    if len(prop.images) >= situation.MAX_PHOTOS:
        raise ValidationFailed([("imagens", "limite_fotos")])

    filename = media.save_upload(file_storage, upload_dir)

    next_order = max((photo.order for photo in prop.images), default=-1) + 1

    photo = RealEstatePhotoModel(
        real_estate_id=prop.real_estate_id,
        file_path=filename,
        alt=alt,
        order=next_order,
        is_cover=len(prop.images) == 0,
    )
    db.add(photo)
    db.commit()
    db.refresh(prop)

    return photo

def update_photo_alt(db: Session, prop: RealEstateModel, photo_id: int, alt: str) -> None:
    photo = next((item for item in prop.images if item.photo_id == photo_id), None)
    if photo is None:
        raise NotFound()

    alt = (alt or "").strip()
    if not alt:
        raise ValidationFailed([("alt", "obrigatorio")])
    if len(alt) > 255:
        raise ValidationFailed([("alt", "muito_longo")])

    photo.alt = alt
    db.commit()

def delete_photo(db: Session, prop: RealEstateModel, photo_id: int, upload_dir: str) -> None:
    photo = next((item for item in prop.images if item.photo_id == photo_id), None)
    if photo is None:
        raise NotFound()

    if situation.is_visible(prop.status.value) and len(prop.images) <= situation.MIN_PHOTOS:
        raise ValidationFailed([("imagens", "foto_obrigatoria")])

    was_cover = photo.is_cover
    filename = photo.file_path

    db.delete(photo)
    db.commit()
    db.refresh(prop)

    if was_cover and prop.images:
        prop.images[0].is_cover = True
        db.commit()

    media.remove_file(upload_dir, filename)

def price_of(prop: RealEstateModel) -> Money | None:
    if prop.price_amount is None or prop.price_currency is None:
        return None
    return Money(Decimal(prop.price_amount), prop.price_currency.value)

def list_public(db: Session, place: str | None = None, order: str = "recentes") -> list[RealEstateModel]:
    visible = [StatusEnum(value) for value in situation.VISIBLE]
    stmt = select(RealEstateModel).where(RealEstateModel.status.in_(visible))

    if place:
        stmt = stmt.where(RealEstateModel.country == place)

    items = list(db.scalars(stmt.order_by(RealEstateModel.real_estate_id.desc())))

    if order == "preco_asc":
        items.sort(key=lambda prop: sort_key_usd(price_of(prop)))
    elif order == "preco_desc":
        priced = [prop for prop in items if price_of(prop) is not None]
        unpriced = [prop for prop in items if price_of(prop) is None]
        priced.sort(key=lambda prop: sort_key_usd(price_of(prop)), reverse=True)
        items = priced + unpriced

    return items

def list_all(db: Session) -> list[RealEstateModel]:
    stmt = select(RealEstateModel).order_by(RealEstateModel.real_estate_id.desc())
    return list(db.scalars(stmt))

def cover_of(prop: RealEstateModel) -> RealEstatePhotoModel | None:
    for photo in prop.images:
        if photo.is_cover:
            return photo
    return prop.images[0] if prop.images else None

def photo_url(photo: RealEstatePhotoModel) -> str:
    return f"/media/{photo.file_path}"

def whatsapp_url(prop: RealEstateModel) -> str | None:
    number = os.getenv("WHATSAPP_E164", "")
    digits = re.sub(r"\D", "", number)

    if not digits or not situation.has_whatsapp(prop.status.value):
        return None

    message = f"Olá, tenho interesse no imóvel {prop.ref}, {prop.title}."
    return f"https://wa.me/{digits}?text={quote(message)}"

def area_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    text = f"{value:,.2f}"
    text = text.replace(",", "#").replace(".", ",").replace("#", ".")
    return text[:-3] if text.endswith(",00") else text

def to_list_item(prop: RealEstateModel) -> dict:
    price = price_of(prop)
    cover = cover_of(prop)

    return {
        "ref": prop.ref,
        "slug": prop.slug,
        "titulo": prop.title,
        "tipologia": prop.property_type.value,
        "situacao": prop.status.value,
        "pais": prop.country,
        "cidade": prop.city,
        "bairro": prop.neighborhood,
        "preco": None if price is None else price.to_dict(),
        "capa": None if cover is None else {"url": photo_url(cover), "alt": cover.alt},
    }

def to_detail(prop: RealEstateModel) -> dict:
    price = price_of(prop)
    typology = typology_for(prop.property_type.value)
    per_m2 = typology.price_per_m2(price, to_canonical(prop)) if typology else None

    detail = to_list_item(prop)
    detail.update({
        "descricao": prop.description,
        "quartos": prop.bedrooms,
        "banheiros": prop.bathrooms,
        "vagas": prop.parking_spaces,
        "andar": prop.floor,
        "areaPrivativa": None if prop.private_area is None else f"{prop.private_area:.2f}",
        "areaConstruida": None if prop.built_area is None else f"{prop.built_area:.2f}",
        "areaTerreno": None if prop.land_area is None else f"{prop.land_area:.2f}",
        "precoPorM2": None if per_m2 is None else per_m2.to_dict(),
        "imagens": [{"url": photo_url(photo), "alt": photo.alt} for photo in prop.images],
        "whatsappUrl": whatsapp_url(prop),
    })

    return detail

def to_list_view(prop: RealEstateModel) -> dict:
    item = to_list_item(prop)
    price = price_of(prop)
    typology = typology_for(prop.property_type.value)

    item["preco_texto"] = price.format() if price else "Preço sob consulta"
    item["praca_nome"] = PLACES[prop.country].name if prop.country in PLACES else prop.country
    item["tipologia_label"] = typology.label if typology else prop.property_type.value
    item["real_estate_id"] = prop.real_estate_id

    return item

def to_detail_view(prop: RealEstateModel) -> dict:
    detail = to_detail(prop)
    view = to_list_view(prop)
    view.update(detail)

    price = price_of(prop)
    typology = typology_for(prop.property_type.value)
    per_m2 = typology.price_per_m2(price, to_canonical(prop)) if typology else None

    view["preco_m2_texto"] = per_m2.format() if per_m2 else None
    view["area_base_label"] = "Área privativa" if typology and typology.area_basis == "area_privativa" else "Área construída"
    base_area = prop.private_area if typology and typology.area_basis == "area_privativa" else prop.built_area
    view["area_base_texto"] = f"{area_text(base_area)} m²" if base_area is not None else None
    view["area_terreno_texto"] = f"{area_text(prop.land_area)} m²" if prop.land_area is not None else None
    view["parceiro"] = prop.partner

    return view
