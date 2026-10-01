from filter_pipeline import analyze_transaction
from merchant_model import MerchantRecurringModel


def create_subscription_history():

    history = []

    for i in range(100):

        customer = f"C{i:03d}"

        history.extend([
            {
                "customer_id": customer,
                "merchant_id": "STREAM001",
                "date": "2026-01-01",
                "amount": 9990
            },
            {
                "customer_id": customer,
                "merchant_id": "STREAM001",
                "date": "2026-02-01",
                "amount": 9990
            },
            {
                "customer_id": customer,
                "merchant_id": "STREAM001",
                "date": "2026-03-01",
                "amount": 9990
            }
        ])

    return history


def test_pipeline_detects_subscription():

    history = create_subscription_history()

    model = MerchantRecurringModel(
        history
    )

    tx = {
        "merchant": "DIGITAL SERVICE",
        "merchant_id": "STREAM001",
        "network": "VISA",
        "mcc": "4899",
        "amount": 9990,
        "cardholder_present": False,
        "ecommerce": True,
        "stored_credential": True
    }

    result = analyze_transaction(
        tx,
        merchant_model=model
    )

    assert result.is_recurring is True

    assert (
        result.recurring_type
        == "SUBSCRIPTION"
    )

    assert (
        result.recurrence_confidence
        >= 0.95
    )

    assert (
        result.type_confidence
        >= 0.80
    )


def test_pipeline_normal_purchase():

    model = MerchantRecurringModel([])

    tx = {
        "merchant": "STORE",
        "merchant_id": "STORE001",
        "network": "VISA",
        "mcc": "5411",
        "amount": 35000,
        "cardholder_present": True,
        "ecommerce": False,
        "stored_credential": False
    }

    result = analyze_transaction(
        tx,
        merchant_model=model
    )

    assert result.is_recurring is False

    assert (
        result.recurring_type
        == "NON_RECURRING"
    )


def test_pipeline_explicit_mastercard():

    model = MerchantRecurringModel([])

    tx = {
        "merchant": "SERVICE",
        "network": "MASTERCARD",
        "cit_mit_indicator": "C103",
        "mcc": "5968"
    }

    result = analyze_transaction(
        tx,
        merchant_model=model
    )

    assert result.is_recurring is True

    assert (
        result.recurring_type
        == "SUBSCRIPTION"
    )

    assert (
        result.detection_level
        == "NETWORK_EXPLICIT"
    )


def test_pipeline_recurring_bill():

    history = []

    for i in range(100):

        customer = f"C{i:03d}"

        history.extend([
            {
                "customer_id": customer,
                "merchant_id": "UTILITY001",
                "date": "2026-01-05",
                "amount": 30000
            },
            {
                "customer_id": customer,
                "merchant_id": "UTILITY001",
                "date": "2026-02-05",
                "amount": 45000
            },
            {
                "customer_id": customer,
                "merchant_id": "UTILITY001",
                "date": "2026-03-05",
                "amount": 25000
            }
        ])

    model = MerchantRecurringModel(
        history
    )

    tx = {
        "merchant": "UTILITY",
        "merchant_id": "UTILITY001",
        "network": "VISA",
        "mcc": "4900",
        "amount": 38000,
        "cardholder_present": False,
        "ecommerce": True,
        "stored_credential": True
    }

    result = analyze_transaction(
        tx,
        merchant_model=model
    )

    assert result.is_recurring is True

    assert (
        result.recurring_type
        == "RECURRING_BILL"
    )