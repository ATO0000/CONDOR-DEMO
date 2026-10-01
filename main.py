import json

from detector import detect_subscription
from merchant_model import MerchantRecurringModel

def main():

    # =========================================================
    # CARGAR HISTORIAL DEL BANCO
    # =========================================================

    with open(
        "historical_transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        historical_transactions = (
            json.load(file)
        )

    # Crear modelo una sola vez
    merchant_model = (
        MerchantRecurringModel(
            historical_transactions
        )
    )

    # =========================================================
    # CARGAR NUEVAS TRANSACCIONES
    # =========================================================

    with open(
        "transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        transactions = json.load(file)

    # =========================================================
    # DETECTAR
    # =========================================================

    for tx in transactions:

        result = detect_subscription(
            tx,
            merchant_model=merchant_model
        )

        print(
            "=" * 70
        )

        print(
            f"Merchant: "
            f"{tx.get('merchant', 'UNKNOWN')}"
        )

        print(
            f"Merchant ID: "
            f"{tx.get('merchant_id', 'UNKNOWN')}"
        )

        print(
            f"Amount: "
            f"{tx.get('amount')} "
            f"{tx.get('currency', '')}"
        )

        print(
            f"Recurring: "
            f"{result.is_recurring}"
        )

        print(
            f"Type: "
            f"{result.transaction_type}"
        )

        print(
            f"Confidence: "
            f"{result.confidence:.2%}"
        )

        print(
            f"Evidence score: "
            f"{result.evidence_score:.2%}"
        )

        print(
            f"Detection level: "
            f"{result.detection_level}"
        )

        if (
            result.merchant_recurring_probability
            is not None
        ):

            print(
                "Merchant probability: "
                f"{result.merchant_recurring_probability:.2%}"
            )

        print(
            "Needs user confirmation: "
            f"{result.needs_user_confirmation}"
        )

        print("Reasons:")

        if not result.reasons:

            print(
                " - No recurring evidence"
            )

        else:

            for reason in result.reasons:

                print(
                    f" - {reason}"
                )


if __name__ == "__main__":
    main()