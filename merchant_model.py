from collections import defaultdict
from datetime import datetime
from statistics import median


RECURRING_WINDOWS = [
    (6, 8),       # semanal
    (13, 16),     # quincenal
    (27, 33),     # mensual
    (55, 65),     # cada 2 meses
    (85, 95),     # trimestral
    (350, 380),   # anual
]


def parse_date(date_string: str) -> datetime:
    return datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )


def interval_matches_recurring_pattern(days: int) -> bool:

    for minimum, maximum in RECURRING_WINDOWS:

        if minimum <= days <= maximum:
            return True

    return False


def calculate_amount_similarity(amounts):

    if len(amounts) < 2:
        return 0.0

    mean_amount = sum(amounts) / len(amounts)

    if mean_amount == 0:
        return 0.0

    deviations = [
        abs(amount - mean_amount)
        / mean_amount
        for amount in amounts
    ]

    mean_deviation = (
        sum(deviations)
        / len(deviations)
    )

    similarity = 1 - mean_deviation

    return max(
        0.0,
        min(similarity, 1.0)
    )


def analyze_customer_history(transactions):

    if len(transactions) < 2:

        return {
            "repeated": False,
            "regularity_score": 0.0,
            "amount_similarity": 0.0
        }

    transactions = sorted(
        transactions,
        key=lambda tx: parse_date(
            tx["date"]
        )
    )

    intervals = []

    for i in range(
        1,
        len(transactions)
    ):

        previous_date = parse_date(
            transactions[i - 1]["date"]
        )

        current_date = parse_date(
            transactions[i]["date"]
        )

        difference = (
            current_date
            - previous_date
        ).days

        intervals.append(
            difference
        )

    recurring_intervals = [
        interval
        for interval in intervals
        if interval_matches_recurring_pattern(
            interval
        )
    ]

    regularity_score = (
        len(recurring_intervals)
        / len(intervals)
    )

    amounts = [
        float(tx["amount"])
        for tx in transactions
    ]

    amount_similarity = (
        calculate_amount_similarity(
            amounts
        )
    )

    return {
        "repeated": True,
        "regularity_score": regularity_score,
        "amount_similarity": amount_similarity
    }


def calculate_merchant_features(
    historical_transactions,
    merchant_id
):

    merchant_transactions = [

        tx
        for tx in historical_transactions

        if str(
            tx.get("merchant_id")
        ) == str(merchant_id)

    ]

    if not merchant_transactions:

        return None

    customers = defaultdict(list)

    for tx in merchant_transactions:

        customer_id = str(
            tx["customer_id"]
        )

        customers[
            customer_id
        ].append(tx)

    total_customers = len(customers)

    repeated_customers = 0

    regularity_scores = []
    amount_similarity_scores = []

    for customer_transactions in customers.values():

        analysis = analyze_customer_history(
            customer_transactions
        )

        if analysis["repeated"]:

            repeated_customers += 1

            regularity_scores.append(
                analysis[
                    "regularity_score"
                ]
            )

            amount_similarity_scores.append(
                analysis[
                    "amount_similarity"
                ]
            )

    repeat_customer_rate = (
        repeated_customers
        / total_customers
        if total_customers > 0
        else 0
    )

    average_regularity = (
        sum(regularity_scores)
        / len(regularity_scores)
        if regularity_scores
        else 0
    )

    average_amount_similarity = (
        sum(amount_similarity_scores)
        / len(amount_similarity_scores)
        if amount_similarity_scores
        else 0
    )

    return {
        "merchant_id": merchant_id,

        "total_transactions":
            len(merchant_transactions),

        "total_customers":
            total_customers,

        "repeat_customer_rate":
            repeat_customer_rate,

        "regularity_score":
            average_regularity,

        "amount_similarity_score":
            average_amount_similarity,
    }


def merchant_recurring_probability(
    historical_transactions,
    merchant_id
):

    features = calculate_merchant_features(
        historical_transactions,
        merchant_id
    )

    if features is None:

        return {
            "probability": 0.0,
            "features": None
        }

    # ------------------------------------------------------
    # CONFIABILIDAD DE LA MUESTRA
    # ------------------------------------------------------

    customers = features[
        "total_customers"
    ]

    if customers >= 100:

        sample_confidence = 1.0

    elif customers >= 50:

        sample_confidence = 0.90

    elif customers >= 20:

        sample_confidence = 0.75

    elif customers >= 10:

        sample_confidence = 0.55

    elif customers >= 5:

        sample_confidence = 0.35

    else:

        sample_confidence = 0.15

    # ------------------------------------------------------
    # SCORE
    # ------------------------------------------------------

    repeat_score = (
        features[
            "repeat_customer_rate"
        ]
    )

    regularity_score = (
        features[
            "regularity_score"
        ]
    )

    amount_score = (
        features[
            "amount_similarity_score"
        ]
    )

    raw_score = (
        repeat_score * 0.35
        +
        regularity_score * 0.45
        +
        amount_score * 0.20
    )

    probability = (
        raw_score
        * sample_confidence
    )

    probability = max(
        0.0,
        min(probability, 1.0)
    )

    return {
        "probability":
            probability,

        "features":
            features
    }

class MerchantRecurringModel:
    def __init__(self, historical_transactions):

        self.transactions_by_merchant = defaultdict(list)
        self.cache = {}

        for tx in historical_transactions:

            merchant_id = tx.get("merchant_id")

            if merchant_id is None:
                continue

            merchant_id = str(merchant_id)

            self.transactions_by_merchant[
                merchant_id
            ].append(tx)

    def predict(self, merchant_id):

        if merchant_id is None:

            return {
                "probability": 0.0,
                "features": None
            }

        merchant_id = str(merchant_id)

        # Si ya calculamos este comercio antes,
        # no repetimos todo el análisis.
        if merchant_id in self.cache:
            return self.cache[merchant_id]

        merchant_history = (
            self.transactions_by_merchant.get(
                merchant_id,
                []
            )
        )

        result = (
            merchant_recurring_probability(
                merchant_history,
                merchant_id
            )
        )

        self.cache[merchant_id] = result

        return result