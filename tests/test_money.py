from decimal import Decimal

import pytest

from domain.money import Money, sort_key_usd

def test_rejects_unknown_currency():
    with pytest.raises(ValueError):
        Money(Decimal("10"), "EUR")

def test_rounds_to_two_places():
    assert Money(Decimal("10.005"), "USD").amount == Decimal("10.01")

def test_to_dict_uses_decimal_text():
    assert Money(Decimal("4850000.1"), "BRL").to_dict() == {"valor": "4850000.10", "moeda": "BRL"}

def test_price_per_area():
    result = Money(Decimal("4850000.10"), "BRL").per_area(Decimal("212"))
    assert result.amount == Decimal("22877.36")
    assert result.currency == "BRL"

def test_price_per_area_rejects_zero():
    with pytest.raises(ValueError):
        Money(Decimal("10"), "USD").per_area(Decimal("0"))

def test_format_brl_uses_brazilian_separators():
    assert Money(Decimal("4850000.10"), "BRL").format() == "R$ 4.850.000,10"

def test_format_usd_and_aed_hide_zero_cents():
    assert Money(Decimal("1250000"), "USD").format() == "US$ 1,250,000"
    assert Money(Decimal("3500000"), "AED").format() == "AED 3,500,000"

def test_sort_key_compares_currencies_through_usd():
    aed = Money(Decimal("3672500"), "AED")
    usd = Money(Decimal("1000000"), "USD")
    assert sort_key_usd(aed) == sort_key_usd(usd)

def test_sort_key_puts_missing_price_last():
    assert sort_key_usd(None) > sort_key_usd(Money(Decimal("999999999"), "USD"))
