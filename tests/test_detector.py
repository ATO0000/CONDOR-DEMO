import pytest

from detector import detect_subscription


def test_mastercard_subscription():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "C103"
    }

    result = detect_subscription(tx)

    assert result.is_recurring is True
    assert result.transaction_type == "SUBSCRIPTION"
    assert result.confidence >= 0.99
    assert result.needs_user_confirmation is False


def test_mastercard_merchant_initiated_subscription():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "M103"
    }

    result = detect_subscription(tx)

    assert result.is_recurring is True
    assert result.transaction_type == "SUBSCRIPTION"


def test_mastercard_cof_is_not_subscription():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "C101",
        "cardholder_present": False,
        "ecommerce": True,
        "stored_credential": True
    }

    result = detect_subscription(tx)

    assert result.transaction_type != "SUBSCRIPTION"
    assert result.is_recurring is False


def test_visa_recurring():

    tx = {
        "network": "VISA",
        "pos_environment": "R"
    }

    result = detect_subscription(tx)

    assert result.is_recurring is True

    assert (
        result.transaction_type
        == "RECURRING_BILL"
    )


def test_visa_cof_is_not_enough():

    tx = {
        "network": "VISA",
        "pos_environment": "C",
        "stored_credential": True
    }

    result = detect_subscription(tx)

    assert result.is_recurring is False
    assert result.transaction_type == "UNKNOWN"


def test_installment_not_subscription():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "C104"
    }

    result = detect_subscription(tx)

    assert result.is_recurring is False
    assert result.transaction_type == "INSTALLMENT"


def test_three_ds_recurring():

    tx = {
        "network": "VISA",
        "three_ds_recurring": True
    }

    result = detect_subscription(tx)

    assert result.is_recurring is True

    assert (
        result.detection_level
        == "AUTHENTICATION_DATA"
    )


def test_manual_merchant_probability_is_ignored():

    tx = {
        "network": "VISA",
        "merchant": "UNKNOWN DIGITAL SERVICE",

        # El detector NO debe confiar en una probabilidad
        # introducida manualmente en la transacción.
        "merchant_subscription_probability": 0.98
    }

    result = detect_subscription(tx)

    assert result.is_recurring is False

    assert (
        result.transaction_type
        == "UNKNOWN"
    )

    assert (
        result.merchant_recurring_probability
        is None
    )

def test_normal_purchase():

    tx = {
        "network": "VISA",
        "cardholder_present": True,
        "ecommerce": False,
        "stored_credential": False
    }

    result = detect_subscription(tx)

    assert result.is_recurring is False
    assert result.transaction_type == "UNKNOWN"
    assert result.evidence_score == 0


def test_network_normalization():

    tx = {
        "network": "mc",
        "cit_mit_indicator": "c103"
    }

    result = detect_subscription(tx)

    assert result.is_recurring is True
    assert result.transaction_type == "SUBSCRIPTION"


def test_invalid_probability():

    tx = {
        "network": "VISA",
        "merchant_subscription_probability": 1.50
    }

    with pytest.raises(ValueError):

        detect_subscription(tx)


def test_negative_amount():

    tx = {
        "network": "VISA",
        "amount": -5000
    }

    with pytest.raises(ValueError):

        detect_subscription(tx)