"""Mapping-слои: произвольные значения источников -> канонические значения платформы."""
import re

from app.normalization.text import fold

# --- Тип сделки ---
TRANSACTION_MAP = {
    "satilik": "sale", "sale": "sale", "for sale": "sale", "satis": "sale",
    "kiralik": "rent_long", "rent": "rent_long", "for rent": "rent_long",
    "long term rent": "rent_long", "uzun donem": "rent_long",
    "gunluk kiralik": "rent_short", "daily rent": "rent_short", "short term": "rent_short",
}

# --- Тип недвижимости ---
PROPERTY_MAP = {
    "daire": "apartment", "apartment": "apartment", "flat": "apartment",
    "rezidans": "apartment", "residence": "apartment",
    "mustakil ev": "house", "house": "house", "ev": "house", "detached": "house",
    "villa": "villa",
    "dukkan": "commercial", "magaza": "commercial", "ofis": "commercial",
    "isyeri": "commercial", "commercial": "commercial", "shop": "commercial", "office": "commercial",
    "arsa": "land", "land": "land", "plot": "land",
}

# --- Отопление ---
HEATING_MAP = {
    "kombi": "combi_gas", "kombi dogalgaz": "combi_gas", "dogalgaz": "combi_gas",
    "merkezi": "central", "central": "central",
    "klima": "ac", "air conditioning": "ac", "ac": "ac",
    "yerden isitma": "underfloor", "underfloor": "underfloor",
    "soba": "stove", "yok": "none", "none": "none",
}

# --- Валюты ---
CURRENCY_MAP = {
    "tl": "TRY", "try": "TRY", "₺": "TRY", "lira": "TRY",
    "usd": "USD", "$": "USD", "dolar": "USD",
    "eur": "EUR", "€": "EUR", "euro": "EUR",
    "gbp": "GBP", "£": "GBP",
}

_ROOMS_RE = re.compile(r"(\d+)\s*[+·.]\s*(\d+)")
_STUDIO_RE = re.compile(r"\b(studyo|studio|1\s*\+\s*0)\b", re.IGNORECASE)


def map_value(mapping: dict[str, str], value: str | None, default: str | None = None) -> str | None:
    if not value:
        return default
    return mapping.get(fold(value), default)


def normalize_transaction(value: str | None) -> str | None:
    return map_value(TRANSACTION_MAP, value)


def normalize_property_type(value: str | None) -> str | None:
    return map_value(PROPERTY_MAP, value)


def normalize_heating(value: str | None) -> str | None:
    return map_value(HEATING_MAP, value)


def normalize_currency(value: str | None) -> str:
    if not value:
        return "TRY"
    v = value.strip()
    return CURRENCY_MAP.get(v.lower(), v.upper() if len(v) == 3 else "TRY")


def normalize_rooms(value: str | None) -> tuple[str | None, int | None]:
    """'2 + 1' -> ('2+1', bedrooms=2); 'Studyo' -> ('1+0', 1)."""
    if not value:
        return None, None
    if _STUDIO_RE.search(value):
        return "1+0", 1
    m = _ROOMS_RE.search(value)
    if m:
        rooms, living = int(m.group(1)), int(m.group(2))
        return f"{rooms}+{living}", rooms
    if value.strip().isdigit():
        n = int(value.strip())
        return f"{n}+1", n
    return None, None


def parse_int(value) -> int | None:
    if value is None:
        return None
    m = re.search(r"-?\d+", str(value).replace(".", "").replace(",", ""))
    return int(m.group()) if m else None


def parse_float(value) -> float | None:
    """Понимает и турецкий ('5.450.000', '36,49'), и английский ('5,450,000', '36.49') форматы."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"[^\d.,\-]", "", str(value))
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):   # 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:                              # 1,234.56
            s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = head.replace(",", "") + (tail if len(tail) == 3 else "." + tail)
    elif "." in s:
        parts = s.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = s.replace(".", "")         # 5.450.000 — точки-разделители тысяч
    try:
        return float(s)
    except ValueError:
        return None


def parse_bool(value) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return fold(str(value)) in {"var", "evet", "yes", "true", "1", "mevcut"}
