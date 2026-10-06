from sqlalchemy import select
from sqlalchemy.orm import Session

from models.site import SiteTextModel
from services.errors import NotFound

DEFAULTS = {
    "inicio": {
        "titulo": "Patrimônio não se compra,",
        "destaque": "se constrói sob tese.",
        "abertura": "Imóveis com tese. Nas praças que fazem sentido para o seu patrimônio, selecionados, governados e executados sob a chancela +55.",
    },
    "rodape": {
        "texto": "Imóveis com tese. Nas praças que fazem sentido para o seu patrimônio.",
    },
}

def get_texts(db: Session, page: str) -> dict:
    if page not in DEFAULTS:
        raise NotFound()

    texts = dict(DEFAULTS[page])
    stmt = select(SiteTextModel).where(SiteTextModel.page == page)

    for row in db.scalars(stmt):
        texts[row.field] = row.value

    return texts

def save_texts(db: Session, page: str, fields: dict) -> dict:
    if page not in DEFAULTS:
        raise NotFound()

    stmt = select(SiteTextModel).where(SiteTextModel.page == page)
    current = {row.field: row for row in db.scalars(stmt)}

    for field, value in fields.items():
        value = value.strip()
        if field in current:
            current[field].value = value
        else:
            db.add(SiteTextModel(page=page, field=field, value=value))

    db.commit()

    return get_texts(db, page)
