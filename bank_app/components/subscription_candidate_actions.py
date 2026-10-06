import streamlit as st

from bank_app.app_models import SubscriptionCandidate, SubscriptionCandidateStatus
from bank_app.services.subscription_service import (
    confirm_subscription_candidate,
    mark_subscription_candidate_unsure,
    reject_subscription_candidate,
)
from bank_app.state.bank_state import BankState


def render_candidate_actions(
    bank: BankState, candidate: SubscriptionCandidate, *, key_prefix: str
) -> None:
    """Las dos pantallas comparten las mismas tres respuestas."""
    if candidate.status != SubscriptionCandidateStatus.PENDING_CONFIRMATION:
        return

    st.write("Detectamos señales de que este comercio podría realizar cobros periódicos.")
    st.write("¿Reconoces este pago como una suscripción?")

    actions = [
        ("Sí, es una suscripción", confirm_subscription_candidate,
         "fue agregada como suscripción supervisada."),
        ("No estoy seguro", mark_subscription_candidate_unsure,
         "quedó supervisada y pendiente de verificar."),
        ("No es una suscripción", reject_subscription_candidate,
         "no fue agregado a tus suscripciones."),
    ]
    for index, (column, (label, resolve, feedback)) in enumerate(zip(st.columns(3), actions)):
        with column:
            if st.button(
                label,
                key=f"{key_prefix}-candidate-{candidate.id}-{index}",
                type="primary" if index == 0 else "secondary",
                width="stretch",
            ):
                try:
                    resolve(bank, candidate.id)
                except ValueError as error:
                    st.error(str(error))
                else:
                    st.session_state["subscription_feedback"] = f"{candidate.merchant} {feedback}"
                    st.rerun()
