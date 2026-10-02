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


def process_incoming_transaction(
    
    bank: BankState,
    raw_transaction: dict,
) -> tuple[Transaction, FilterAnalysis]:
    """
    Procesa una nueva transacción recibida por el banco.

    Flujo:
    1. La transacción pasa por el filtro real.
    2. Se registra como movimiento.
    3. Si el filtro detecta una SUBSCRIPTION,
       se crea un SubscriptionCandidate.
    """
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
    # ========================================================
    # FILTRO REAL
    # ========================================================

    analysis = analyze_bank_transaction(
        raw_transaction
    )

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

    if (
        analysis.is_recurring
        and analysis.recurring_type
        == "SUBSCRIPTION"
    ):

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