from html import escape
from textwrap import dedent

import streamlit as st

from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def render_html(content: str) -> None:
    """
    Renderiza HTML directamente, sin pasar por Markdown.
    """
    st.html(
        dedent(content).strip()
    )


def transaction_status(transaction) -> str:

    if transaction.status.value == "PENDING_APPROVAL":
        return "Pendiente"

    if transaction.status.value == "REJECTED":
        return "Rechazado"

    if transaction.status.value == "APPROVED":
        return "Aprobado"

    if transaction.recurring_type == "SUBSCRIPTION":
        return "Suscripción"

    if transaction.recurring_type == "RECURRING_BILL":
        return "Pago recurrente"

    return "Compra"


def render_dashboard(bank: BankState) -> None:

    active_subscriptions = [
        subscription
        for subscription in bank.subscriptions
        if subscription.status.value == "ACTIVE"
    ]

    trusted_count = sum(
        1
        for subscription in active_subscriptions
        if subscription.trust_status.value == "TRUSTED"
    )

    supervised_count = sum(
        1
        for subscription in active_subscriptions
        if subscription.trust_status.value == "UNTRUSTED"
    )

    pending_count = sum(
        1
        for authorization in bank.pending_authorizations
        if authorization.status.value == "PENDING"
    )

    pending_candidates = sum(
        1
        for candidate in bank.subscription_candidates
        if candidate.status.value == "PENDING_CONFIRMATION"
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.title("Inicio")

    render_html(
        """
        <div class="page-heading">
            <div class="subtitle">
                Resumen de tu cuenta
            </div>
        </div>
        """
    )

    # ========================================================
    # ACCOUNT
    # ========================================================

    render_html(
        f"""
        <div class="account-card">
            <div class="account-top">

                <div>
                    <div class="account-label">
                        Saldo disponible
                    </div>

                    <div class="account-balance">
                        {format_clp(bank.balance)}
                    </div>

                    <div class="account-number">
                        Cuenta corriente •••• 4821
                    </div>
                </div>

                <div class="account-type">
                    Cuenta principal
                </div>

            </div>
        </div>
        """
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    render_html(
        f"""
        <div class="summary-strip">

            <div class="summary-item">
                <div class="summary-label">
                    Suscripciones
                </div>
                <div class="summary-value">
                    {len(active_subscriptions)}
                </div>
            </div>

            <div class="summary-item">
                <div class="summary-label">
                    Supervisadas
                </div>
                <div class="summary-value">
                    {supervised_count}
                </div>
            </div>

            <div class="summary-item">
                <div class="summary-label">
                    De confianza
                </div>
                <div class="summary-value">
                    {trusted_count}
                </div>
            </div>

            <div class="summary-item">
                <div class="summary-label">
                    Pendientes
                </div>
                <div class="summary-value">
                    {pending_count}
                </div>
            </div>

        </div>
        """
    )

    # ========================================================
    # PROTECTION STATUS
    # ========================================================

    if pending_count > 0:

        protection_title = (
            f"{pending_count} cobro"
            f"{'s' if pending_count != 1 else ''} pendiente"
            f"{'s' if pending_count != 1 else ''}"
        )

        protection_copy = (
            "El cobro está retenido hasta que lo apruebes o rechaces."
        )

        protection_status = (
            '<span class="pill pill-alert">'
            "Requiere atención"
            "</span>"
        )

    elif pending_candidates > 0:

        protection_title = (
            "Hay nuevas suscripciones por revisar"
        )

        protection_copy = (
            "Confirma si reconoces los pagos detectados."
        )

        protection_status = (
            '<span class="pill pill-watch">'
            "Por revisar"
            "</span>"
        )

    else:

        protection_title = (
            "Protección de suscripciones activa"
        )

        protection_copy = (
            "No hay cobros que requieran una acción."
        )

        protection_status = (
            '<span class="pill pill-ok">'
            "Al día"
            "</span>"
        )

    render_html(
        f"""
        <div class="protection-card">

            <div>
                <div class="protection-title">
                    {protection_title}
                </div>

                <div class="protection-copy">
                    {protection_copy}
                </div>
            </div>

            {protection_status}

        </div>
        """
    )

    # ========================================================
    # MAIN CONTENT
    # ========================================================

    left, right = st.columns(
        [1.35, 1],
        gap="large",
    )

    # ========================================================
    # MOVEMENTS
    # ========================================================

    with left:

        render_html(
            '<div class="section-title">'
            'Movimientos recientes'
            '</div>'
        )

        recent_transactions = sorted(
            bank.transactions,
            key=lambda item: item.date,
            reverse=True,
        )[:5]

        if not recent_transactions:

            st.info("No hay movimientos recientes.")

        else:

            rows = []

            for transaction in recent_transactions:

                merchant = escape(
                    transaction.merchant
                )

                status = transaction_status(
                    transaction
                )

                date_text = transaction.date.strftime(
                    "%d/%m/%Y"
                )

                rows.append(
                    dedent(
                        f"""
                        <div class="bank-row">

                            <div class="row-main">

                                <div class="row-title">
                                    {merchant}
                                </div>

                                <div class="row-subtitle">
                                    {date_text} · {status}
                                </div>

                            </div>

                            <div class="row-amount">
                                -{format_clp(transaction.amount)}
                            </div>

                        </div>
                        """
                    ).strip()
                )

            render_html(
                '<div class="bank-list">'
                + "".join(rows)
                + "</div>"
            )

    # ========================================================
    # SUBSCRIPTIONS
    # ========================================================

    with right:

        render_html(
            '<div class="section-title">'
            'Suscripciones'
            '</div>'
        )

        if not active_subscriptions:

            st.info(
                "No hay suscripciones activas."
            )

        else:

            rows = []

            for subscription in active_subscriptions[:5]:

                merchant = escape(
                    subscription.merchant
                )

                frequency = escape(
                    subscription.frequency
                )

                if (
                    subscription.trust_status.value
                    == "TRUSTED"
                ):

                    status_html = (
                        '<span class="pill pill-ok">'
                        "De confianza"
                        "</span>"
                    )

                else:

                    status_html = (
                        '<span class="pill pill-watch">'
                        "Supervisada"
                        "</span>"
                    )

                rows.append(
                    dedent(
                        f"""
                        <div class="bank-row">

                            <div class="row-main">

                                <div class="row-title">
                                    {merchant}
                                </div>

                                <div class="row-subtitle">
                                    {format_clp(subscription.current_price)}
                                    · {frequency}
                                </div>

                            </div>

                            {status_html}

                        </div>
                        """
                    ).strip()
                )

            render_html(
                '<div class="bank-list">'
                + "".join(rows)
                + "</div>"
            )