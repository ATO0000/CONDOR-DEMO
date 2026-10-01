import streamlit as st

from bank_app.app_models import TrustStatus
from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_subscriptions(bank: BankState) -> None:
    st.title("Suscripciones")

    st.caption(
        "Administra tus pagos recurrentes y define cuáles son de confianza."
    )

    st.write("")

    if not bank.subscriptions:
        st.info("No hay suscripciones registradas.")
        return

    for subscription in bank.subscriptions:

        with st.container(border=True):

            col1, col2, col3 = st.columns([2.5, 1, 1])

            # ================================================
            # INFORMACIÓN
            # ================================================

            with col1:

                st.markdown(
                    f"### {subscription.merchant}"
                )

                st.caption(
                    f"{subscription.recurring_type} · "
                    f"{subscription.frequency}"
                )

                st.write(
                    f"Último cobro: "
                    f"{subscription.last_charge_date.strftime('%d/%m/%Y')}"
                )

            # ================================================
            # PRECIO
            # ================================================

            with col2:

                st.caption("Precio actual")

                st.markdown(
                    f"### {format_clp(subscription.current_price)}"
                )

                st.caption(
                    f"/ {subscription.frequency.lower()}"
                )

            # ================================================
            # ESTADO
            # ================================================

            with col3:

                st.caption("Estado")

                if subscription.status.value == "ACTIVE":
                    st.success("Activa")
                else:
                    st.error("Cancelada")

            st.divider()

            col_status, col_button = st.columns([2, 1])

            # ================================================
            # TRUST STATUS
            # ================================================

            with col_status:

                st.caption("Nivel de confianza")

                if subscription.trust_status == TrustStatus.TRUSTED:

                    st.success(
                        "✓ De confianza"
                    )

                    st.caption(
                        "Los cobros de esta suscripción tienen "
                        "menor fricción."
                    )

                else:

                    st.warning(
                        "⚠ Supervisada"
                    )

                    st.caption(
                        "Los cambios de precio serán revisados "
                        "antes de procesarse."
                    )

            # ================================================
            # CAMBIAR TRUST STATUS
            # ================================================

            with col_button:

                if subscription.trust_status == TrustStatus.TRUSTED:

                    if st.button(
                        "Marcar como supervisada",
                        key=f"untrust-{subscription.id}",
                        use_container_width=True,
                    ):

                        subscription.trust_status = TrustStatus.UNTRUSTED

                        st.rerun()

                else:

                    if st.button(
                        "Marcar como de confianza",
                        key=f"trust-{subscription.id}",
                        use_container_width=True,
                    ):

                        subscription.trust_status = TrustStatus.TRUSTED

                        st.rerun()