import streamlit as st

from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_movements(bank: BankState) -> None:
    st.title("Movimientos")

    st.caption(
        "Revisa tus transacciones y los pagos recurrentes detectados."
    )

    st.write("")

    if not bank.transactions:
        st.info("No hay movimientos registrados.")
        return

    # Más recientes primero
    transactions = sorted(
        bank.transactions,
        key=lambda transaction: transaction.date,
        reverse=True,
    )

    for transaction in transactions:

        with st.container(border=True):

            col1, col2 = st.columns([3, 1])

            # =================================================
            # INFORMACIÓN PRINCIPAL
            # =================================================

            with col1:

                st.markdown(
                    f"### {transaction.merchant}"
                )

                st.caption(
                    transaction.date.strftime(
                        "%d/%m/%Y - %H:%M"
                    )
                )

            with col2:

                st.markdown(
                    f"### -{format_clp(transaction.amount)}"
                )

            # =================================================
            # CLASIFICACIÓN
            # =================================================

            if transaction.recurring_type == "SUBSCRIPTION":

                st.info(
                    "🔁 Este pago corresponde a una suscripción."
                )

                st.caption(
                    "El sistema identificó comportamiento recurrente "
                    "asociado a este comercio."
                )

            elif transaction.recurring_type == "RECURRING_BILL":

                st.info(
                    "🔁 Este pago corresponde a un cobro recurrente."
                )

            else:

                st.caption(
                    "Compra normal"
                )

            # =================================================
            # ESTADO DE LA TRANSACCIÓN
            # =================================================

            if transaction.status.value == "PENDING_APPROVAL":

                st.warning(
                    "⏳ Este cobro está esperando tu aprobación."
                )

            elif transaction.status.value == "REJECTED":

                st.error(
                    "Cobro rechazado"
                )

            elif transaction.status.value == "APPROVED":

                st.success(
                    "Cobro aprobado"
                )