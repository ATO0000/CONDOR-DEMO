from html import escape

from bank_app.state.bank_state import BankState

import streamlit as st

from bank_app.app_models import (
    SubscriptionCandidateStatus,
    SubscriptionStatus,
    TrustStatus,
)

from bank_app.components.subscription_candidate_actions import (
    render_candidate_actions,
)



# ============================================================
# HELPERS
# ============================================================

def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def format_confidence(value: float | None) -> str:
    if value is None:
        return "No disponible"

    return f"{value * 100:.1f}%"


def recurring_type_label(value: str) -> str:
    labels = {
        "SUBSCRIPTION": "Suscripción",
        "RECURRING_BILL": "Pago recurrente",
        "UNKNOWN_RECURRING": "Pago recurrente",
    }

    return labels.get(value, value)


def trust_pill(subscription) -> str:

    if subscription.trust_status == TrustStatus.TRUSTED:
        return (
            '<span class="pill pill-ok">'
            "De confianza"
            "</span>"
        )

    return (
        '<span class="pill pill-watch">'
        "Supervisada"
        "</span>"
    )


def status_pill(subscription) -> str:

    if subscription.status == SubscriptionStatus.ACTIVE:
        return (
            '<span class="pill pill-ok">'
            "Activa"
            "</span>"
        )

    return (
        '<span class="pill pill-neutral">'
        "Cancelada"
        "</span>"
    )


# ============================================================
# SUBSCRIPTION ROW
# ============================================================

def render_subscription(
    bank: BankState,
    subscription,
) -> None:

    merchant = escape(subscription.merchant)

    col_name, col_price, col_trust, col_status = st.columns(
        [2.4, 1, 1.25, 0.9],
        vertical_alignment="center",
    )

    # --------------------------------------------------------
    # MERCHANT
    # --------------------------------------------------------

    with col_name:

        st.markdown(
            f"**{merchant}**"
        )

        st.caption(
            f"{recurring_type_label(subscription.recurring_type)}"
            f" · {subscription.frequency}"
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    with col_price:

        st.markdown(
            f"**{format_clp(subscription.current_price)}**"
        )

        st.caption(
            "Precio actual"
        )

    # --------------------------------------------------------
    # TRUST
    # --------------------------------------------------------

    with col_trust:

        st.html(
            trust_pill(subscription)
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    with col_status:

        st.html(
            status_pill(subscription)
        )

    if subscription.needs_user_verification:
        st.caption("Por verificar")

    # ========================================================
    # DETAILS
    # ========================================================

    with st.expander("Administrar"):

        info_col, detector_col = st.columns(
            [1, 1],
            gap="large",
        )

        # ----------------------------------------------------
        # SUBSCRIPTION INFO
        # ----------------------------------------------------

        with info_col:

            st.markdown("#### Detalle")

            st.write(
                f"**Precio actual:** "
                f"{format_clp(subscription.current_price)}"
            )

            st.write(
                f"**Frecuencia:** "
                f"{subscription.frequency}"
            )

            st.write(
                f"**Último cobro:** "
                f"{subscription.last_charge_date.strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**Estado:** "
                f"{'Activa' if subscription.status == SubscriptionStatus.ACTIVE else 'Cancelada'}"
            )

            st.write(
                f"**Confianza:** "
                f"{'De confianza' if subscription.trust_status == TrustStatus.TRUSTED else 'Supervisada'}"
            )

        # ----------------------------------------------------
        # DETECTOR INFO
        # ----------------------------------------------------

        with detector_col:

            st.markdown("#### Información del detector")

            st.write(
                "**Probabilidad de recurrencia:** "
                f"{format_confidence(subscription.recurrence_confidence)}"
            )

            st.write(
                "**Confianza del tipo:** "
                f"{format_confidence(subscription.type_confidence)}"
            )

            if subscription.detection_reasons:

                with st.popover("Ver razones de detección"):

                    for reason in subscription.detection_reasons:
                        st.write(f"• {reason}")

            else:

                st.caption(
                    "No hay información adicional del detector."
                )

        # ====================================================
        # HISTORY
        # ====================================================

        st.divider()

        st.markdown("#### Historial")

        if subscription.transaction_history:

            for transaction_id in subscription.transaction_history:

                transaction = bank.get_transaction_by_id(
                    transaction_id
                )

                if transaction is None:
                    continue

                date_col, amount_col = st.columns(
                    [3, 1]
                )

                with date_col:

                    st.write(
                        transaction.date.strftime(
                            "%d/%m/%Y"
                        )
                    )

                with amount_col:

                    st.write(
                        format_clp(
                            transaction.amount
                        )
                    )

        else:

            st.caption(
                "No hay cobros registrados."
            )

        # ====================================================
        # MANAGEMENT
        # ====================================================

        st.divider()

        st.markdown("#### Gestión")

        if subscription.status == SubscriptionStatus.ACTIVE:

            action_col, cancel_col = st.columns(
                [1, 1],
                gap="large",
            )

            # ------------------------------------------------
            # TRUST
            # ------------------------------------------------

            with action_col:

                st.caption("Nivel de confianza")

                if subscription.trust_status == TrustStatus.TRUSTED:

                    st.write(
                        "Los cobros de esta suscripción "
                        "se procesan con menor fricción."
                    )

                    if st.button(
                        "Pasar a supervisada",
                        key=f"untrust-{subscription.id}",
                        use_container_width=True,
                    ):

                        subscription.trust_status = (
                            TrustStatus.UNTRUSTED
                        )

                        st.rerun()

                else:

                    st.write(
                        "Los aumentos de precio requieren "
                        "tu aprobación."
                    )

                    if st.button(
                        "Marcar como de confianza",
                        key=f"trust-{subscription.id}",
                        use_container_width=True,
                    ):

                        subscription.trust_status = (
                            TrustStatus.TRUSTED
                        )

                        st.rerun()

            # ------------------------------------------------
            # CANCEL
            # ------------------------------------------------

            with cancel_col:

                st.caption("Cancelar suscripción")

                st.write(
                    "La cancelación se simula dentro "
                    "del gemelo digital."
                )

                confirm_cancel = st.checkbox(
                    "Confirmar cancelación",
                    key=f"confirm-cancel-{subscription.id}",
                )

                if st.button(
                    "Cancelar suscripción",
                    key=f"cancel-{subscription.id}",
                    use_container_width=True,
                    disabled=not confirm_cancel,
                ):

                    subscription.status = (
                        SubscriptionStatus.CANCELLED
                    )

                    st.rerun()

        else:

            st.caption(
                "Esta suscripción fue cancelada. "
                "Su historial se conserva en la cuenta."
            )


# ============================================================
# PAGE
# ============================================================

def render_subscriptions(bank: BankState) -> None:

    st.title("Suscripciones")

    if "subscription_feedback" in st.session_state:
        st.success(st.session_state.pop("subscription_feedback"))

    st.caption(
        "Administra tus pagos recurrentes y su nivel de confianza."
    )

    st.write("")

    # ========================================================
    # PENDING CONFIRMATION
    # ========================================================

    pending_candidates = [
        candidate
        for candidate in bank.subscription_candidates
        if (
            candidate.status
            == SubscriptionCandidateStatus.PENDING_CONFIRMATION
        )
    ]

    if pending_candidates:

        st.markdown("### Por confirmar")

        st.caption(
            "Detectamos pagos que podrían corresponder "
            "a nuevas suscripciones."
        )

        for candidate in pending_candidates:

            transaction = bank.get_transaction_by_id(
                candidate.transaction_id
            )

            if transaction is None:
                continue

            with st.container(border=True):

                info_col, amount_col = st.columns(
                    [3, 1],
                    vertical_alignment="center",
                )

                with info_col:

                    st.markdown(
                        f"**{candidate.merchant}**"
                    )

                    st.caption(
                        "Posible suscripción detectada"
                    )

                with amount_col:

                    st.markdown(
                        f"**{format_clp(transaction.amount)}**"
                    )

                    st.caption(
                        "Primer cobro"
                    )

                render_candidate_actions(bank, candidate, key_prefix="subscriptions")

        st.write("")

    # ========================================================
    # ACTIVE / CANCELLED
    # ========================================================

    active_subscriptions = [
        subscription
        for subscription in bank.subscriptions
        if subscription.status == SubscriptionStatus.ACTIVE
    ]

    cancelled_subscriptions = [
        subscription
        for subscription in bank.subscriptions
        if subscription.status == SubscriptionStatus.CANCELLED
    ]

    # ========================================================
    # SUMMARY
    # ========================================================

    trusted_count = sum(
        1
        for subscription in active_subscriptions
        if subscription.trust_status == TrustStatus.TRUSTED
    )

    supervised_count = (
        len(active_subscriptions)
        - trusted_count
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Activas",
            len(active_subscriptions),
        )

    with col2:
        st.metric(
            "Supervisadas",
            supervised_count,
        )

    with col3:
        st.metric(
            "De confianza",
            trusted_count,
        )

    st.write("")

    # ========================================================
    # ACTIVE SUBSCRIPTIONS
    # ========================================================

    st.markdown("### Suscripciones activas")

    if not active_subscriptions:

        st.info(
            "No tienes suscripciones activas."
        )

    else:

        with st.container(border=True):

            for index, subscription in enumerate(
                active_subscriptions
            ):

                render_subscription(
                    bank,
                    subscription,
                )

                if index < len(active_subscriptions) - 1:
                    st.divider()

    # ========================================================
    # CANCELLED SUBSCRIPTIONS
    # ========================================================

    if cancelled_subscriptions:

        st.write("")

        st.markdown("### Canceladas")

        st.caption(
            "Se mantienen visibles para conservar el historial."
        )

        with st.container(border=True):

            for index, subscription in enumerate(
                cancelled_subscriptions
            ):

                render_subscription(
                    bank,
                    subscription,
                )

                if index < len(cancelled_subscriptions) - 1:
                    st.divider()