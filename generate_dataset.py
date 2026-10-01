import json
import random
from datetime import datetime, timedelta


random.seed(42)


MERCHANTS = [
    # =========================================================
    # SUSCRIPCIONES
    # =========================================================

    {
        "merchant_id": "SPOTIFY001",
        "merchant": "SPOTIFY",
        "mcc": "4899",
        "true_type": "SUBSCRIPTION",
        "base_amount": 5290,
        "amount_variation": 0.00,
        "interval_days": 30,
        "interval_variation": 2,
        "repeat_probability": 0.96,
    },

    {
        "merchant_id": "NETFLIX001",
        "merchant": "NETFLIX.COM",
        "mcc": "4899",
        "true_type": "SUBSCRIPTION",
        "base_amount": 9990,
        "amount_variation": 0.02,
        "interval_days": 30,
        "interval_variation": 2,
        "repeat_probability": 0.95,
    },

    {
        "merchant_id": "ADOBE001",
        "merchant": "ADOBE",
        "mcc": "5817",
        "true_type": "SUBSCRIPTION",
        "base_amount": 14990,
        "amount_variation": 0.01,
        "interval_days": 30,
        "interval_variation": 2,
        "repeat_probability": 0.94,
    },

    {
        "merchant_id": "GYM001",
        "merchant": "FITNESS CLUB",
        "mcc": "7997",
        "true_type": "SUBSCRIPTION",
        "base_amount": 29990,
        "amount_variation": 0.03,
        "interval_days": 30,
        "interval_variation": 3,
        "repeat_probability": 0.91,
    },

    # =========================================================
    # RECURRENTES, PERO NO LOS TRATAREMOS COMO SUSCRIPCIÓN
    # =========================================================

    {
        "merchant_id": "ELECTRIC001",
        "merchant": "ELECTRICIDAD",
        "mcc": "4900",
        "true_type": "RECURRING_BILL",
        "base_amount": 45000,
        "amount_variation": 0.45,
        "interval_days": 30,
        "interval_variation": 3,
        "repeat_probability": 0.97,
    },

    {
        "merchant_id": "WATER001",
        "merchant": "AGUA",
        "mcc": "4900",
        "true_type": "RECURRING_BILL",
        "base_amount": 28000,
        "amount_variation": 0.40,
        "interval_days": 30,
        "interval_variation": 4,
        "repeat_probability": 0.96,
    },

    {
        "merchant_id": "INSURANCE001",
        "merchant": "SEGURO AUTO",
        "mcc": "6300",
        "true_type": "RECURRING_BILL",
        "base_amount": 32000,
        "amount_variation": 0.01,
        "interval_days": 30,
        "interval_variation": 2,
        "repeat_probability": 0.96,
    },

    # =========================================================
    # NO RECURRENTES
    # =========================================================

    {
        "merchant_id": "JUMBO001",
        "merchant": "JUMBO",
        "mcc": "5411",
        "true_type": "NON_RECURRING",
        "base_amount": 45000,
        "amount_variation": 0.80,
        "interval_days": 8,
        "interval_variation": 6,
        "repeat_probability": 0.85,
    },

    {
        "merchant_id": "UBER001",
        "merchant": "UBER *TRIP",
        "mcc": "4121",
        "true_type": "NON_RECURRING",
        "base_amount": 8500,
        "amount_variation": 0.80,
        "interval_days": 5,
        "interval_variation": 5,
        "repeat_probability": 0.80,
    },

    {
        "merchant_id": "STARBUCKS001",
        "merchant": "STARBUCKS",
        "mcc": "5814",
        "true_type": "NON_RECURRING",
        "base_amount": 5500,
        "amount_variation": 0.55,
        "interval_days": 7,
        "interval_variation": 7,
        "repeat_probability": 0.70,
    },

    {
        "merchant_id": "AMAZON001",
        "merchant": "AMZN Mktp",
        "mcc": "5399",
        "true_type": "NON_RECURRING",
        "base_amount": 30000,
        "amount_variation": 0.95,
        "interval_days": 20,
        "interval_variation": 18,
        "repeat_probability": 0.55,
    },
]


def generate_amount(base, variation):

    factor = random.uniform(
        1 - variation,
        1 + variation
    )

    return max(
        100,
        round(base * factor)
    )


def generate_customer_transactions(
    customer_id,
    merchant,
    start_date
):

    transactions = []

    current_date = start_date

    # Número máximo de pagos históricos
    number_of_possible_payments = random.randint(
        2,
        8
    )

    for _ in range(number_of_possible_payments):

        if random.random() > merchant["repeat_probability"]:
            break

        amount = generate_amount(
            merchant["base_amount"],
            merchant["amount_variation"]
        )

        transactions.append({
            "customer_id": customer_id,

            "merchant_id":
                merchant["merchant_id"],

            "merchant":
                merchant["merchant"],

            "mcc": 
                merchant["mcc"],

            "date":
                current_date.strftime(
                    "%Y-%m-%d"
                ),

            "amount": amount,

            # Ground truth.
            # El modelo NO debe usar esto.
            "true_type":
                merchant["true_type"]
        })

        variation = random.randint(
            -merchant["interval_variation"],
            merchant["interval_variation"]
        )

        days = max(
            1,
            merchant["interval_days"]
            + variation
        )

        current_date += timedelta(
            days=days
        )

    return transactions


def generate_history(
    customers_per_merchant=300
):

    history = []

    base_date = datetime(
        2025,
        1,
        1
    )

    customer_counter = 0

    for merchant in MERCHANTS:

        for _ in range(
            customers_per_merchant
        ):

            customer_counter += 1

            customer_id = (
                f"C{customer_counter:06d}"
            )

            start_offset = random.randint(
                0,
                90
            )

            start_date = (
                base_date
                + timedelta(
                    days=start_offset
                )
            )

            history.extend(
                generate_customer_transactions(
                    customer_id,
                    merchant,
                    start_date
                )
            )

    return history


def generate_evaluation_transactions():

    transactions = []

    for merchant in MERCHANTS:

        # Simulamos un cliente completamente nuevo.
        tx = {
            "customer_id":
                f"NEW_{merchant['merchant_id']}",

            "merchant_id":
                merchant["merchant_id"],

            "merchant":
                merchant["merchant"],

            "mcc":
                merchant["mcc"],

            "network":
                random.choice(
                    ["VISA", "MASTERCARD"]
                ),

            "amount":
                generate_amount(
                    merchant["base_amount"],
                    merchant["amount_variation"]
                ),

            "currency":
                "CLP",

            "cardholder_present":
                False,

            "ecommerce":
                True,

            "stored_credential":
                (
                    merchant["true_type"]
                    != "NON_RECURRING"
                ),

            # No damos señales explícitas.
            # Queremos probar el merchant model.
            "cit_mit_indicator":
                None,

            "pos_environment":
                None,

            "three_ds_recurring":
                None,

            # Ground truth SOLO para evaluación.
            "true_type":
                merchant["true_type"]
        }

        transactions.append(tx)

    return transactions


def main():

    history = generate_history(
        customers_per_merchant=300
    )

    evaluation = (
        generate_evaluation_transactions()
    )

    with open(
        "large_historical_transactions.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=2,
            ensure_ascii=False
        )

    with open(
        "evaluation_transactions.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            evaluation,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Historical transactions: "
        f"{len(history)}"
    )

    print(
        f"Evaluation transactions: "
        f"{len(evaluation)}"
    )

    print(
        "Datasets generated successfully."
    )


if __name__ == "__main__":
    main()