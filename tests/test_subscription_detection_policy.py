import pytest

from bank_app.services.filter_adapter import FilterAnalysis
from bank_app.services.subscription_detection_policy import (
    SubscriptionDetectionAction,
    decide_subscription_action,
)


@pytest.mark.parametrize(
    "is_recurring,recurring_type,recurrence,type_confidence,expected",
    [
        (True, "SUBSCRIPTION", 0.9855, 0.85, "AUTO_DETECTED"),
        (True, "SUBSCRIPTION", 0.90, 0.80, "AUTO_DETECTED"),
        (True, "SUBSCRIPTION", 0.899, 0.80, "NEEDS_CONFIRMATION"),
        (True, "SUBSCRIPTION", 0.90, 0.799, "NEEDS_CONFIRMATION"),
        (True, "SUBSCRIPTION", 0.82, 0.68, "NEEDS_CONFIRMATION"),
        (False, "NON_RECURRING", 0.99, 0.99, "NONE"),
        (False, "SUBSCRIPTION", 0.99, 0.99, "NONE"),
        (True, "RECURRING_BILL", 0.99, 0.99, "NONE"),
        (True, "UNKNOWN_RECURRING", 0.99, 0.99, "NONE"),
    ],
)
def test_subscription_detection_policy(
    is_recurring, recurring_type, recurrence, type_confidence, expected
):
    analysis = FilterAnalysis(
        is_recurring=is_recurring,
        recurring_type=recurring_type,
        recurrence_confidence=recurrence,
        type_confidence=type_confidence,
        detection_level="TEST",
        needs_user_confirmation=True,
        merchant_recurring_probability=None,
        reasons=[],
    )

    assert decide_subscription_action(analysis) == SubscriptionDetectionAction(expected)
