from bank_app.components.manual_transaction import render_manual_transaction
from bank_app.services.subscription_detection_policy import (
    SubscriptionDetectionAction,
    decide_subscription_action,
)
import json
from pathlib import Path

import streamlit as st

from bank_app.app_models import (
    SubscriptionCandidateStatus,
    TransactionStatus,
)
from bank_app.services.incoming_transaction_service import (
    process_incoming_transaction,
)
from bank_app.components.subscription_candidate_actions import (
    render_candidate_actions,
)
from bank_app.services.transaction_service import (
    simulate_subscription_charge,
)
from bank_app.state.bank_state import BankState
from bank_app.services.controlled_demo_service import (
    DEMO_AMOUNT,
    DEMO_MERCHANT,
    DEMO_NOTICE,
    DEMO_TRANSACTION_KEY,
    intermediate_demo_analysis,
    process_intermediate_demo,
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EVALUATION_DATA_PATH = (
    PROJECT_ROOT / "evaluation_transactions.json"
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


def load_evaluation_transactions() -> list[dict]:
    with open(
        EVALUATION_DATA_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# KNOWN SUBSCRIPTION CHARGE
# ============================================================

def render_known_subscription_charge(
    bank: BankState,
) -> None:

    st.subheader("Nuevo cobro de una suscripción")

    st.html(
        """
        <div class="scenario-box">
            <div class="scenario-title">
                Escenario: cambio de precio
            </div>

            <div class="scenario-copy">
                Simula un nuevo intento de cobro de una suscripción
                que el banco ya conoce. Permite comprobar qué ocurre
                cuando el monto cambia.
            </div>
        </div>
        """
    )

    active_subscriptions = [
        subscription
        for subscription in bank.subscriptions
        if subscription.status.value == "ACTIVE"
    ]

    if not active_subscriptions:
        st.info(
            "No existen suscripciones activas para simular."
        )
        return

    subscription_by_name = {
        subscription.merchant: subscription
        for subscription in active_subscriptions
    }

    selected_name = st.selectbox(
        "Suscripción",
        options=list(subscription_by_name.keys()),
        key="known-subscription-selector",
    )

    subscription = subscription_by_name[selected_name]

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

            st.success(
                subscription.status.value
            )

    attempted_amount = st.number_input(
        "Nuevo intento de cobro",
        min_value=1.0,
        value=float(subscription.current_price),
        step=100.0,
        key=f"amount-{subscription.id}",
    )

    price_difference = (
        attempted_amount
        - subscription.current_price
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

    if st.button(
        "Simular intento de cobro",
        type="primary",
        use_container_width=True,
        key="simulate-known-charge",
    ):

        try:

            transaction = simulate_subscription_charge(
                bank=bank,
                subscription_id=subscription.id,
                attempted_amount=attempted_amount,
            )

            if (
                transaction.status
                == TransactionStatus.PENDING_APPROVAL
            ):

                st.error(
                    "🛡️ Cobro detenido antes de ejecutarse"
                )

                st.warning(
                    f"{subscription.merchant} intentó cobrar "
                    f"{format_clp(attempted_amount)}, "
                    f"pero el precio conocido era "
                    f"{format_clp(subscription.current_price)}."
                )

                st.info(
                    "Como esta suscripción está supervisada, "
                    "el cobro requiere aprobación del usuario."
                )

            elif (
                transaction.status
                == TransactionStatus.COMPLETED
            ):

                st.success(
                    "Cobro procesado correctamente."
                )

                st.write(
                    f"Nuevo saldo: "
                    f"**{format_clp(bank.balance)}**"
                )

        except ValueError as error:

            st.error(str(error))


# ============================================================
# NEW TRANSACTION
# ============================================================

def render_new_transaction(
    bank: BankState,
) -> None:

    st.subheader("Primer cobro de un comercio")

    scenario = st.segmented_control(
        "Origen del cobro",
        ["Dataset de demostración", "Crear cobro manual", "Confianza intermedia"],
        default="Dataset de demostración",
        key="first-charge-scenario",
    )
    if scenario == "Crear cobro manual":
        render_manual_transaction(bank)
        render_pending_candidates(bank)
        return
    if scenario == "Confianza intermedia":
        render_controlled_demo(bank)
        render_pending_candidates(bank)
        return

    st.caption("Dataset de demostración → FILTRO REAL")
    st.html(
        """
        <div class="scenario-box">
            <div class="scenario-title">
                Escenario: detección desde el primer cobro
            </div>

            <div class="scenario-copy">
                Simula una transacción de un comercio que todavía
                no ha sido clasificado para este cliente.
                La operación será analizada por el filtro real.
            </div>
        </div>
        """
    )

    try:
        transactions = load_evaluation_transactions()

    except FileNotFoundError:

        st.error(
            "No se encontró evaluation_transactions.json."
        )
        return


    # --------------------------------------------------------
    # Evitar utilizar como "nuevo comercio" uno que ya sea una
    # suscripción activa o tenga confirmación pendiente.
    # --------------------------------------------------------

    blocked_merchant_ids = {
        subscription.merchant_id
        for subscription in bank.subscriptions
        if subscription.status.value == "ACTIVE"
    }

    blocked_merchant_names = {
        subscription.merchant.strip().upper()
        for subscription in bank.subscriptions
        if subscription.status.value == "ACTIVE"
    }

    blocked_merchant_ids.update(
        candidate.merchant_id
        for candidate in bank.subscription_candidates
        if (
            candidate.status
            == SubscriptionCandidateStatus.PENDING_CONFIRMATION
        )
    )

    blocked_merchant_names.update(
        candidate.merchant.strip().upper()
        for candidate in bank.subscription_candidates
        if (
            candidate.status
            == SubscriptionCandidateStatus.PENDING_CONFIRMATION
        )
    )

    available_transactions = [
        transaction
        for transaction in transactions
        if (
            transaction.get("merchant_id")
            not in blocked_merchant_ids
            and
            transaction.get(
                "merchant",
                "",
            ).strip().upper()
            not in blocked_merchant_names
            and
            (
                f"{transaction.get('customer_id', 'UNKNOWN')}"
                f"|{transaction.get('merchant_id', 'UNKNOWN')}"
            )
            not in bank.processed_demo_transactions
        )
    ]

    # --------------------------------------------------------
    # SELECTOR
    # --------------------------------------------------------

    transaction_options = {}

    for index, transaction in enumerate(
        available_transactions
    ):

        label = (
            f"{transaction.get('merchant', 'UNKNOWN')} · "
            f"{format_clp(float(transaction.get('amount', 0)))} · "
            f"MCC {transaction.get('mcc', '-')}"
        )

        # Evitar problemas si existieran labels repetidos.
        label = f"{label} · #{index + 1}"

        transaction_options[label] = transaction

    selected_label = st.selectbox(
        "Transacción de prueba",
        options=list(transaction_options.keys()),
        key="incoming-transaction-selector",
    )

    if not transaction_options:
        st.info("No quedan nuevas transacciones de demostración disponibles.")
        render_pending_candidates(bank)
        return

    raw_transaction = transaction_options[selected_label]

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    with st.container(border=True):

        col1, col2, col3 = st.columns(3)

        with col1:

            st.caption("Comercio")

            st.markdown(
                f"### {raw_transaction.get('merchant')}"
            )

        with col2:

            st.caption("Monto")

            st.markdown(
                f"### "
                f"{format_clp(float(raw_transaction.get('amount', 0)))}"
            )

        with col3:

            st.caption("Red")

            st.markdown(
                f"### {raw_transaction.get('network', '-')}"
            )

        st.caption(
            "Esta transacción todavía no ha sido clasificada "
            "por la aplicación."
        )

    # --------------------------------------------------------
    # INFORMACIÓN TÉCNICA
    # --------------------------------------------------------

    with st.expander(
        "Ver información recibida por el filtro"
    ):

        st.write(
            f"**Merchant ID:** "
            f"{raw_transaction.get('merchant_id')}"
        )

        st.write(
            f"**MCC:** "
            f"{raw_transaction.get('mcc')}"
        )

        st.write(
            f"**E-commerce:** "
            f"{raw_transaction.get('ecommerce')}"
        )

        st.write(
            f"**Stored credential:** "
            f"{raw_transaction.get('stored_credential')}"
        )

        st.write(
            f"**Cardholder present:** "
            f"{raw_transaction.get('cardholder_present')}"
        )

        st.caption(
            "La etiqueta true_type del dataset no se entrega "
            "al filtro y no participa en la detección."
        )

    # --------------------------------------------------------
    # PROCESAR
    # --------------------------------------------------------

    if st.button(
        "Procesar nueva transacción",
        type="primary",
        use_container_width=True,
        key="process-new-transaction",
    ):

        # Copia para no modificar el dataset cargado.
        transaction_for_filter = raw_transaction.copy()

        # true_type es únicamente ground truth del dataset.
        # El filtro NO puede utilizarlo.
        transaction_for_filter.pop(
            "true_type",
            None,
        )

        try:

            transaction, analysis = (
                process_incoming_transaction(
                    bank,
                    transaction_for_filter,
                )
            )

            st.divider()

            action = decide_subscription_action(analysis)

            if action == SubscriptionDetectionAction.AUTO_DETECTED:
                st.success(
                    f"Detectamos una nueva suscripción: {transaction.merchant} · "
                    f"{format_clp(transaction.amount)}"
                )

            elif not analysis.is_recurring:

                st.success(
                    "Transacción procesada como compra normal."
                )

                st.write(
                    f"El filtro clasificó el pago como "
                    f"**{analysis.recurring_type}**."
                )

            elif action == SubscriptionDetectionAction.NEEDS_CONFIRMATION:

                st.warning(
                    "Posible suscripción detectada"
                )

                st.write(
                    "Detectamos señales de que este comercio podría realizar "
                    "cobros periódicos."
                )

                st.write(
                    f"Confianza de recurrencia: "
                    f"**{format_confidence(analysis.recurrence_confidence)}**"
                )

                st.write(
                    f"Tipo estimado: "
                    f"**{analysis.recurring_type}**"
                )

            else:

                st.info(
                    "El filtro detectó un pago recurrente."
                )

                st.write(
                    f"Tipo detectado: "
                    f"**{analysis.recurring_type}**"
                )

            with st.expander(
                "Información del detector"
            ):

                st.write(
                    f"**Nivel de detección:** "
                    f"{analysis.detection_level}"
                )

                st.write(
                    f"**Confianza de recurrencia:** "
                    f"{format_confidence(analysis.recurrence_confidence)}"
                )

                st.write(
                    f"**Confianza del tipo:** "
                    f"{format_confidence(analysis.type_confidence)}"
                )

                if analysis.reasons:

                    st.markdown(
                        "**Razones de detección:**"
                    )

                    for reason in analysis.reasons:
                        st.write(f"- {reason}")

        except Exception as error:

            st.error(
                f"No fue posible procesar la transacción: "
                f"{error}"
            )

    render_pending_candidates(bank)


def render_controlled_demo(bank: BankState) -> None:
    st.info(DEMO_NOTICE)
    st.write(
        "Este caso utiliza una confianza intermedia simulada para probar qué ocurre "
        "cuando el sistema sospecha que un pago es una suscripción, pero no tiene "
        "confianza suficiente para clasificarlo automáticamente. "
        "El resultado no proviene del filtro real."
    )
    with st.container(border=True):
        st.markdown(f"### {DEMO_MERCHANT} · {format_clp(DEMO_AMOUNT)}")
        st.caption("El primer cobro se descontará una sola vez.")
    with st.expander("Información del detector"):
        analysis = intermediate_demo_analysis()
        st.caption("Análisis controlado para demostración")
        st.write(f"Confianza de recurrencia: {format_confidence(analysis.recurrence_confidence)}")
        st.write(f"Confianza del tipo: {format_confidence(analysis.type_confidence)}")
    processed = DEMO_TRANSACTION_KEY in bank.processed_demo_transactions
    if processed:
        st.caption("Este escenario ya fue procesado. Reinicia la demo para repetirlo.")
    if st.button(
        "Procesar escenario controlado",
        key="process-controlled-demo",
        type="primary",
        width="stretch",
        disabled=processed,
    ):
        try:
            process_intermediate_demo(bank)
        except ValueError as error:
            st.error(str(error))
        else:
            st.rerun()


def render_pending_candidates(bank: BankState) -> None:
    # ========================================================
    # CANDIDATOS PENDIENTES
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

        st.divider()

        st.subheader(
            "Suscripciones por confirmar"
        )

    for candidate in pending_candidates:

        transaction = bank.get_transaction_by_id(
            candidate.transaction_id
        )

        if transaction is None:
            continue

        with st.container(border=True):

            st.warning(
                "Posible suscripción detectada"
            )

            st.markdown(
                f"### {candidate.merchant}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.caption("Monto del primer cobro")

                st.write(
                    format_clp(
                        transaction.amount
                    )
                )

            with col2:
                st.caption("Tipo estimado")

                st.write(
                    candidate.detected_type
                )

            with col3:
                st.caption("Confianza")

                st.write(
                    format_confidence(
                        candidate.recurrence_confidence
                    )
                )

            with st.expander(
                "¿Por qué fue detectada?"
            ):

                for reason in candidate.reasons:
                    st.write(f"- {reason}")

            render_candidate_actions(bank, candidate, key_prefix="simulator")


# ============================================================
# MAIN SIMULATOR
# ============================================================

def render_simulator(bank: BankState) -> None:

    st.title("Simulador")

    st.caption(
        "Herramienta de demostración del sistema de protección."
    )

    st.html(
        """
        <div class="demo-banner">

            <span class="demo-badge">
                MODO DEMO
            </span>

            <div>
                <div class="demo-title">
                    Simulación de eventos bancarios
                </div>

                <div class="demo-copy">
                    Esta sección permite generar escenarios para
                    demostrar el funcionamiento del prototipo.
                    En una implementación real, estos eventos
                    llegarían automáticamente desde los sistemas
                    de pago del banco.
                </div>
            </div>

        </div>
        """
    )

    if "subscription_feedback" in st.session_state:

        st.success(
            st.session_state.pop(
                "subscription_feedback"
            )
        )

    known_tab, new_tab = st.tabs(
        [
            "Suscripción existente",
            "Primer cobro",
        ]
    )

    with known_tab:

        render_known_subscription_charge(
            bank
        )

    with new_tab:

        render_new_transaction(
            bank
        )
