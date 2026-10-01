def _normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().upper()


def normalize_transaction(tx: dict) -> dict:
    """
    Valida y normaliza una transacción antes de enviarla
    al detector.
    """

    if not isinstance(tx, dict):
        raise TypeError("Transaction must be a dictionary")

    normalized = dict(tx)

    # ---------------------------------------------------------
    # NORMALIZAR RED
    # ---------------------------------------------------------

    network = _normalize_text(
        normalized.get("network")
    )

    network_aliases = {
        "MC": "MASTERCARD",
        "MASTERCARD": "MASTERCARD",
        "VISA": "VISA"
    }

    normalized["network"] = network_aliases.get(
        network,
        network
    )

    # ---------------------------------------------------------
    # NORMALIZAR INDICADORES
    # ---------------------------------------------------------

    normalized["cit_mit_indicator"] = _normalize_text(
        normalized.get("cit_mit_indicator")
    )

    normalized["pos_environment"] = _normalize_text(
        normalized.get("pos_environment")
    )

    # ---------------------------------------------------------
    # NORMALIZAR COMERCIO
    # ---------------------------------------------------------

    merchant = normalized.get("merchant")

    if merchant is not None:
        normalized["merchant"] = str(
            merchant
        ).strip()

    # ---------------------------------------------------------
    # VALIDAR MONTO
    # ---------------------------------------------------------

    amount = normalized.get("amount")

    if amount is not None:

        if (
            not isinstance(amount, (int, float))
            or isinstance(amount, bool)
        ):
            raise ValueError(
                "amount must be numeric"
            )

        if amount < 0:
            raise ValueError(
                "amount cannot be negative"
            )

    # ---------------------------------------------------------
    # NORMALIZAR MONEDA
    # ---------------------------------------------------------

    currency = normalized.get("currency")

    if currency is not None:
        normalized["currency"] = (
            str(currency)
            .strip()
            .upper()
        )

    # ---------------------------------------------------------
    # NORMALIZAR MERCHANT ID
    # ---------------------------------------------------------

    merchant_id = normalized.get("merchant_id")

    if merchant_id is not None:

        normalized["merchant_id"] = str(
            merchant_id
        ).strip()


    # ---------------------------------------------------------
    # VALIDAR BOOLEANOS
    # ---------------------------------------------------------

    boolean_fields = [
        "cardholder_present",
        "ecommerce",
        "stored_credential",
        "three_ds_recurring"
    ]

    for field in boolean_fields:

        value = normalized.get(field)

        if value is not None and not isinstance(
            value,
            bool
        ):
            raise ValueError(
                f"{field} must be True, False or null"
            )

    # ---------------------------------------------------------
    # VALIDAR PROBABILIDAD DEL MERCHANT
    # ---------------------------------------------------------

    probability = normalized.get(
        "merchant_subscription_probability"
    )

    if probability is not None:

        if (
            not isinstance(probability, (int, float))
            or isinstance(probability, bool)
        ):
            raise ValueError(
                "merchant_subscription_probability "
                "must be numeric"
            )

        if not 0 <= probability <= 1:
            raise ValueError(
                "merchant_subscription_probability "
                "must be between 0 and 1"
            )

        normalized[
            "merchant_subscription_probability"
        ] = float(probability)

    return normalized