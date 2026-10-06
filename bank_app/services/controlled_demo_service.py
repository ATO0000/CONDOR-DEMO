"""Escenario local de UX. No consulta ni modifica el filtro o sus datasets."""

from bank_app.app_models import Transaction
from bank_app.services.filter_adapter import FilterAnalysis
from bank_app.services.incoming_transaction_service import process_analyzed_transaction
from bank_app.state.bank_state import BankState


DEMO_MERCHANT_ID = "DEMO_INTERMEDIATE_001"
DEMO_MERCHANT = "FITNESS FLEX DEMO"
DEMO_AMOUNT = 24990.0
DEMO_TRANSACTION_KEY = f"DEMO_CUSTOMER|{DEMO_MERCHANT_ID}"
DEMO_NOTICE = "Escenario controlado de demostración"


def intermediate_demo_analysis() -> FilterAnalysis:
    """Devuelve un resultado nuevo, explícitamente simulado, en cada llamada."""
    return FilterAnalysis(
        is_recurring=True,
        recurring_type="SUBSCRIPTION",
        recurrence_confidence=0.82,
        type_confidence=0.68,
        detection_level="DEMO_CONTROLLED",
        needs_user_confirmation=True,
        merchant_recurring_probability=None,
        reasons=[f"{DEMO_NOTICE}: confianza simulada; no proviene del filtro real."],
    )


def process_intermediate_demo(bank: BankState) -> tuple[Transaction, FilterAnalysis]:
    """Procesa exclusivamente el escenario fijo DEMO con la política bancaria real."""
    return process_analyzed_transaction(
        bank,
        {
            "customer_id": "DEMO_CUSTOMER",
            "merchant_id": DEMO_MERCHANT_ID,
            "merchant": DEMO_MERCHANT,
            "amount": DEMO_AMOUNT,
            "mcc": "7997",
        },
        intermediate_demo_analysis(),
    )
