"""Manual first charge UI, using the same incoming service as dataset charges."""

import re

import streamlit as st

from bank_app.services.incoming_transaction_service import process_incoming_transaction
from bank_app.services.manual_transaction_service import (
    CIT_MIT_INDICATORS, NETWORKS, POS_ENVIRONMENTS, build_manual_transaction,
)
from bank_app.services.subscription_detection_policy import (
    SubscriptionDetectionAction, decide_subscription_action,
)
from bank_app.state.bank_state import BankState


RESULT_KEY = "manual_charge_result"


def optional_label(value):
    if value is None:
        return "No informado"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    return value


TYPE_LABELS = {
    "SUBSCRIPTION": "Suscripción",
    "NON_RECURRING": "No recurrente",
    "RECURRING_BILL": "Cobro recurrente",
    "UNKNOWN_RECURRING": "Cobro recurrente de tipo desconocido",
}
LEVEL_LABELS = {
    "INSUFFICIENT_EVIDENCE": "Evidencia insuficiente",
    "MERCHANT_MODEL+TYPE_ENGINE": "Modelo histórico + análisis de tipo",
    "MERCHANT_MODEL": "Modelo histórico",
    "NETWORK_EXPLICIT": "Señal explícita de la red",
    "AUTHENTICATION_DATA": "Datos de autenticación",
    "HEURISTIC": "Análisis de señales",
    "HEURISTIC+TYPE_ENGINE": "Análisis de señales + análisis de tipo",
}


def friendly_reason(reason: str) -> str:
    """Translate only known filter messages, preserving unfamiliar evidence."""
    exact = {
        "E-commerce transaction": "Transacción de comercio electrónico",
        "Stored credential": "Tarjeta guardada en el comercio",
        "Card-not-present transaction": "Transacción sin presencia del titular",
    }
    if reason in exact:
        return exact[reason]
    for source, label in (
        ("Merchant historical model", "Modelo histórico del comercio"),
        ("Repeat customer rate", "Tasa de clientes recurrentes"),
        ("Recurring interval regularity", "Regularidad de los intervalos"),
        ("Amount similarity", "Similitud del monto"),
    ):
        match = re.fullmatch(re.escape(source) + r": ([0-9]+(?:\.[0-9]+)?)%", reason)
        if match:
            return f"{label}: {float(match[1]):.2f}%"
    match = re.fullmatch(r"Merchant customers observed: ([0-9]+)", reason)
    if match:
        return f"Clientes observados: {match[1]}"
    match = re.fullmatch(r"MCC ([0-9]{4}) is subscription/membership-oriented", reason)
    if match:
        return f"MCC {match[1]} asociado a suscripciones o membresías"
    return reason


def render_detector_information(analysis, raw: dict) -> None:
    with st.expander("Información del detector"):
        rows = (
            ("¿Es un cobro recurrente?", optional_label(analysis.is_recurring)),
            ("Tipo detectado", TYPE_LABELS.get(analysis.recurring_type, analysis.recurring_type)),
            ("Confianza de recurrencia", f"{analysis.recurrence_confidence:.2%}"),
            ("Confianza del tipo", f"{analysis.type_confidence:.2%}"),
            ("Nivel de detección", LEVEL_LABELS.get(analysis.detection_level, analysis.detection_level)),
        )
        for label, value in rows:
            st.markdown(f"**{label}:** {value}")
        if analysis.reasons:
            st.markdown("**Motivos considerados:**")
            for reason in analysis.reasons:
                st.write(f"• {friendly_reason(reason)}")
        with st.expander("Ver datos técnicos", expanded=False):
            st.json({name: getattr(analysis, name) for name in (
                "is_recurring", "recurring_type", "recurrence_confidence",
                "type_confidence", "detection_level", "reasons",
            )})
            st.caption("Identificadores enviados al filtro")
            st.write({name: raw[name] for name in ("customer_id", "merchant_id")})


def render_manual_transaction(bank: BankState) -> None:
    st.subheader("Crear cobro manual")
    st.caption("Cobro manual → FILTRO REAL")
    result = st.session_state.get(RESULT_KEY)
    # Resetting the bank invalidates the previous receipt as well.
    if result and bank.get_transaction_by_id(result[0].id) is None:
        del st.session_state[RESULT_KEY]
        result = None

    if result is None:
        with st.form("manual-charge-form"):
            merchant = st.text_input("Comercio", placeholder="SPOTIFY", key="manual-merchant")
            amount = st.number_input("Monto del cobro", min_value=1, value=5290, step=1,
                                     help="Monto entero en CLP.", key="manual-amount")
            mcc = st.text_input("Código de categoría del comercio (MCC)", max_chars=4,
                               help="Cuatro dígitos que identifican el tipo de comercio.", key="manual-mcc")
            network = st.selectbox("Red", NETWORKS, key="manual-network")
            ecommerce = st.selectbox("Compra online", (True, False), format_func=optional_label,
                                    key="manual-ecommerce")
            stored = st.selectbox("¿La tarjeta estaba guardada en el comercio?", (True, False),
                                 format_func=optional_label, key="manual-stored")
            st.caption("Credencial almacenada (COF)")
            with st.expander("Información avanzada", expanded=False):
                merchant_id = st.text_input("merchant_id", key="manual-merchant-id",
                    help="Vacío: ID nuevo. SPOTIFY001 permite consultar su historial real; el nombre no asigna el ID.")
                customer_id = st.text_input("customer_id", key="manual-customer-id",
                    help="Vacío: ID único automático para este nuevo cobro.")
                present = st.selectbox("Titular presente (cardholder_present)", (None, True, False),
                                      format_func=optional_label, key="manual-present")
                indicator = st.selectbox("Indicador Mastercard (cit_mit_indicator)", CIT_MIT_INDICATORS,
                                         format_func=optional_label, key="manual-indicator")
                pos = st.selectbox("Entorno Visa (pos_environment)", POS_ENVIRONMENTS,
                                   format_func=optional_label, key="manual-pos")
                recurring = st.selectbox("Recurrencia 3DS (three_ds_recurring)", (None, True, False),
                                         format_func=optional_label, key="manual-3ds")
                st.caption("Moneda: CLP. Las señales se interpretan según la red y el filtro existente.")
            submitted = st.form_submit_button("Procesar cobro", type="primary", key="process-manual-charge")
            st.caption("Este cobro será analizado por el filtro real de CONDOR.")
        if submitted:
            try:
                raw = build_manual_transaction(
                    merchant=merchant, amount=amount, mcc=mcc, network=network,
                    ecommerce=ecommerce, stored_credential=stored,
                    merchant_id=merchant_id, customer_id=customer_id,
                    cardholder_present=present, cit_mit_indicator=indicator,
                    pos_environment=pos, three_ds_recurring=recurring,
                )
                transaction, analysis = process_incoming_transaction(bank, raw)
            except ValueError as error:
                st.error(str(error))
            except (OSError, TypeError) as error:
                st.error(f"No fue posible analizar el cobro: {error}")
            else:
                st.session_state[RESULT_KEY] = (transaction, analysis, raw)
                st.rerun()
        return

    transaction, analysis, raw = result
    st.success("Analizado por el filtro real")
    st.write(f"{transaction.merchant} · ${transaction.amount:,.0f} CLP".replace(",", "."))
    action = decide_subscription_action(analysis)
    if action == SubscriptionDetectionAction.AUTO_DETECTED:
        st.success(f"Detectamos una nueva suscripción: {transaction.merchant} · "
                   f"${transaction.amount:,.0f}".replace(",", "."))
    elif action == SubscriptionDetectionAction.NEEDS_CONFIRMATION:
        st.info("El cobro fue registrado. Revisa la posible suscripción en el flujo de confirmación.")
    elif not analysis.is_recurring:
        st.success("El filtro no encontró evidencia suficiente para clasificar este cobro como recurrente.")
    else:
        st.info("El filtro detectó un pago recurrente. El movimiento fue registrado.")
    render_detector_information(analysis, raw)
    # A deliberate new draft is required; reruns/double clicks cannot debit again.
    if st.button("Crear otro cobro manual", key="new-manual-charge"):
        del st.session_state[RESULT_KEY]
        st.rerun()
