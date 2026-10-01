from dataclasses import dataclass
from typing import List


@dataclass
class TypeClassification:
    recurring_type: str
    confidence: float
    reasons: List[str]


# ============================================================
# MCCs
# ============================================================

# Muy fuerte: el propio MCC está orientado a continuidad
# o suscripción.
STRONG_SUBSCRIPTION_MCCS = {
    "5968",   # Direct Marketing - Continuity/Subscription
}

# Comercios donde una relación recurrente es frecuentemente
# una membresía o suscripción.
SUBSCRIPTION_ORIENTED_MCCS = {
    "4899",   # Cable / satellite / streaming
    "7997",   # Membership / athletic / sports clubs
}

# Bienes digitales.
# NO significan automáticamente suscripción.
DIGITAL_GOODS_MCCS = {
    "5815",
    "5816",
    "5817",
    "5818",
}

# Si ya detectamos recurrencia, estos MCC apuntan
# fuertemente a una cuenta periódica.
RECURRING_BILL_MCCS = {
    "4900",   # Utilities
    "6300",   # Insurance
}

# MCCs normalmente transaccionales.
# No los declaramos subscription aunque el cliente
# compre regularmente.
TRANSACTIONAL_MCCS = {
    "5411",   # Grocery / supermarkets
    "4121",   # Taxi / rideshare
    "5814",   # Fast food
    "5311",   # Department stores
    "5399",   # General merchandise
}


def classify_recurring_type(
    tx: dict,
    merchant_features=None
) -> TypeClassification:

    network = str(
        tx.get("network", "")
    ).strip().upper()

    cit_mit_indicator = str(
        tx.get("cit_mit_indicator", "")
    ).strip().upper()

    mcc = str(
        tx.get("mcc", "")
    ).strip()

    reasons = []

    # ========================================================
    # NIVEL 1
    # INDICADOR EXPLÍCITO DE RED
    # ========================================================

    if network == "MASTERCARD":

        if cit_mit_indicator in {
            "C103",
            "M103"
        }:

            return TypeClassification(
                recurring_type="SUBSCRIPTION",
                confidence=0.995,
                reasons=[
                    "Mastercard explicit subscription indicator"
                ]
            )

        if cit_mit_indicator in {
            "C102",
            "M102"
        }:

            return TypeClassification(
                recurring_type="RECURRING_BILL",
                confidence=0.99,
                reasons=[
                    "Mastercard explicit recurring / standing-order indicator"
                ]
            )

    # ========================================================
    # NIVEL 2
    # MCC MUY FUERTE
    # ========================================================

    if mcc in STRONG_SUBSCRIPTION_MCCS:

        return TypeClassification(
            recurring_type="SUBSCRIPTION",
            confidence=0.95,
            reasons=[
                f"MCC {mcc} is strongly associated "
                f"with continuity/subscription merchants"
            ]
        )

    # ========================================================
    # NIVEL 3
    # CUENTAS RECURRENTES
    # ========================================================

    if mcc in RECURRING_BILL_MCCS:

        return TypeClassification(
            recurring_type="RECURRING_BILL",
            confidence=0.90,
            reasons=[
                f"MCC {mcc} is associated with "
                f"periodic billing"
            ]
        )

    # ========================================================
    # NIVEL 4
    # MCC ORIENTADO A SUSCRIPCIÓN / MEMBRESÍA
    # ========================================================

    if mcc in SUBSCRIPTION_ORIENTED_MCCS:

        return TypeClassification(
            recurring_type="SUBSCRIPTION",
            confidence=0.85,
            reasons=[
                f"MCC {mcc} is subscription/"
                f"membership-oriented"
            ]
        )

    # ========================================================
    # FEATURES DEL MERCHANT
    # ========================================================

    amount_similarity = 0.0
    regularity = 0.0

    if merchant_features is not None:

        amount_similarity = (
            merchant_features.get(
                "amount_similarity_score",
                0.0
            )
        )

        regularity = (
            merchant_features.get(
                "regularity_score",
                0.0
            )
        )

    # ========================================================
    # NIVEL 5
    # BIENES DIGITALES
    # ========================================================

    if mcc in DIGITAL_GOODS_MCCS:

        reasons.append(
            f"MCC {mcc} indicates digital goods"
        )

        # Un producto digital por sí solo NO significa
        # suscripción.
        #
        # Exigimos además un patrón recurrente fuerte
        # y un monto bastante estable.

        if (
            regularity >= 0.90
            and amount_similarity >= 0.90
        ):

            reasons.append(
                "Merchant shows highly regular charges "
                "with stable amounts"
            )

            return TypeClassification(
                recurring_type="SUBSCRIPTION",
                confidence=0.80,
                reasons=reasons
            )

    # ========================================================
    # NIVEL 6
    # COMPORTAMIENTO TÍPICO DE CUENTA VARIABLE
    # ========================================================

    if (
        regularity >= 0.90
        and amount_similarity < 0.65
    ):

        return TypeClassification(
            recurring_type="RECURRING_BILL",
            confidence=0.70,
            reasons=[
                "Highly regular billing interval "
                "with substantially variable amount"
            ]
        )

    # ========================================================
    # MCC TRANSACCIONAL
    # ========================================================

    if mcc in TRANSACTIONAL_MCCS:

        return TypeClassification(
            recurring_type="UNKNOWN_RECURRING",
            confidence=0.0,
            reasons=[
                f"MCC {mcc} is normally transactional; "
                f"recurrence alone is insufficient "
                f"to classify it as a subscription"
            ]
        )

    # ========================================================
    # NO HAY INFORMACIÓN SUFICIENTE
    # ========================================================

    return TypeClassification(
        recurring_type="UNKNOWN_RECURRING",
        confidence=0.0,
        reasons=[
            "Insufficient evidence to determine "
            "the recurring payment type"
        ]
    )