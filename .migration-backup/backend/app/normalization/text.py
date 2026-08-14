"""Утилиты нормализации турецкого текста."""
import re

_TR_MAP = str.maketrans(
    {
        "İ": "i", "I": "i", "ı": "i",
        "Ş": "s", "ş": "s",
        "Ğ": "g", "ğ": "g",
        "Ç": "c", "ç": "c",
        "Ö": "o", "ö": "o",
        "Ü": "u", "ü": "u",
    }
)

# Суффиксы административных единиц, отбрасываемые при сопоставлении.
_SUFFIXES = re.compile(
    r"\b(mahallesi|mahalle|mah\.?|beldesi|belde|koyu|köyü|ilcesi|ilçesi)\b\.?", re.IGNORECASE
)


def fold(text: str) -> str:
    """'MAHMUTLAR Mah.' -> 'mahmutlar' — ключ для словарей алиасов."""
    t = text.translate(_TR_MAP).lower()
    t = _SUFFIXES.sub(" ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def slugify(*parts: str) -> str:
    return "-".join(re.sub(r"\s+", "-", fold(p)) for p in parts if p)
