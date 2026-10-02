import streamlit as st

from bank_app.components.dashboard import render_dashboard
from bank_app.state.session_state import (
    get_bank_state,
    reset_bank_state,
)
from bank_app.styles import inject_global_styles


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Banco Digital",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL STYLES
# ============================================================

inject_global_styles()


# ============================================================
# STATE
# ============================================================

bank = get_bank_state()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## Banco Digital")

    st.caption(
        "Cuenta personal"
    )

    st.divider()

    pages = [
        "Inicio",
        "Movimientos",
        "Suscripciones",
        "Autorizaciones",
        "Simulador",
    ]

    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Inicio"

    for page in pages:

        is_active = (
            st.session_state.selected_page == page
        )

        if st.button(
            page,
            key=f"nav-{page}",
            type="primary" if is_active else "tertiary",
            use_container_width=True,
        ):
            st.session_state.selected_page = page
            st.rerun()

    selected_page = st.session_state.selected_page

    st.divider()

    pending_count = sum(
        1
        for authorization in bank.pending_authorizations
        if authorization.status.value == "PENDING"
    )

    if pending_count > 0:
        st.warning(
            f"{pending_count} cobro"
            f"{'s' if pending_count != 1 else ''} "
            f"requiere"
            f"{'n' if pending_count != 1 else ''} tu atención."
        )

    st.caption("Prototipo universitario")

    if st.button(
        "↻ Reiniciar demo",
        key="reset-demo",
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

    from bank_app.components.movements import (
        render_movements,
    )

    render_movements(bank)


elif selected_page == "Suscripciones":

    from bank_app.components.subscriptions import (
        render_subscriptions,
    )

    render_subscriptions(bank)


elif selected_page == "Autorizaciones":

    from bank_app.components.pending_approvals import (
        render_pending_approvals,
    )

    render_pending_approvals(bank)


elif selected_page == "Simulador":

    from bank_app.components.simulator import (
        render_simulator,
    )

    render_simulator(bank)