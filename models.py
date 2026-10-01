from dataclasses import dataclass
from typing import List


@dataclass
class DetectionResult:

    # ¿Hay evidencia de futuros cobros recurrentes?
    is_recurring: bool

    # SUBSCRIPTION
    # RECURRING_BILL
    # PROBABLE_RECURRING
    # INSTALLMENT
    # UNKNOWN
    transaction_type: str

    confidence: float

    evidence_score: float

    detection_level: str

    needs_user_confirmation: bool

    reasons: List[str]

    # Probabilidad de recurrencia histórica del merchant.
    merchant_recurring_probability: float | None = None