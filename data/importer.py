import csv
import os
import re
from decimal import Decimal, InvalidOperation

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

PROPERTIES_CSV = os.path.join(DATA_DIR, "imoveis-exemplo.csv")

IMAGES_DIR = os.path.join(DATA_DIR, "Imagens")

PHOTO_INDEX_CSV = os.path.join(IMAGES_DIR, "indice-das-fotos.csv")

CURRENCY_PREFIXES = (("R$", "BRL"), ("US$", "USD"), ("AED", "AED"))

UNIT_AREA_TYPES = ("apartamento", "penthouse")

def parse_number(text: str) -> Decimal | None:
    text = (text or "").strip()
    if not text:
        return None

    text = re.sub(r"\s*m(²|2)\s*$", "", text, flags=re.IGNORECASE).strip()

    multiplier = Decimal("1")
    if text and text[-1] in "Mm":
        multiplier = Decimal("1000000")
        text = text[:-1]

    text = re.sub(r"[^\d.,]", "", text)
    if not text:
        return None

    has_dot = "." in text
    has_comma = "," in text

    if has_dot and has_comma:
        decimal_sep = "." if text.rfind(".") > text.rfind(",") else ","
    elif has_dot or has_comma:
        sep = "." if has_dot else ","
        parts = text.split(sep)
        is_thousands = len(parts) > 2 or (len(parts[-1]) == 3 and multiplier == 1)
        decimal_sep = None if is_thousands else sep
    else:
        decimal_sep = None

    if decimal_sep is None:
        digits = re.sub(r"[.,]", "", text)
    else:
        integer, _, fraction = text.rpartition(decimal_sep)
        digits = re.sub(r"[.,]", "", integer) + "." + fraction

    try:
        return Decimal(digits) * multiplier
    except InvalidOperation:
        return None

def parse_price(text: str) -> tuple[Decimal | None, str | None]:
    text = (text or "").strip()
    for prefix, currency in CURRENCY_PREFIXES:
        if text.startswith(prefix):
            return parse_number(text[len(prefix):]), currency
    return None, None

def decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else f"{value:.2f}"

def integer_or_none(text: str) -> int | None:
    text = (text or "").strip()
    return int(text) if text.isdigit() else None

def text_or_none(text: str) -> str | None:
    text = (text or "").strip()
    return text or None

def read_properties(path: str = PROPERTIES_CSV) -> list[dict]:
    items = []

    with open(path, encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            price, currency = parse_price(row["preco"])
            area = decimal_text(parse_number(row["area"]))
            is_unit = row["tipologia"].strip() in UNIT_AREA_TYPES

            items.append({
                "ref": row["ref"].strip(),
                "titulo": row["titulo"].strip(),
                "pais": row["praca"].strip(),
                "cidade": row["cidade"].strip(),
                "bairro": row["bairro"].strip(),
                "tipologia": row["tipologia"].strip(),
                "descricao": row["descricao"].strip(),
                "preco_valor": decimal_text(price),
                "preco_moeda": currency,
                "area_privativa": area if is_unit else None,
                "area_construida": None if is_unit else area,
                "area_terreno": decimal_text(parse_number(row["area_terreno"])),
                "quartos": integer_or_none(row["quartos"]),
                "banheiros": integer_or_none(row["banheiros"]),
                "vagas": integer_or_none(row["vagas"]),
                "andar": integer_or_none(row["andar"]),
                "parceiro": text_or_none(row["parceiro"]),
                "situacao": row["situacao"].strip(),
            })

    return items

def read_photo_index(path: str = PHOTO_INDEX_CSV) -> dict[str, list[str]]:
    photos: dict[str, list[str]] = {}

    with open(path, encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            photos.setdefault(row["ref"].strip(), []).append(row["arquivo"].strip())

    return photos

def photo_path(filename: str) -> str:
    return os.path.join(IMAGES_DIR, os.path.basename(filename))
