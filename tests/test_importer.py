from decimal import Decimal

import pytest

from data.importer import parse_number, parse_price, read_photo_index, read_properties

@pytest.mark.parametrize("text,expected", [
    ("4.850.000,10", "4850000.10"),
    ("1,250,000", "1250000"),
    ("3.150.000", "3150000"),
    ("3.5M", "3500000"),
    ("9.2M", "9200000"),
    ("14,800,000", "14800000"),
    ("7,750,000.00", "7750000.00"),
    ("1.150 m²", "1150"),
    ("20.000 m²", "20000"),
    ("199.74 m2", "199.74"),
    ("1,718.71 m2", "1718.71"),
    ("2,972.90 m2", "2972.90"),
    ("212 m²", "212"),
])
def test_parse_number(text, expected):
    assert parse_number(text) == Decimal(expected)

def test_parse_number_empty():
    assert parse_number("") is None

def test_parse_price_detects_currency():
    assert parse_price("R$ 4.850.000,10") == (Decimal("4850000.10"), "BRL")
    assert parse_price("US$ 1,250,000") == (Decimal("1250000"), "USD")
    assert parse_price("AED 3.5M") == (Decimal("3500000"), "AED")

def test_parse_price_on_request():
    assert parse_price("sob consulta") == (None, None)

def test_properties_csv_is_normalized():
    items = {item["ref"]: item for item in read_properties()}
    assert len(items) == 18
    assert items["BR-0104"]["preco_valor"] is None
    assert items["BR-0101"]["area_privativa"] == "212.00"
    assert items["BR-0101"]["area_construida"] is None
    assert items["BR-0103"]["area_construida"] == "620.00"
    assert items["BR-0103"]["area_terreno"] == "540.00"
    assert items["AE-0304"]["area_terreno"] == "2972.90"
    assert items["AE-0304"]["preco_valor"] == "48000000.00"
    assert items["PA-0206"]["vagas"] == 0
    assert items["BR-0103"]["andar"] is None

def test_photo_index_groups_by_ref():
    photos = read_photo_index()
    assert sum(len(files) for files in photos.values()) == 58
    assert photos["BR-0101"][0].startswith("IMG_")
