from merchant_model import (
    interval_matches_recurring_pattern,
    calculate_amount_similarity,
    analyze_customer_history,
    merchant_recurring_probability
    )

def test_monthly_interval():

    assert (
        interval_matches_recurring_pattern(
            30
        )
        is True
    )


def test_random_interval():

    assert (
        interval_matches_recurring_pattern(
            19
        )
        is False
    )


def test_equal_amounts():

    amounts = [
        5290,
        5290,
        5290
    ]

    score = calculate_amount_similarity(
        amounts
    )

    assert score == 1.0


def test_variable_amounts():

    amounts = [
        5000,
        15000,
        30000
    ]

    score = calculate_amount_similarity(
        amounts
    )

    assert score < 1.0


def test_monthly_customer():

    transactions = [
        {
            "date": "2026-01-01",
            "amount": 10000
        },
        {
            "date": "2026-02-01",
            "amount": 10000
        },
        {
            "date": "2026-03-01",
            "amount": 10000
        }
    ]

    result = analyze_customer_history(
        transactions
    )

    assert result[
        "regularity_score"
    ] == 1.0

    assert result[
        "amount_similarity"
    ] == 1.0


def test_unknown_merchant():

    result = (
        merchant_recurring_probability(
            [],
            "UNKNOWN"
        )
    )

    assert result[
        "probability"
    ] == 0.0