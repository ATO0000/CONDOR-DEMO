import streamlit as st

from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    """
    Formatea un monto como pesos chilenos.
    Ejemplo:
    1250000 -> $1.250.000
    """

    formatted = f"{amount:,.0f}"
    formatted = formatted.replace(",", ".")

    return f"${formatted}"


def render_dashboard(bank: BankState) -> None:
    """
    Renderiza la pantalla principal del banco.
    """

    st.title("Inicio")

    st.caption(
        "Resumen de tu cuenta y protección de pagos recurrentes."
    )

    # ========================================================
    # CUENTA PRINCIPAL
    # ========================================================

    with st.container(border=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.caption("Saldo disponible")

            st.markdown(
                f"## {format_clp(bank.balance)}"
            )

            st.caption(
                "Cuenta Corriente •••• 4821"
            )

        with col2:
            st.caption("Estado")

            st.success("Cuenta activa")


    st.write("")


    # ========================================================
    # MÉTRICAS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Movimientos",
            len(bank.transactions),
        )

    with col2:
        active_subscriptions = sum(
            1
            for subscription in bank.subscriptions
            if subscription.status.value == "ACTIVE"
        )

        st.metric(
            "Suscripciones",
            active_subscriptions,
        )

    with col3:
        st.metric(
            "Por confirmar",
            len(bank.subscription_candidates),
        )

    with col4:
        pending_count = sum(
            1
            for authorization in bank.pending_authorizations
            if authorization.status.value == "PENDING"
        )

        st.metric(
            "Cobros pendientes",
            pending_count,
        )


    st.write("")


    # ========================================================
    # CONTENIDO PRINCIPAL
    # ========================================================

    left, right = st.columns([1.7, 1])


    # ========================================================
    # MOVIMIENTOS RECIENTES
    # ========================================================

    with left:
        st.subheader("Movimientos recientes")

        with st.container(border=True):

            if not bank.transactions:
                st.info(
                    "Todavía no hay movimientos registrados."
                )

            else:
                recent_transactions = bank.transactions[-5:]
                recent_transactions.reverse()

                for transaction in recent_transactions:

                    col_name, col_amount = st.columns([3, 1])

                    with col_name:
                        st.markdown(
                            f"**{transaction.merchant}**"
                        )

                        st.caption(
                            transaction.date.strftime(
                                "%d/%m/%Y"
                            )
                        )

                    with col_amount:
                        st.markdown(
                            f"**-{format_clp(transaction.amount)}**"
                        )

                    st.divider()


    # ========================================================
    # CENTRO DE PROTECCIÓN
    # ========================================================

    with right:
        st.subheader("Centro de protección")

        with st.container(border=True):

            if bank.pending_authorizations:
                st.warning(
                    "Tienes cobros esperando tu aprobación."
                )

            elif bank.subscription_candidates:
                st.warning(
                    "Detectamos posibles suscripciones "
                    "que necesitan tu confirmación."
                )

            else:
                st.success(
                    "No hay cobros que requieran tu atención."
                )

            st.caption(
                "Supervisamos tus pagos recurrentes para "
                "detectar cambios inesperados."
            )


    st.write("")


    # ========================================================
    # SUSCRIPCIONES
    # ========================================================

    st.subheader("Suscripciones")

    with st.container(border=True):

        if not bank.subscriptions:

            st.info(
                "Aún no hay suscripciones confirmadas."
            )

        else:

            for subscription in bank.subscriptions[:4]:

                col1, col2, col3 = st.columns(
                    [2, 1, 1]
                )

                with col1:
                    st.markdown(
                        f"**{subscription.merchant}**"
                    )

                    st.caption(
                        subscription.recurring_type
                    )

                with col2:
                    st.write(
                        format_clp(
                            subscription.current_price
                        )
                    )

                with col3:

                    if (
                        subscription.trust_status.value
                        == "TRUSTED"
                    ):
                        st.success("De confianza")

                    else:
                        st.warning("Supervisada")