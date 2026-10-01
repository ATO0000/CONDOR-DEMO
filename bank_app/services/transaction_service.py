from datetime import datetime
from uuid import uuid4

from bank_app.app_models import (
    PendingAuthorization,
    Transaction,
    TransactionStatus,
    TrustStatus,
)
from bank_app.state.bank_state import BankState


def simulate_subscription_charge(
    bank: BankState,
    subscription_id: str,
    attempted_amount: float,
) -> Transaction:
    """
    Simula un nuevo intento de cobro asociado a una
    suscripción ya conocida por el gemelo digital.

    Regla principal:
    - UNTRUSTED + aumento de precio -> PENDING_APPROVAL
    - En los demás casos -> COMPLETED
    """

    subscription = bank.get_subscription_by_id(
        subscription_id
    )

    if subscription is None:
        raise ValueError("Subscription not found")

    if subscription.status.value != "ACTIVE":
        raise ValueError(
            "Cannot charge a cancelled subscription"
        )

    if attempted_amount <= 0:
        raise ValueError(
            "Attempted amount must be greater than zero"
        )

    previous_amount = subscription.current_price

    transaction = Transaction(
        id=f"tx-{uuid4().hex[:8]}",
        merchant=subscription.merchant,
        merchant_id=subscription.merchant_id,
        amount=attempted_amount,
        date=datetime.now(),
        recurring_type=subscription.recurring_type,
        recurrence_confidence=subscription.recurrence_confidence,
        type_confidence=subscription.type_confidence,
        detection_reasons=list(
            subscription.detection_reasons
        ),
    )

    price_increased = (
        attempted_amount > previous_amount
    )

    # ========================================================
    # UNTRUSTED + PRICE INCREASE
    # ========================================================

    if (
        subscription.trust_status == TrustStatus.UNTRUSTED
        and price_increased
    ):
        transaction.status = (
            TransactionStatus.PENDING_APPROVAL
        )

        percentage_change = (
            (
                attempted_amount - previous_amount
            )
            / previous_amount
        ) * 100

        authorization = PendingAuthorization(
            id=f"auth-{uuid4().hex[:8]}",
            transaction_id=transaction.id,
            subscription_id=subscription.id,
            previous_amount=previous_amount,
            attempted_amount=attempted_amount,
            percentage_change=percentage_change,
            reason="PRICE_INCREASE",
        )

        bank.add_transaction(transaction)
        bank.add_pending_authorization(
            authorization
        )

        return transaction

    # ========================================================
    # NORMAL PROCESSING
    # ========================================================

    transaction.status = TransactionStatus.COMPLETED

    bank.add_transaction(transaction)

    bank.balance -= attempted_amount

    subscription.current_price = attempted_amount
    subscription.last_charge_date = transaction.date

    subscription.transaction_history.append(
        transaction.id
    )

    return transaction