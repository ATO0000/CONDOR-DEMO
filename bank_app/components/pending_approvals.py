from html import escape

import streamlit as st

from bank_app.app_models import AuthorizationStatus
from bank_app.services.authorization_service import (
    approve_authorization,
    reject_authorization,
)
from bank_app.state.bank_state import BankState


# ============================================================
# HELPERS
# ============================================================

def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_pending_approvals(bank: BankState) -> None:

    st.title("Autorizaciones")

    st.caption(
        "Revisa los cobros retenidos antes de que se procesen."
    )

    st.write("")

    pending = [
        authorization
        for authorization in bank.pending_authorizations
        if authorization.status == AuthorizationStatus.PENDING
    ]

    resolved = [
        authorization
        for authorization in bank.pending_authorizations
        if authorization.status != AuthorizationStatus.PENDING
    ]

    # ========================================================
    # EMPTY STATE
    # ========================================================

    if not pending:

        st.success(
            "No tienes cobros pendientes de aprobación."
        )

        if resolved:
            render_resolved_authorizations(
                bank,
                resolved,
            )

        return

    # ========================================================
    # SUMMARY
    # ========================================================

    total_held = sum(
        authorization.attempted_amount
        for authorization in pending
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Cobros retenidos",
            len(pending),
        )

    with col2:

        st.metric(
            "Monto pendiente",
            format_clp(total_held),
        )

    st.write("")

    # ========================================================
    # PENDING AUTHORIZATIONS
    # ========================================================

    st.markdown("### Requieren tu decisión")

    for authorization in pending:

        subscription = bank.get_subscription_by_id(
            authorization.subscription_id
        )

        transaction = bank.get_transaction_by_id(
            authorization.transaction_id
        )

        if subscription is None or transaction is None:
            continue

        merchant = escape(subscription.merchant)

        with st.container(border=True):

            # =================================================
            # HEADER
            # =================================================

            header_col, status_col = st.columns(
                [4, 1],
                vertical_alignment="center",
            )

            with header_col:

                st.markdown(
                    f"### {merchant}"
                )

                st.caption(
                    "Cambio de precio detectado"
                )

            with status_col:

                st.html(
                    '<span class="pill pill-alert">'
                    "Retenido"
                    "</span>"
                )

            st.divider()

            # =================================================
            # AMOUNTS
            # =================================================

            previous_col, attempted_col, increase_col = st.columns(
                3
            )

            with previous_col:

                st.caption("Precio anterior")

                st.markdown(
                    f"**{format_clp(authorization.previous_amount)}**"
                )

            with attempted_col:

                st.caption("Nuevo cobro")

                st.markdown(
                    f"**{format_clp(authorization.attempted_amount)}**"
                )

            with increase_col:

                st.caption("Variación")

                st.markdown(
                    f"**+{authorization.percentage_change:.1f}%**"
                )

            st.write("")

            st.caption(
                "Este cobro todavía no ha sido descontado de tu cuenta."
            )

            # =================================================
            # DECISION
            # =================================================

            approve_col, reject_col = st.columns(
                2,
                gap="medium",
            )

            with approve_col:

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

                        st.session_state[
                            "authorization_feedback"
                        ] = (
                            f"El cobro de {subscription.merchant} "
                            "fue aprobado."
                        )

                        st.rerun()

                    except ValueError as error:

                        st.error(str(error))

            with reject_col:

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

                        st.session_state[
                            "authorization_feedback"
                        ] = (
                            f"El cobro de {subscription.merchant} "
                            "fue rechazado."
                        )

                        st.rerun()

                    except ValueError as error:

                        st.error(str(error))

    # ========================================================
    # FEEDBACK
    # ========================================================

    if "authorization_feedback" in st.session_state:

        st.success(
            st.session_state.pop(
                "authorization_feedback"
            )
        )

    # ========================================================
    # RESOLVED
    # ========================================================

    if resolved:

        render_resolved_authorizations(
            bank,
            resolved,
        )


# ============================================================
# RESOLVED AUTHORIZATIONS
# ============================================================

def render_resolved_authorizations(
    bank: BankState,
    authorizations,
) -> None:

    st.write("")
    st.markdown("### Operaciones recientes")

    rows = []

    for authorization in reversed(
        authorizations[-5:]
    ):

        subscription = bank.get_subscription_by_id(
            authorization.subscription_id
        )

        if subscription is None:
            continue

        merchant = escape(
            subscription.merchant
        )

        if (
            authorization.status
            == AuthorizationStatus.APPROVED
        ):

            status_html = (
                '<span class="pill pill-ok">'
                "Aprobado"
                "</span>"
            )

        else:

            status_html = (
                '<span class="pill pill-neutral">'
                "Rechazado"
                "</span>"
            )

        rows.append(
            f"""
            <div class="bank-row">

                <div class="row-main">

                    <div class="row-title">
                        {merchant}
                    </div>

                    <div class="row-subtitle">
                        Cambio de precio
                    </div>

                </div>

                <div style="
                    display:flex;
                    align-items:center;
                    gap:1.2rem;
                    margin-left:auto;
                ">

                    {status_html}

                    <div class="row-amount"
                         style="min-width:95px;text-align:right;">
                        {format_clp(
                            authorization.attempted_amount
                        )}
                    </div>

                </div>

            </div>
            """
        )

    if rows:

        st.html(
            '<div class="bank-list">'
            + "".join(rows)
            + "</div>"
        )