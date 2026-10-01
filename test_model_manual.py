import json

from merchant_model import (
    merchant_recurring_probability
)


with open(
    "historical_transactions.json",
    "r",
    encoding="utf-8"
) as file:

    history = json.load(file)


spotify = merchant_recurring_probability(
    history,
    "SPOTIFY001"
)

jumbo = merchant_recurring_probability(
    history,
    "SUPERMARKET001"
)


print("SPOTIFY")
print(
    spotify
)

print()

print("JUMBO")
print(
    jumbo
)