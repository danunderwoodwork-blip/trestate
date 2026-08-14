from app.normalization.locations import canonicalize
from app.normalization.mappings import (
    normalize_currency,
    normalize_property_type,
    normalize_rooms,
    normalize_transaction,
    parse_bool,
    parse_float,
)
from app.normalization.prices import price_per_m2
from app.normalization.text import fold


def test_fold_turkish_and_suffixes():
    assert fold("MAHMUTLAR") == "mahmutlar"
    assert fold("Mahmutlar Mah.") == "mahmutlar"
    assert fold("Mahmutlar Mahallesi") == "mahmutlar"
    assert fold("Çıkcıllı") == "cikcilli"


def test_canonicalize_neighbourhood_aliases():
    for raw in ["Mahmutlar", "MAHMUTLAR", "Mahmutlar Mah.", "Mahmutlar Mahallesi"]:
        assert canonicalize(None, None, raw) == ("Antalya", "Alanya", "Mahmutlar")


def test_rooms():
    assert normalize_rooms("2+1") == ("2+1", 2)
    assert normalize_rooms("2 + 1") == ("2+1", 2)
    assert normalize_rooms("Studyo") == ("1+0", 1)
    assert normalize_rooms(None) == (None, None)


def test_mappings():
    assert normalize_transaction("Satılık") == "sale"
    assert normalize_transaction("Kiralık") == "rent_long"
    assert normalize_property_type("Daire") == "apartment"
    assert normalize_currency("TL") == "TRY"
    assert normalize_currency("€") == "EUR"
    assert parse_bool("Var") is True
    assert parse_bool("Yok") is False
    assert parse_float("5.450.000") == 5450000.0


def test_price_per_m2_gross_vs_net():
    assert price_per_m2(5500000, 120) == 45833.33
    assert price_per_m2(5500000, 105) == 52380.95
    assert price_per_m2(None, 100) is None
    assert price_per_m2(100, 0) is None
