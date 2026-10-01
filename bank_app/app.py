import streamlit as st

from bank_app.components.dashboard import render_dashboard
from bank_app.state.session_state import (
    get_bank_state,
    reset_bank_state,
)


st.set_page_config(
    page_title="Banco Digital",
    page_icon="🏦",
    layout="wide",
)


# ============================================================
# STATE
# ============================================================

bank = get_bank_state()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🏦 Banco Digital")

    st.caption(
        "Protección inteligente de suscripciones"
    )

    st.divider()

    selected_page = st.radio(
        "Navegación",
        [
            "Inicio",
            "Movimientos",
            "Suscripciones",
            "Autorizaciones",
            "Simulador",
        ],
    )

    st.divider()

    if st.button(
        "Reiniciar demo",
        use_container_width=True,
    ):
        reset_bank_state()
        st.rerun()


# ============================================================
# ROUTING
# ============================================================

if selected_page == "Inicio":

    render_dashboard(bank)


elif selected_page == "Movimientos":

    from bank_app.components.movements import render_movements

    render_movements(bank)


elif selected_page == "Suscripciones":

    from bank_app.components.subscriptions import render_subscriptions

    render_subscriptions(bank)


elif selected_page == "Autorizaciones":

    from bank_app.components.pending_approvals import (
        render_pending_approvals,
    )

    render_pending_approvals(bank)


elif selected_page == "Simulador":

    from bank_app.components.simulator import render_simulator

    render_simulator(bank)