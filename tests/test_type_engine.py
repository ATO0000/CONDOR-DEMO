from type_engine import classify_recurring_type


def test_mastercard_explicit_subscription():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "C103"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "SUBSCRIPTION"
    assert result.confidence >= 0.99


def test_mastercard_recurring_bill():

    tx = {
        "network": "MASTERCARD",
        "cit_mit_indicator": "C102"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "RECURRING_BILL"


def test_subscription_mcc():

    tx = {
        "network": "VISA",
        "mcc": "5968"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "SUBSCRIPTION"


def test_streaming_mcc():

    tx = {
        "network": "VISA",
        "mcc": "4899"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "SUBSCRIPTION"


def test_utility_mcc():

    tx = {
        "network": "VISA",
        "mcc": "4900"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "RECURRING_BILL"


def test_insurance_mcc():

    tx = {
        "network": "VISA",
        "mcc": "6300"
    }

    result = classify_recurring_type(tx)

    assert result.recurring_type == "RECURRING_BILL"


def test_digital_goods_with_recurring_pattern():

    tx = {
        "network": "VISA",
        "mcc": "5817"
    }

    features = {
        "regularity_score": 0.98,
        "amount_similarity_score": 0.97
    }

    result = classify_recurring_type(
        tx,
        merchant_features=features
    )

    assert result.recurring_type == "SUBSCRIPTION"


def test_supermarket_not_called_subscription():

    tx = {
        "network": "VISA",
        "mcc": "5411"
    }

    features = {
        "regularity_score": 0.95,
        "amount_similarity_score": 0.95
    }

    result = classify_recurring_type(
        tx,
        merchant_features=features
    )

    assert (
        result.recurring_type
        == "UNKNOWN_RECURRING"
    )