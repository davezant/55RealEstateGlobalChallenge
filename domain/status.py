VISIBLE = ("publicado", "reservado", "vendido")

OFFERED = ("rascunho", "publicado", "reservado")

WHATSAPP = ("publicado", "reservado")

ALL = ("rascunho", "publicado", "reservado", "vendido", "arquivado")

TRANSITIONS = {
    "rascunho": ("publicado", "arquivado"),
    "publicado": ("rascunho", "reservado", "vendido", "arquivado"),
    "reservado": ("publicado", "vendido", "arquivado"),
    "vendido": ("arquivado",),
    "arquivado": ("rascunho",),
}

MIN_PHOTOS = 1
MAX_PHOTOS = 12

def is_visible(status: str) -> bool:
    return status in VISIBLE

def has_whatsapp(status: str) -> bool:
    return status in WHATSAPP

def transition_error(current: str, target: str, was_sold: bool) -> str | None:
    if target not in ALL:
        return "situacao_invalida"
    if current == target:
        return None
    if was_sold and target in OFFERED:
        return "vendido_irreversivel"
    if target not in TRANSITIONS.get(current, ()):
        return "transicao_invalida"
    return None

def publication_error(photo_alts: list[str]) -> str | None:
    if len(photo_alts) < MIN_PHOTOS:
        return "foto_obrigatoria"
    if any(not (alt or "").strip() for alt in photo_alts):
        return "descricao_foto_obrigatoria"
    return None
