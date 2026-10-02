from uuid import uuid4

from bank_app.app_models import (
    Subscription,
    SubscriptionCandidateStatus,
    SubscriptionStatus,
    TrustStatus,
)

from bank_app.state.bank_state import BankState


def confirm_subscription_candidate(
    bank: BankState,
    candidate_id: str,
) -> Subscription:
    """
    Confirma que una detección del filtro corresponde
    realmente a una suscripción.

    Al confirmar:
    - Candidate -> CONFIRMED
    - se crea una Subscription
    - inicialmente queda UNTRUSTED
    - el primer cobro queda asociado al historial
    """

    candidate = next(
        (
            candidate
            for candidate in bank.subscription_candidates
            if candidate.id == candidate_id
        ),
        None,
    )

    if candidate is None:
        raise ValueError("Subscription candidate not found")

    if (
        candidate.status
        != SubscriptionCandidateStatus.PENDING_CONFIRMATION
    ):
        raise ValueError(
            "Subscription candidate has already been resolved"
        )

    transaction = bank.get_transaction_by_id(
        candidate.transaction_id
    )

    if transaction is None:
        raise ValueError("Original transaction not found")

    # Evitar duplicar una suscripción ya conocida.
    existing_subscription = next(
        (
            subscription
            for subscription in bank.subscriptions
            if (
                subscription.status
                == SubscriptionStatus.ACTIVE
                and (
                    subscription.merchant_id
                    == candidate.merchant_id
                    or
                    subscription.merchant.strip().upper()
                    == candidate.merchant.strip().upper()
                )
            )
        ),
        None,
    )

    if existing_subscription is not None:
        raise ValueError(
            "This merchant is already registered as an active subscription"
        )

    subscription = Subscription(
        id=f"sub-{uuid4().hex[:8]}",
        merchant=candidate.merchant,
        merchant_id=candidate.merchant_id,
        current_price=transaction.amount,
        frequency="Por determinar",
        last_charge_date=transaction.date,
        recurring_type=candidate.detected_type,
        trust_status=TrustStatus.UNTRUSTED,
        status=SubscriptionStatus.ACTIVE,
        recurrence_confidence=(
            candidate.recurrence_confidence
        ),
        type_confidence=candidate.type_confidence,
        detection_reasons=list(candidate.reasons),
        transaction_history=[
            transaction.id
        ],
    )

    bank.add_subscription(subscription)

    candidate.status = (
        SubscriptionCandidateStatus.CONFIRMED
    )

    return subscription


def reject_subscription_candidate(
    bank: BankState,
    candidate_id: str,
) -> None:
    """
    El usuario indica que el pago detectado por el filtro
    no corresponde a una suscripción.

    El movimiento original permanece registrado, pero no
    se crea una Subscription.
    """

    candidate = next(
        (
            candidate
            for candidate in bank.subscription_candidates
            if candidate.id == candidate_id
        ),
        None,
    )

    if candidate is None:
        raise ValueError("Subscription candidate not found")

    if (
        candidate.status
        != SubscriptionCandidateStatus.PENDING_CONFIRMATION
    ):
        raise ValueError(
            "Subscription candidate has already been resolved"
        )

    candidate.status = (
        SubscriptionCandidateStatus.REJECTED_BY_USER
    )