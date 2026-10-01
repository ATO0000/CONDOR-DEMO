import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from filter_pipeline import analyze_transaction
from merchant_model import MerchantRecurringModel


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HISTORICAL_DATA_PATH = (
    PROJECT_ROOT / "large_historical_transactions.json"
)


# ============================================================
# APP-FACING RESULT
# ============================================================

@dataclass
class FilterAnalysis:
    is_recurring: bool
    recurring_type: str

    recurrence_confidence: float
    type_confidence: float

    detection_level: str
    needs_user_confirmation: bool

    merchant_recurring_probability: float | None

    reasons: List[str]


# ============================================================
# MERCHANT MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_merchant_model() -> MerchantRecurringModel:
    """
    Carga una única vez el histórico de transacciones
    y construye el MerchantRecurringModel.

    El modelo queda cacheado para no reconstruirlo en
    cada interacción de Streamlit.
    """

    if not HISTORICAL_DATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo histórico: "
            f"{HISTORICAL_DATA_PATH}"
        )

    with open(
        HISTORICAL_DATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        history = json.load(file)

    return MerchantRecurringModel(history)


# ============================================================
# FILTER ADAPTER
# ============================================================

def analyze_bank_transaction(
    transaction_data: dict,
) -> FilterAnalysis:
    """
    Ejecuta el filtro existente sobre una transacción bancaria.

    Esta función es el único punto de integración entre
    el gemelo digital y filter_pipeline.py.
    """

    merchant_model = get_merchant_model()

    result = analyze_transaction(
        transaction_data,
        merchant_model=merchant_model,
    )

    return FilterAnalysis(
        is_recurring=result.is_recurring,
        recurring_type=result.recurring_type,
        recurrence_confidence=result.recurrence_confidence,
        type_confidence=result.type_confidence,
        detection_level=result.detection_level,
        needs_user_confirmation=result.needs_user_confirmation,
        merchant_recurring_probability=(
            result.merchant_recurring_probability
        ),
        reasons=list(result.reasons),
    )