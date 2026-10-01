from datetime import datetime

from bank_app.app_models import (
    Subscription,
    SubscriptionStatus,
    Transaction,
    TransactionStatus,
    TrustStatus,
)

from bank_app.state.bank_state import BankState


def seed_demo_data(bank: BankState) -> None:
    """
    Carga el estado inicial del gemelo digital.

    La función evita duplicar datos si el banco ya
    contiene información.
    """

    if bank.transactions or bank.subscriptions:
        return

    # ========================================================
    # TRANSACTIONS
    # ========================================================

    transactions = [
        Transaction(
            id="tx-001",
            merchant="JUMBO",
            merchant_id="merchant-jumbo",
            amount=45990,
            date=datetime(2026, 9, 30, 18, 42),
            status=TransactionStatus.COMPLETED,
        ),

        Transaction(
            id="tx-002",
            merchant="UBER *TRIP",
            merchant_id="merchant-uber",
            amount=7890,
            date=datetime(2026, 9, 29, 21, 15),
            status=TransactionStatus.COMPLETED,
        ),

        Transaction(
            id="tx-003",
            merchant="SPOTIFY",
            merchant_id="merchant-spotify",
            amount=5290,
            date=datetime(2026, 9, 28, 10, 5),
            status=TransactionStatus.COMPLETED,
            recurring_type="SUBSCRIPTION",
            recurrence_confidence=0.9855,
            type_confidence=0.85,
        ),

        Transaction(
            id="tx-004",
            merchant="NETFLIX.COM",
            merchant_id="merchant-netflix",
            amount=9990,
            date=datetime(2026, 9, 27, 9, 20),
            status=TransactionStatus.COMPLETED,
            recurring_type="SUBSCRIPTION",
            recurrence_confidence=0.9827,
            type_confidence=0.85,
        ),

        Transaction(
            id="tx-005",
            merchant="STARBUCKS STORE",
            merchant_id="merchant-starbucks",
            amount=4650,
            date=datetime(2026, 9, 26, 17, 30),
            status=TransactionStatus.COMPLETED,
        ),

        Transaction(
            id="tx-006",
            merchant="ADOBE *CREATIVE CLD",
            merchant_id="merchant-adobe",
            amount=17990,
            date=datetime(2026, 9, 25, 8, 10),
            status=TransactionStatus.COMPLETED,
            recurring_type="SUBSCRIPTION",
            recurrence_confidence=0.97,
            type_confidence=0.85,
        ),

        Transaction(
            id="tx-007",
            merchant="COPEC",
            merchant_id="merchant-copec",
            amount=35000,
            date=datetime(2026, 9, 24, 16, 35),
            status=TransactionStatus.COMPLETED,
        ),

        Transaction(
            id="tx-008",
            merchant="RAPPI *RESTAURANT",
            merchant_id="merchant-rappi",
            amount=16490,
            date=datetime(2026, 9, 23, 20, 50),
            status=TransactionStatus.COMPLETED,
        ),
    ]

    for transaction in transactions:
        bank.add_transaction(transaction)

    # ========================================================
    # SUBSCRIPTIONS
    # ========================================================

    spotify = Subscription(
        id="sub-spotify",
        merchant="Spotify",
        merchant_id="merchant-spotify",
        current_price=5290,
        frequency="Mensual",
        last_charge_date=datetime(2026, 9, 28),
        recurring_type="SUBSCRIPTION",
        trust_status=TrustStatus.UNTRUSTED,
        status=SubscriptionStatus.ACTIVE,
        recurrence_confidence=0.9855,
        type_confidence=0.85,
        transaction_history=["tx-003"],
    )

    netflix = Subscription(
        id="sub-netflix",
        merchant="Netflix",
        merchant_id="merchant-netflix",
        current_price=9990,
        frequency="Mensual",
        last_charge_date=datetime(2026, 9, 27),
        recurring_type="SUBSCRIPTION",
        trust_status=TrustStatus.TRUSTED,
        status=SubscriptionStatus.ACTIVE,
        recurrence_confidence=0.9827,
        type_confidence=0.85,
        transaction_history=["tx-004"],
    )

    adobe = Subscription(
        id="sub-adobe",
        merchant="Adobe Creative Cloud",
        merchant_id="merchant-adobe",
        current_price=17990,
        frequency="Mensual",
        last_charge_date=datetime(2026, 9, 25),
        recurring_type="SUBSCRIPTION",
        trust_status=TrustStatus.UNTRUSTED,
        status=SubscriptionStatus.ACTIVE,
        recurrence_confidence=0.97,
        type_confidence=0.85,
        transaction_history=["tx-006"],
    )

    bank.add_subscription(spotify)
    bank.add_subscription(netflix)
    bank.add_subscription(adobe)