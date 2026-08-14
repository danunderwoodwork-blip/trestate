"""Расчёт цены за m². Gross и net считаются раздельно и никогда не смешиваются."""


def price_per_m2(price: float | None, area_m2: float | None) -> float | None:
    if not price or not area_m2 or area_m2 <= 0:
        return None
    return round(price / area_m2, 2)
