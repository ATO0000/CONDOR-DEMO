from uuid import uuid4

from bank_app.app_models import (
    Subscription,
    SubscriptionCandidateStatus,
    SubscriptionStatus,
    Transaction,
    TrustStatus,
)

from bank_app.state.bank_state import BankState


def find_active_subscription(
    bank: BankState,
    merchant_id: str,
    merchant: str,
) -> Subscription | None:
    """Busca por ID o nombre normalizado, como en la confirmación manual."""
    return next(
        (
            subscription
            for subscription in bank.subscriptions
            if subscription.status == SubscriptionStatus.ACTIVE
            and (
                subscription.merchant_id == merchant_id
                or subscription.merchant.strip().upper() == merchant.strip().upper()
            )
        ),
        None,
    )


def create_subscription_from_transaction(
    bank: BankState,
    transaction: Transaction,
    *,
    merchant: str,
    merchant_id: str,
    recurring_type: str,
    recurrence_confidence: float,
    type_confidence: float,
    reasons: list[str],
) -> Subscription:
    """Registra una suscripción supervisada sin volver a descontar el cobro."""
    if find_active_subscription(bank, merchant_id, merchant) is not None:
        raise ValueError(
            "This merchant is already registered as an active subscription"
        )

    subscription = Subscription(
        id=f"sub-{uuid4().hex[:8]}",
        merchant=merchant,
        merchant_id=merchant_id,
        current_price=transaction.amount,
        frequency="Por determinar",
        last_charge_date=transaction.date,
        recurring_type=recurring_type,
        trust_status=TrustStatus.UNTRUSTED,
        status=SubscriptionStatus.ACTIVE,
        recurrence_confidence=recurrence_confidence,
        type_confidence=type_confidence,
        detection_reasons=list(reasons),
        transaction_history=[transaction.id],
    )
    bank.add_subscription(subscription)
    return subscription


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

    return _resolve_subscription_candidate(bank, candidate_id, unsure=False)


def mark_subscription_candidate_unsure(
    bank: BankState,
    candidate_id: str,
) -> Subscription:
    """Activa supervisión conservadora y deja la suscripción por verificar."""
    return _resolve_subscription_candidate(bank, candidate_id, unsure=True)


def _resolve_subscription_candidate(
    bank: BankState,
    candidate_id: str,
    *,
    unsure: bool,
) -> Subscription:
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

    subscription = create_subscription_from_transaction(
        bank,
        transaction,
        merchant=candidate.merchant,
        merchant_id=candidate.merchant_id,
        recurring_type=candidate.detected_type,
        recurrence_confidence=(
            candidate.recurrence_confidence
        ),
        type_confidence=candidate.type_confidence,
        reasons=candidate.reasons,
    )

    subscription.needs_user_verification = unsure
    candidate.status = (
        SubscriptionCandidateStatus.UNSURE_BY_USER
        if unsure else SubscriptionCandidateStatus.CONFIRMED
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
