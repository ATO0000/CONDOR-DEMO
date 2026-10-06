from enum import Enum


HIGH_RECURRENCE_CONFIDENCE = 0.90
HIGH_TYPE_CONFIDENCE = 0.80


class SubscriptionDetectionAction(str, Enum):
    NONE = "NONE"
    AUTO_DETECTED = "AUTO_DETECTED"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"


def decide_subscription_action(analysis) -> SubscriptionDetectionAction:
    """Aplica los umbrales del DT sin cambiar la decisión del filtro."""
    if not analysis.is_recurring or analysis.recurring_type != "SUBSCRIPTION":
        return SubscriptionDetectionAction.NONE

    recurrence_confidence = analysis.recurrence_confidence or 0.0
    type_confidence = analysis.type_confidence or 0.0

    if (
        recurrence_confidence >= HIGH_RECURRENCE_CONFIDENCE
        and type_confidence >= HIGH_TYPE_CONFIDENCE
    ):
        return SubscriptionDetectionAction.AUTO_DETECTED

    return SubscriptionDetectionAction.NEEDS_CONFIRMATION
