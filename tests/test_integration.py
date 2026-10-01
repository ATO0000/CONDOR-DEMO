from detector import detect_subscription
from merchant_model import MerchantRecurringModel

def create_subscription_history(
    number_of_customers=100
):

    history = []

    for i in range(
        number_of_customers
    ):

        customer_id = (
            f"CUSTOMER_{i:03d}"
        )

        history.extend([
            {
                "customer_id": customer_id,
                "merchant_id": "SUB001",
                "date": "2026-01-05",
                "amount": 9990
            },
            {
                "customer_id": customer_id,
                "merchant_id": "SUB001",
                "date": "2026-02-05",
                "amount": 9990
            },
            {
                "customer_id": customer_id,
                "merchant_id": "SUB001",
                "date": "2026-03-05",
                "amount": 9990
            }
        ])

    return history


def test_first_payment_detected_from_other_customers():

    history = (
        create_subscription_history(
            100
        )
    )

    merchant_model = (
        MerchantRecurringModel(
            history
        )
    )

    # Este usuario está pagando
    # por PRIMERA VEZ.
    tx = {
        "merchant": "UNKNOWN SERVICE",
        "merchant_id": "SUB001",
        "network": "VISA",
        "amount": 9990,
        "currency": "CLP",
        "cardholder_present": False,
        "ecommerce": True,
        "stored_credential": True
    }

    result = detect_subscription(
        tx,
        merchant_model=merchant_model
    )

    assert result.is_recurring is True

    assert (
        result.transaction_type
        == "PROBABLE_RECURRING"
    )

    assert (
        result.detection_level
        == "MERCHANT_MODEL"
    )

    assert (
        result.merchant_recurring_probability
        >= 0.95
    )

    assert (
        result.needs_user_confirmation
        is True
    )


def test_unknown_merchant_not_detected():

    history = (
        create_subscription_history(
            100
        )
    )

    merchant_model = (
        MerchantRecurringModel(
            history
        )
    )

    tx = {
        "merchant": "UNKNOWN SHOP",
        "merchant_id": "NOT_IN_DATABASE",
        "network": "VISA",
        "amount": 15990,
        "cardholder_present": False,
        "ecommerce": True,
        "stored_credential": False
    }

    result = detect_subscription(
        tx,
        merchant_model=merchant_model
    )

    assert (
        result.is_recurring
        is False
    )


def test_network_signal_has_priority():

    merchant_model = (
        MerchantRecurringModel([])
    )

    tx = {
        "merchant": "SERVICE",
        "merchant_id": "UNKNOWN",
        "network": "MASTERCARD",
        "cit_mit_indicator": "C103"
    }

    result = detect_subscription(
        tx,
        merchant_model=merchant_model
    )

    assert (
        result.transaction_type
        == "SUBSCRIPTION"
    )

    assert (
        result.detection_level
        == "NETWORK_EXPLICIT"
    )