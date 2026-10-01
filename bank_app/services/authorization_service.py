from bank_app.app_models import (
    AuthorizationStatus,
    TransactionStatus,
)
from bank_app.state.bank_state import BankState


def approve_authorization(
    bank: BankState,
    authorization_id: str,
) -> None:
    """
    Aprueba un cobro que estaba detenido.

    Al aprobar:
    - Authorization -> APPROVED
    - Transaction -> APPROVED
    - se descuenta el saldo
    - se actualiza el precio conocido
    - se actualiza el último cobro
    - se agrega al historial de la suscripción
    """

    authorization = next(
        (
            item
            for item in bank.pending_authorizations
            if item.id == authorization_id
        ),
        None,
    )

    if authorization is None:
        raise ValueError("Authorization not found")

    if authorization.status != AuthorizationStatus.PENDING:
        raise ValueError(
            "Authorization has already been resolved"
        )

    transaction = bank.get_transaction_by_id(
        authorization.transaction_id
    )

    subscription = bank.get_subscription_by_id(
        authorization.subscription_id
    )

    if transaction is None:
        raise ValueError("Transaction not found")

    if subscription is None:
        raise ValueError("Subscription not found")

    # Actualizar estados
    authorization.status = AuthorizationStatus.APPROVED
    transaction.status = TransactionStatus.APPROVED

    # Ejecutar el cobro
    bank.balance -= authorization.attempted_amount

    # Actualizar suscripción
    subscription.current_price = authorization.attempted_amount
    subscription.last_charge_date = transaction.date

    if transaction.id not in subscription.transaction_history:
        subscription.transaction_history.append(
            transaction.id
        )


def reject_authorization(
    bank: BankState,
    authorization_id: str,
) -> None:
    """
    Rechaza un cobro que estaba detenido.

    Al rechazar:
    - Authorization -> REJECTED
    - Transaction -> REJECTED
    - NO se descuenta saldo
    - NO se modifica el precio conocido
    """

    authorization = next(
        (
            item
            for item in bank.pending_authorizations
            if item.id == authorization_id
        ),
        None,
    )

    if authorization is None:
        raise ValueError("Authorization not found")

    if authorization.status != AuthorizationStatus.PENDING:
        raise ValueError(
            "Authorization has already been resolved"
        )

    transaction = bank.get_transaction_by_id(
        authorization.transaction_id
    )

    if transaction is None:
        raise ValueError("Transaction not found")

    authorization.status = AuthorizationStatus.REJECTED
    transaction.status = TransactionStatus.REJECTED