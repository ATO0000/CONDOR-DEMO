import streamlit as st

from bank_app.app_models import AuthorizationStatus
from bank_app.services.authorization_service import (
    approve_authorization,
    reject_authorization,
)
from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_pending_approvals(bank: BankState) -> None:
    st.title("Autorizaciones pendientes")

    st.caption(
        "Revisa los cobros que fueron detenidos antes de ejecutarse."
    )

    pending = [
        authorization
        for authorization in bank.pending_authorizations
        if authorization.status == AuthorizationStatus.PENDING
    ]

    if not pending:
        st.success(
            "No tienes cobros pendientes de aprobación."
        )
        return

    st.write("")

    for authorization in pending:

        subscription = bank.get_subscription_by_id(
            authorization.subscription_id
        )

        transaction = bank.get_transaction_by_id(
            authorization.transaction_id
        )

        if subscription is None or transaction is None:
            continue

        with st.container(border=True):

            st.error("⚠ CAMBIO DE PRECIO DETECTADO")

            st.markdown(
                f"## {subscription.merchant}"
            )

            st.write(
                f"{subscription.merchant} intentó cobrar "
                f"**{format_clp(authorization.attempted_amount)}**."
            )

            st.write("")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption("Precio anterior")
                st.markdown(
                    f"### {format_clp(authorization.previous_amount)}"
                )

            with col2:
                st.caption("Nuevo precio")
                st.markdown(
                    f"### {format_clp(authorization.attempted_amount)}"
                )

            with col3:
                st.caption("Aumento")
                st.markdown(
                    f"### +{authorization.percentage_change:.1f}%"
                )

            st.warning(
                "El cobro está temporalmente detenido "
                "y todavía no ha sido descontado de tu cuenta."
            )

            st.write("")

            col_approve, col_reject = st.columns(2)

            with col_approve:

                if st.button(
                    "Aprobar cobro",
                    key=f"approve-{authorization.id}",
                    type="primary",
                    use_container_width=True,
                ):

                    try:
                        approve_authorization(
                            bank,
                            authorization.id,
                        )

                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

            with col_reject:

                if st.button(
                    "Rechazar cobro",
                    key=f"reject-{authorization.id}",
                    use_container_width=True,
                ):

                    try:
                        reject_authorization(
                            bank,
                            authorization.id,
                        )

                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))