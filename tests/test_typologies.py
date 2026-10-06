from decimal import Decimal

from domain.money import Money
from domain.real_estate import Apartment, Estate, HouseTypology, Penthouse, UnitTypology, Villa, rule_errors, typology_for

def test_inheritance_groups():
    assert issubclass(Apartment, UnitTypology)
    assert issubclass(Penthouse, UnitTypology)
    assert issubclass(Villa, HouseTypology)
    assert issubclass(Estate, HouseTypology)

def test_unit_requires_private_area_bedrooms_and_floor():
    assert typology_for("apartamento").missing_fields({}) == ["area_privativa", "quartos", "andar"]

def test_house_requires_built_and_land_area_and_bedrooms():
    assert typology_for("villa").missing_fields({}) == ["area_construida", "area_terreno", "quartos"]

def test_unit_rejects_land_area():
    assert typology_for("penthouse").forbidden_fields({"area_terreno": "10"}) == ["area_terreno"]

def test_house_rejects_floor():
    assert typology_for("estate").forbidden_fields({"andar": 3}) == ["andar"]

def test_price_per_m2_uses_private_area_for_units():
    data = {"area_privativa": "100", "area_construida": "999"}
    result = typology_for("apartamento").price_per_m2(Money(Decimal("1000000"), "USD"), data)
    assert result.amount == Decimal("10000.00")

def test_price_per_m2_uses_built_area_for_houses():
    data = {"area_construida": "500", "area_terreno": "5000"}
    result = typology_for("villa").price_per_m2(Money(Decimal("1000000"), "USD"), data)
    assert result.amount == Decimal("2000.00")

def test_price_per_m2_is_none_without_price_or_area():
    assert typology_for("villa").price_per_m2(None, {"area_construida": "10"}) is None
    assert typology_for("villa").price_per_m2(Money(Decimal("10"), "USD"), {}) is None

def test_draft_may_be_incomplete():
    data = {"tipologia": "apartamento", "pais": "PA", "preco_moeda": "USD"}
    assert rule_errors(data, complete=False) == []

def test_complete_reports_missing_fields_and_price():
    data = {"tipologia": "apartamento", "pais": "PA", "preco_moeda": "USD"}
    fields = {field for field, _ in rule_errors(data, complete=True)}
    assert fields == {"area_privativa", "quartos", "andar", "preco_valor"}

def test_currency_must_match_place():
    data = {"tipologia": "villa", "pais": "AE", "preco_moeda": "USD"}
    assert ("preco_moeda", "moeda_incompativel") in rule_errors(data, complete=False)

def test_unknown_place_and_typology():
    errors = rule_errors({"tipologia": "castelo", "pais": "XX"}, complete=False)
    assert ("pais", "invalido") in errors
    assert ("tipologia", "invalido") in errors
