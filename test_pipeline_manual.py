import json

from filter_pipeline import analyze_transaction
from merchant_model import MerchantRecurringModel


with open(
    "large_historical_transactions.json",
    "r",
    encoding="utf-8"
) as file:

    history = json.load(file)


with open(
    "evaluation_transactions.json",
    "r",
    encoding="utf-8"
) as file:

    transactions = json.load(file)


model = MerchantRecurringModel(
    history
)


for tx in transactions:

    result = analyze_transaction(
        tx,
        merchant_model=model
    )

    print("=" * 80)

    print(
        f"Merchant: {tx['merchant']}"
    )

    print(
        f"MCC: {tx['mcc']}"
    )

    print(
        f"Recurring: "
        f"{result.is_recurring}"
    )

    print(
        f"Type: "
        f"{result.recurring_type}"
    )

    print(
        f"Recurrence confidence: "
        f"{result.recurrence_confidence:.2%}"
    )

    print(
        f"Type confidence: "
        f"{result.type_confidence:.2%}"
    )

    print(
        f"Detection level: "
        f"{result.detection_level}"
    )

    print(
        f"Needs confirmation: "
        f"{result.needs_user_confirmation}"
    )

    print("Reasons:")

    for reason in result.reasons:

        print(
            f" - {reason}"
        )