def clean_amount(amount):
    amount = int(round(float(amount) * 100, 0))
    return amount

# This function makes sure to not add 'Itbis' in the dict, unless there's a value.
# Azul documentation doesn't specificy that it will fail if sent empty.
def update_itbis(data):
    if data.get('Itbis'):
        temp = {
            'Itbis': clean_amount(value),
        }
        data.update(temp)
    return data
