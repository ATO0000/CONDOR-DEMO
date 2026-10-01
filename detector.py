from models import DetectionResult
from schemas import normalize_transaction


def detect_subscription(
    tx: dict,
    merchant_model=None
) -> DetectionResult:

    # =========================================================
    # VALIDACIÓN Y NORMALIZACIÓN
    # =========================================================

    tx = normalize_transaction(tx)

    network = tx.get(
        "network",
        ""
    )

    cit_mit_indicator = tx.get(
        "cit_mit_indicator",
        ""
    )

    pos_environment = tx.get(
        "pos_environment",
        ""
    )

    merchant_id = tx.get(
        "merchant_id"
    )

    reasons = []

    # =========================================================
    # NIVEL 1
    # SEÑALES EXPLÍCITAS DE LA RED
    # =========================================================

    # ---------------------------------------------------------
    # MASTERCARD
    # ---------------------------------------------------------

    if network == "MASTERCARD":

        if cit_mit_indicator in {
            "C103",
            "M103"
        }:

            return DetectionResult(
                is_recurring=True,
                transaction_type="SUBSCRIPTION",
                confidence=0.995,
                evidence_score=1.0,
                detection_level="NETWORK_EXPLICIT",
                needs_user_confirmation=False,
                reasons=[
                    f"Mastercard indicator "
                    f"{cit_mit_indicator}: "
                    f"subscription"
                ]
            )

        if cit_mit_indicator in {
            "C102",
            "M102"
        }:

            return DetectionResult(
                is_recurring=True,
                transaction_type="RECURRING_BILL",
                confidence=0.99,
                evidence_score=1.0,
                detection_level="NETWORK_EXPLICIT",
                needs_user_confirmation=False,
                reasons=[
                    f"Mastercard indicator "
                    f"{cit_mit_indicator}: "
                    f"recurring payment"
                ]
            )

        if cit_mit_indicator in {
            "C104",
            "M104"
        }:

            return DetectionResult(
                is_recurring=False,
                transaction_type="INSTALLMENT",
                confidence=0.995,
                evidence_score=0.0,
                detection_level="NETWORK_EXPLICIT",
                needs_user_confirmation=False,
                reasons=[
                    f"Mastercard indicator "
                    f"{cit_mit_indicator}: "
                    f"installment"
                ]
            )

        if cit_mit_indicator in {
            "C101",
            "M101"
        }:

            reasons.append(
                f"Mastercard indicator "
                f"{cit_mit_indicator}: "
                f"credential on file"
            )

    # ---------------------------------------------------------
    # VISA
    # ---------------------------------------------------------

    if network == "VISA":

        if pos_environment == "R":

            return DetectionResult(
                is_recurring=True,
                transaction_type="RECURRING_BILL",
                confidence=0.99,
                evidence_score=1.0,
                detection_level="NETWORK_EXPLICIT",
                needs_user_confirmation=False,
                reasons=[
                    "Visa POS Environment R: "
                    "recurring transaction"
                ]
            )

        if pos_environment == "I":

            return DetectionResult(
                is_recurring=False,
                transaction_type="INSTALLMENT",
                confidence=0.995,
                evidence_score=0.0,
                detection_level="NETWORK_EXPLICIT",
                needs_user_confirmation=False,
                reasons=[
                    "Visa POS Environment I: "
                    "installment"
                ]
            )

        if pos_environment == "C":

            reasons.append(
                "Visa credential-on-file transaction"
            )

    # =========================================================
    # NIVEL 2
    # AUTENTICACIÓN / 3DS
    # =========================================================

    if tx.get("three_ds_recurring") is True:

        return DetectionResult(
            is_recurring=True,
            transaction_type="RECURRING_BILL",
            confidence=0.98,
            evidence_score=0.98,
            detection_level="AUTHENTICATION_DATA",
            needs_user_confirmation=False,
            reasons=[
                "Recurring relationship indicated "
                "during authentication"
            ]
        )

    # =========================================================
    # NIVEL 3
    # MODELO HISTÓRICO DEL MERCHANT
    # =========================================================

    merchant_probability = None

    if (
        merchant_model is not None
        and merchant_id is not None
    ):

        merchant_result = (
            merchant_model.predict(
                merchant_id
            )
        )

        merchant_probability = (
            merchant_result[
                "probability"
            ]
        )

        features = merchant_result.get(
            "features"
        )

        if features is not None:

            reasons.append(
                "Merchant historical model: "
                f"{merchant_probability:.2%}"
            )

            reasons.append(
                "Merchant customers observed: "
                f"{features['total_customers']}"
            )

            reasons.append(
                "Repeat customer rate: "
                f"{features['repeat_customer_rate']:.2%}"
            )

            reasons.append(
                "Recurring interval regularity: "
                f"{features['regularity_score']:.2%}"
            )

            reasons.append(
                "Amount similarity: "
                f"{features['amount_similarity_score']:.2%}"
            )

        # -----------------------------------------
        # Merchant extremadamente consistente
        # -----------------------------------------

        if merchant_probability >= 0.95:

            return DetectionResult(
                is_recurring=True,

                transaction_type="PROBABLE_RECURRING",

                confidence=merchant_probability,

                evidence_score=merchant_probability,

                detection_level="MERCHANT_MODEL",

                # Sabemos que probablemente es recurrente,
                # pero todavía necesitamos saber qué tipo
                # de relación es.
                needs_user_confirmation=True,

                reasons=reasons,

                merchant_recurring_probability=(
                    merchant_probability
                )
            )

    # =========================================================
    # NIVEL 4
    # MOTOR HEURÍSTICO
    # =========================================================

    score = 0.0

    # ---------------------------------------------------------
    # CARD NOT PRESENT
    # ---------------------------------------------------------

    if tx.get("cardholder_present") is False:

        score += 0.10

        reasons.append(
            "Card-not-present transaction"
        )

    # ---------------------------------------------------------
    # E-COMMERCE
    # ---------------------------------------------------------

    if tx.get("ecommerce") is True:

        score += 0.10

        reasons.append(
            "E-commerce transaction"
        )

    # ---------------------------------------------------------
    # STORED CREDENTIAL
    # ---------------------------------------------------------

    if tx.get("stored_credential") is True:

        score += 0.20

        reasons.append(
            "Stored credential"
        )

    # ---------------------------------------------------------
    # MERCHANT MODEL
    # ---------------------------------------------------------

    if merchant_probability is not None:

        merchant_component = (
            merchant_probability
            * 0.50
        )

        score += merchant_component

    # Las heurísticas nunca adquieren
    # la fuerza de una señal explícita.
    score = min(
        score,
        0.94
    )

    # =========================================================
    # DECISIÓN HEURÍSTICA
    # =========================================================

    if score >= 0.80:

        return DetectionResult(
            is_recurring=True,
            transaction_type="POSSIBLE_RECURRING",
            confidence=score,
            evidence_score=score,
            detection_level="HEURISTIC",
            needs_user_confirmation=True,
            reasons=reasons,
            merchant_recurring_probability=merchant_probability
        )

    # =========================================================
    # EVIDENCIA INSUFICIENTE
    # =========================================================

    return DetectionResult(
        is_recurring=False,
        transaction_type="UNKNOWN",
        confidence=0.0,
        evidence_score=score,
        detection_level="INSUFFICIENT_EVIDENCE",
        needs_user_confirmation=False,
        reasons=reasons,
        merchant_recurring_probability=merchant_probability
    )