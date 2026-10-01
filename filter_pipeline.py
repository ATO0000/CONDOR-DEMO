from dataclasses import dataclass
from typing import List, Optional

from detector import detect_subscription
from type_engine import classify_recurring_type


@dataclass
class FilterResult:

    is_recurring: bool

    recurring_type: str

    recurrence_confidence: float

    type_confidence: float

    detection_level: str

    needs_user_confirmation: bool

    merchant_recurring_probability: Optional[float]

    reasons: List[str]


def analyze_transaction(
    tx: dict,
    merchant_model=None
) -> FilterResult:

    # =========================================================
    # ETAPA 1
    # DETECCIÓN DE RECURRENCIA
    # =========================================================

    recurrence_result = detect_subscription(
        tx,
        merchant_model=merchant_model
    )

    # =========================================================
    # NO RECURRENTE
    # =========================================================

    if not recurrence_result.is_recurring:

        return FilterResult(
            is_recurring=False,

            recurring_type="NON_RECURRING",

            recurrence_confidence=(
                recurrence_result.evidence_score
            ),

            type_confidence=0.0,

            detection_level=(
                recurrence_result.detection_level
            ),

            needs_user_confirmation=False,

            merchant_recurring_probability=(
                recurrence_result
                .merchant_recurring_probability
            ),

            reasons=recurrence_result.reasons
        )

    # =========================================================
    # CASOS DONDE LA RED YA NOS DIO EL TIPO
    # =========================================================

    if recurrence_result.transaction_type in {
        "SUBSCRIPTION",
        "RECURRING_BILL"
    }:

        return FilterResult(
            is_recurring=True,

            recurring_type=(
                recurrence_result.transaction_type
            ),

            recurrence_confidence=(
                recurrence_result.confidence
            ),

            type_confidence=(
                recurrence_result.confidence
            ),

            detection_level=(
                recurrence_result.detection_level
            ),

            needs_user_confirmation=(
                recurrence_result
                .needs_user_confirmation
            ),

            merchant_recurring_probability=(
                recurrence_result
                .merchant_recurring_probability
            ),

            reasons=recurrence_result.reasons
        )

    # =========================================================
    # OBTENER FEATURES HISTÓRICAS
    # =========================================================

    merchant_features = None

    merchant_id = tx.get(
        "merchant_id"
    )

    if (
        merchant_model is not None
        and merchant_id is not None
    ):

        merchant_analysis = (
            merchant_model.predict(
                merchant_id
            )
        )

        merchant_features = (
            merchant_analysis.get(
                "features"
            )
        )

    # =========================================================
    # ETAPA 2
    # TYPE ENGINE
    # =========================================================

    type_result = classify_recurring_type(
        tx,
        merchant_features=merchant_features
    )

    combined_reasons = (
        recurrence_result.reasons
        + type_result.reasons
    )

    # =========================================================
    # RESULTADO FINAL
    # =========================================================

    return FilterResult(
        is_recurring=True,

        recurring_type=(
            type_result.recurring_type
        ),

        recurrence_confidence=(
            recurrence_result.confidence
        ),

        type_confidence=(
            type_result.confidence
        ),

        detection_level=(
            recurrence_result.detection_level
            + "+TYPE_ENGINE"
        ),

        # Si la detección no vino explícitamente
        # desde la red, queremos que el usuario pueda
        # confirmar lo detectado.
        needs_user_confirmation=(
            recurrence_result
            .needs_user_confirmation
            or type_result.recurring_type
            == "UNKNOWN_RECURRING"
        ),

        merchant_recurring_probability=(
            recurrence_result
            .merchant_recurring_probability
        ),

        reasons=combined_reasons
    )