from decimal import ROUND_HALF_UP, Decimal

_CENT = Decimal('0.01')


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)
