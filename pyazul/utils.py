def clean_amount(amount: float) -> int:
    return int(round(float(amount) * 100, 0))