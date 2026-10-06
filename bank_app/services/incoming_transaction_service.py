from datetime import datetime
from uuid import uuid4

from bank_app.app_models import (
    SubscriptionCandidate,
    Transaction,
    TransactionStatus,
)

from bank_app.services.filter_adapter import (
    FilterAnalysis,
    analyze_bank_transaction,
)

from bank_app.state.bank_state import BankState
from bank_app.services.subscription_detection_policy import (
    SubscriptionDetectionAction,
    decide_subscription_action,
)
from bank_app.services.subscription_service import (
    create_subscription_from_transaction,
    find_active_subscription,
)


def process_incoming_transaction(
    
    bank: BankState,
    raw_transaction: dict,
) -> tuple[Transaction, FilterAnalysis]:
    """
    Procesa una nueva transacción recibida por el banco.

    Flujo:
    1. La transacción pasa por el filtro real.
    2. Se registra como movimiento.
    3. La política del DT registra una suscripción automáticamente,
       solicita confirmación o mantiene el procesamiento normal.
    """
    _check_not_processed(bank, raw_transaction)
    analysis = analyze_bank_transaction(raw_transaction)
    return process_analyzed_transaction(bank, raw_transaction, analysis)


def _check_not_processed(bank: BankState, raw_transaction: dict) -> str:
    demo_transaction_key = (
        f"{raw_transaction.get('customer_id', 'UNKNOWN')}"
        f"|{raw_transaction.get('merchant_id', 'UNKNOWN')}"
    )

    if (
        demo_transaction_key
        in bank.processed_demo_transactions
    ):
        raise ValueError(
            "Esta transacción de demostración ya fue procesada."
        )
    return demo_transaction_key


def process_analyzed_transaction(
    bank: BankState,
    raw_transaction: dict,
    analysis: FilterAnalysis,
) -> tuple[Transaction, FilterAnalysis]:
    """Aplica la política y registra un cobro ya analizado una sola vez.

    Punto compartido interno: el flujo normal obtiene siempre su análisis
    del filtro real; únicamente el servicio DEMO construye uno controlado.
    """
    demo_transaction_key = _check_not_processed(bank, raw_transaction)

    # ========================================================
    # TRANSACTION DEL GEMELO DIGITAL
    # ========================================================

    transaction = Transaction(
        id=f"tx-{uuid4().hex[:8]}",
        merchant=raw_transaction.get(
            "merchant",
            "UNKNOWN",
        ),
        merchant_id=raw_transaction.get(
            "merchant_id",
            "UNKNOWN",
        ),
        amount=float(
            raw_transaction.get(
                "amount",
                0,
            )
        ),
        date=datetime.now(),
        status=TransactionStatus.COMPLETED,
        recurring_type=(
            analysis.recurring_type
            if analysis.is_recurring
            else None
        ),
        recurrence_confidence=(
            analysis.recurrence_confidence
        ),
        type_confidence=(
            analysis.type_confidence
        ),
        detection_reasons=list(
            analysis.reasons
        ),
    )

    bank.add_transaction(transaction)

    bank.processed_demo_transactions.add(
        demo_transaction_key
    )

    # El primer cobro ya llegó y fue procesado.
    bank.balance -= transaction.amount

    # ========================================================
    # POSIBLE NUEVA SUSCRIPCIÓN
    # ========================================================

    action = decide_subscription_action(analysis)

    if action == SubscriptionDetectionAction.AUTO_DETECTED:
        if find_active_subscription(
            bank, transaction.merchant_id, transaction.merchant
        ) is None:
            create_subscription_from_transaction(
                bank,
                transaction,
                merchant=transaction.merchant,
                merchant_id=transaction.merchant_id,
                recurring_type=analysis.recurring_type,
                recurrence_confidence=analysis.recurrence_confidence,
                type_confidence=analysis.type_confidence,
                reasons=analysis.reasons,
            )

    elif action == SubscriptionDetectionAction.NEEDS_CONFIRMATION:

        candidate = SubscriptionCandidate(
            id=f"candidate-{uuid4().hex[:8]}",
            transaction_id=transaction.id,
            merchant=transaction.merchant,
            merchant_id=transaction.merchant_id,
            detected_type=analysis.recurring_type,
            recurrence_confidence=(
                analysis.recurrence_confidence
            ),
            type_confidence=(
                analysis.type_confidence
            ),
            reasons=list(
                analysis.reasons
            ),
        )

        bank.add_subscription_candidate(
            candidate
        )

    return transaction, analysis
