def clean_amount(amount):
    amount = int(round(float(amount) * 100, 0))
    return amount
