import streamlit as st

from bank_app.app_models import TransactionStatus
from bank_app.services.transaction_service import (
    simulate_subscription_charge,
)
from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_simulator(bank: BankState) -> None:
    st.title("Simulador de cobros")

    st.caption(
        "Simula la llegada de un nuevo cobro de una suscripción conocida."
    )

    st.write("")

    active_subscriptions = [
        subscription
        for subscription in bank.subscriptions
        if subscription.status.value == "ACTIVE"
    ]

    if not active_subscriptions:
        st.info("No existen suscripciones activas para simular.")
        return

    # ========================================================
    # SELECCIÓN
    # ========================================================

    subscription_by_name = {
        subscription.merchant: subscription
        for subscription in active_subscriptions
    }

    selected_name = st.selectbox(
        "Suscripción",
        options=list(subscription_by_name.keys()),
    )

    subscription = subscription_by_name[selected_name]

    # ========================================================
    # INFORMACIÓN ACTUAL
    # ========================================================

    with st.container(border=True):

        col1, col2, col3 = st.columns(3)

        with col1:
            st.caption("Precio conocido")
            st.markdown(
                f"### {format_clp(subscription.current_price)}"
            )

        with col2:
            st.caption("Estado de confianza")

            if subscription.trust_status.value == "TRUSTED":
                st.success("De confianza")
            else:
                st.warning("Supervisada")

        with col3:
            st.caption("Estado")
            st.success(subscription.status.value)

    st.write("")

    # ========================================================
    # NUEVO COBRO
    # ========================================================

    attempted_amount = st.number_input(
        "Nuevo intento de cobro",
        min_value=1.0,
        value=float(subscription.current_price),
        step=100.0,
        key=f"amount-{subscription.id}",
    )

    price_difference = (
        attempted_amount - subscription.current_price
    )

    if price_difference > 0:

        percentage_change = (
            price_difference
            / subscription.current_price
        ) * 100

        st.warning(
            f"Aumento detectado: "
            f"{format_clp(price_difference)} "
            f"(+{percentage_change:.1f}%)"
        )

    elif price_difference < 0:

        percentage_change = (
            abs(price_difference)
            / subscription.current_price
        ) * 100

        st.info(
            f"Disminución de precio: "
            f"{format_clp(abs(price_difference))} "
            f"(-{percentage_change:.1f}%)"
        )

    else:

        st.caption(
            "El monto coincide con el precio conocido."
        )

    st.write("")

    # ========================================================
    # SIMULAR
    # ========================================================

    if st.button(
        "Simular intento de cobro",
        type="primary",
        use_container_width=True,
    ):

        try:

            transaction = simulate_subscription_charge(
                bank=bank,
                subscription_id=subscription.id,
                attempted_amount=attempted_amount,
            )

            # =================================================
            # COBRO DETENIDO
            # =================================================

            if (
                transaction.status
                == TransactionStatus.PENDING_APPROVAL
            ):

                st.error(
                    "🛡️ Cobro detenido antes de ejecutarse"
                )

                st.warning(
                    f"{subscription.merchant} intentó cobrar "
                    f"{format_clp(attempted_amount)}, pero el precio "
                    f"conocido era "
                    f"{format_clp(subscription.current_price)}."
                )

                st.info(
                    "Como esta suscripción está supervisada, "
                    "el cobro requiere aprobación del usuario."
                )

            # =================================================
            # COBRO PROCESADO
            # =================================================

            elif (
                transaction.status
                == TransactionStatus.COMPLETED
            ):

                st.success(
                    "Cobro procesado correctamente."
                )

                st.write(
                    f"Nuevo saldo: **{format_clp(bank.balance)}**"
                )

        except ValueError as error:

            st.error(str(error))