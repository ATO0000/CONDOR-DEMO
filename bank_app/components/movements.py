from html import escape

import streamlit as st

from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def get_transaction_label(
    bank: BankState,
    transaction,
) -> tuple[str, str]:

    pending_candidate = next(
        (
            candidate
            for candidate in bank.subscription_candidates
            if (
                candidate.transaction_id == transaction.id
                and candidate.status.value
                == "PENDING_CONFIRMATION"
            )
        ),
        None,
    )

    if pending_candidate is not None:
        return "Posible suscripción", "pill-watch"

    if transaction.status.value == "PENDING_APPROVAL":
        return "Pendiente de aprobación", "pill-alert"

    if transaction.status.value == "REJECTED":
        return "Rechazado", "pill-neutral"

    if transaction.status.value == "APPROVED":
        return "Aprobado", "pill-ok"

    if transaction.recurring_type == "SUBSCRIPTION":
        return "Suscripción", "pill-watch"

    if transaction.recurring_type == "RECURRING_BILL":
        return "Pago recurrente", "pill-neutral"

    return "Compra", "pill-neutral"


def render_movements(bank: BankState) -> None:

    st.title("Movimientos")

    st.caption(
        "Historial de transacciones de tu cuenta."
    )

    st.write("")

    if not bank.transactions:
        st.info("No hay movimientos registrados.")
        return

    # ========================================================
    # RESUMEN
    # ========================================================

    pending_count = sum(
        1
        for transaction in bank.transactions
        if transaction.status.value == "PENDING_APPROVAL"
    )

    recurring_count = sum(
        1
        for transaction in bank.transactions
        if transaction.recurring_type in {
            "SUBSCRIPTION",
            "RECURRING_BILL",
        }
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Movimientos",
            len(bank.transactions),
        )

    with col2:
        st.metric(
            "Pagos recurrentes",
            recurring_count,
        )

    with col3:
        st.metric(
            "Pendientes",
            pending_count,
        )

    st.write("")

    # ========================================================
    # LISTA
    # ========================================================

    transactions = sorted(
        bank.transactions,
        key=lambda transaction: transaction.date,
        reverse=True,
    )

    rows = []

    for transaction in transactions:

        merchant = escape(
            transaction.merchant
        )

        date_text = transaction.date.strftime(
            "%d/%m/%Y · %H:%M"
        )

        label, pill_class = get_transaction_label(
            bank,
            transaction,
        )

        rows.append(
            f"""
            <div class="bank-row">

                <div class="row-main">

                    <div class="row-title">
                        {merchant}
                    </div>

                    <div class="row-subtitle">
                        {date_text}
                    </div>

                </div>

                <div style="
                    display:flex;
                    align-items:center;
                    gap:1.2rem;
                    margin-left:auto;
                ">

                    <span class="pill {pill_class}">
                        {label}
                    </span>

                    <div class="row-amount"
                         style="min-width:95px;text-align:right;">
                        -{format_clp(transaction.amount)}
                    </div>

                </div>

            </div>
            """
        )

    st.html(
        '<div class="bank-list">'
        + "".join(rows)
        + "</div>"
    )