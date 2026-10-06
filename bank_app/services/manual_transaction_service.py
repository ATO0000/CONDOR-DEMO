"""Build validated bank inputs; classification belongs to the real filter."""

import re
from uuid import uuid4

from schemas import normalize_transaction


NETWORKS = ("VISA", "MASTERCARD")
# Explicit signals read by detector.py; missing signals stay None.
CIT_MIT_INDICATORS = (None, "C101", "C102", "C103", "C104", "M101", "M102", "M103", "M104")
POS_ENVIRONMENTS = (None, "C", "R", "I")


def build_manual_transaction(
    *, merchant, amount, mcc, network, ecommerce, stored_credential,
    merchant_id="", customer_id="", cardholder_present=None,
    cit_mit_indicator=None, pos_environment=None, three_ds_recurring=None,
) -> dict:
    """Use explicit inputs only, with independent IDs and CLP integer amounts."""
    if not isinstance(merchant, str) or not merchant.strip():
        raise ValueError("Ingresa el nombre del comercio.")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("El monto del cobro debe ser un entero positivo en CLP.")
    if not isinstance(mcc, str) or not re.fullmatch(r"[0-9]{4}", mcc.strip()):
        raise ValueError("El MCC debe contener exactamente 4 dígitos.")
    if not isinstance(network, str) or network.strip().upper() not in NETWORKS:
        raise ValueError("Selecciona una red válida: VISA o MASTERCARD.")
    for label, value, optional in (
        ("Compra online", ecommerce, False),
        ("Tarjeta guardada", stored_credential, False),
        ("Titular presente", cardholder_present, True),
        ("Recurrencia 3DS", three_ds_recurring, True),
    ):
        if not isinstance(value, bool) and not (optional and value is None):
            raise ValueError(f"Valor inválido para {label}.")
    if cit_mit_indicator not in CIT_MIT_INDICATORS:
        raise ValueError("Indicador CIT/MIT no compatible.")
    if pos_environment not in POS_ENVIRONMENTS:
        raise ValueError("Entorno POS no compatible.")
    ids = {}
    for field, value in (("merchant_id", merchant_id), ("customer_id", customer_id)):
        if not isinstance(value, str) or "|" in value:
            raise ValueError(f"{field} debe ser texto sin el carácter |.")
        ids[field] = value.strip() or f"MANUAL_{field.upper()}_{uuid4().hex}"
    transaction = normalize_transaction({
        **ids, "merchant": merchant.strip(), "amount": amount,
        "mcc": mcc.strip(), "network": network.strip().upper(), "currency": "CLP",
        "ecommerce": ecommerce, "stored_credential": stored_credential,
        "cardholder_present": cardholder_present,
        "cit_mit_indicator": cit_mit_indicator, "pos_environment": pos_environment,
        "three_ds_recurring": three_ds_recurring,
    })
    # The schema normalizes missing text to ""; retain explicit missing inputs.
    transaction["cit_mit_indicator"] = cit_mit_indicator
    transaction["pos_environment"] = pos_environment
    return transaction
