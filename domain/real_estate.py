from abc import ABC
from dataclasses import dataclass
from decimal import Decimal

from domain.money import Money

@dataclass(frozen=True)
class Place:
    code: str
    name: str
    currency: str

PLACES = {
    "BR": Place("BR", "Brasil", "BRL"),
    "PA": Place("PA", "Panamá", "USD"),
    "AE": Place("AE", "Dubai", "AED"),
}

class Typology(ABC):
    key: str
    label: str
    required_fields: tuple[str, ...]
    not_applicable_fields: tuple[str, ...]
    area_basis: str

    def missing_fields(self, data: dict) -> list[str]:
        return [name for name in self.required_fields if data.get(name) in (None, "")]

    def forbidden_fields(self, data: dict) -> list[str]:
        return [name for name in self.not_applicable_fields if data.get(name) not in (None, "")]

    def price_per_m2(self, price: Money | None, data: dict) -> Money | None:
        area = data.get(self.area_basis)
        if price is None or not area:
            return None
        return price.per_area(Decimal(str(area)))

class UnitTypology(Typology):
    required_fields = ("area_privativa", "quartos", "andar")
    not_applicable_fields = ("area_terreno",)
    area_basis = "area_privativa"

class HouseTypology(Typology):
    required_fields = ("area_construida", "area_terreno", "quartos")
    not_applicable_fields = ("andar",)
    area_basis = "area_construida"

class Apartment(UnitTypology):
    key = "apartamento"
    label = "Apartamento"

class Penthouse(UnitTypology):
    key = "penthouse"
    label = "Penthouse"

class Villa(HouseTypology):
    key = "villa"
    label = "Villa"

class Estate(HouseTypology):
    key = "estate"
    label = "Estate"

TYPOLOGIES = {cls.key: cls() for cls in (Apartment, Penthouse, Villa, Estate)}

def typology_for(key: str) -> Typology | None:
    return TYPOLOGIES.get(key)

def check_currency(place_code: str, currency: str | None) -> bool:
    place = PLACES.get(place_code)
    return place is not None and (currency is None or currency == place.currency)

def rule_errors(data: dict, complete: bool) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    typology = typology_for(data.get("tipologia"))
    place = PLACES.get(data.get("pais"))

    if place is None:
        errors.append(("pais", "invalido"))
    elif not check_currency(place.code, data.get("preco_moeda")):
        errors.append(("preco_moeda", "moeda_incompativel"))

    if typology is None:
        errors.append(("tipologia", "invalido"))
        return errors

    for name in typology.forbidden_fields(data):
        errors.append((name, "nao_se_aplica"))

    if complete:
        for name in typology.missing_fields(data):
            errors.append((name, "obrigatorio"))
        if data.get("preco_valor") in (None, ""):
            errors.append(("preco_valor", "obrigatorio"))

    return errors
