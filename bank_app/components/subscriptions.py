import streamlit as st

from bank_app.app_models import TrustStatus
from bank_app.state.bank_state import BankState


def format_clp(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"${formatted}"


def format_confidence(value: float | None) -> str:
    if value is None:
        return "No disponible"

    return f"{value * 100:.1f}%"


def render_subscriptions(bank: BankState) -> None:
    st.title("Suscripciones")

    st.caption(
        "Administra tus pagos recurrentes y define cuáles son de confianza."
    )

    st.write("")

    if not bank.subscriptions:
        st.info("No hay suscripciones registradas.")
        return

    for subscription in bank.subscriptions:

        with st.container(border=True):

            # =================================================
            # RESUMEN PRINCIPAL
            # =================================================

            col1, col2, col3 = st.columns([2.5, 1, 1])

            with col1:
                st.markdown(
                    f"### {subscription.merchant}"
                )

                st.caption(
                    f"{subscription.recurring_type} · "
                    f"{subscription.frequency}"
                )

                st.write(
                    f"Último cobro: "
                    f"{subscription.last_charge_date.strftime('%d/%m/%Y')}"
                )

            with col2:
                st.caption("Precio actual")

                st.markdown(
                    f"### {format_clp(subscription.current_price)}"
                )

                st.caption(
                    f"/ {subscription.frequency.lower()}"
                )

            with col3:
                st.caption("Estado")

                if subscription.status.value == "ACTIVE":
                    st.success("Activa")
                else:
                    st.error("Cancelada")

            st.divider()

            # =================================================
            # TRUST STATUS
            # =================================================

            col_status, col_button = st.columns([2, 1])

            with col_status:
                st.caption("Nivel de confianza")

                if subscription.trust_status == TrustStatus.TRUSTED:

                    st.success("✓ De confianza")

                    st.caption(
                        "Esta suscripción tiene menor fricción "
                        "en sus cobros."
                    )

                else:

                    st.warning("⚠ Supervisada")

                    st.caption(
                        "Los cambios de precio serán revisados "
                        "antes de procesarse."
                    )

            with col_button:

                if subscription.trust_status == TrustStatus.TRUSTED:

                    if st.button(
                        "Marcar como supervisada",
                        key=f"untrust-{subscription.id}",
                        use_container_width=True,
                    ):
                        subscription.trust_status = TrustStatus.UNTRUSTED
                        st.rerun()

                else:

                    if st.button(
                        "Marcar como de confianza",
                        key=f"trust-{subscription.id}",
                        use_container_width=True,
                    ):
                        subscription.trust_status = TrustStatus.TRUSTED
                        st.rerun()

            # =================================================
            # DETALLE
            # =================================================

            with st.expander("Ver detalle"):

                detail1, detail2 = st.columns(2)

                with detail1:

                    st.markdown("#### Información de la suscripción")

                    st.write(
                        f"**Comercio:** {subscription.merchant}"
                    )

                    st.write(
                        f"**Precio actual:** "
                        f"{format_clp(subscription.current_price)}"
                    )

                    st.write(
                        f"**Frecuencia estimada:** "
                        f"{subscription.frequency}"
                    )

                    st.write(
                        f"**Último cobro:** "
                        f"{subscription.last_charge_date.strftime('%d/%m/%Y')}"
                    )

                    st.write(
                        f"**Tipo detectado:** "
                        f"{subscription.recurring_type}"
                    )

                    st.write(
                        f"**Estado:** "
                        f"{subscription.status.value}"
                    )

                    st.write(
                        f"**Confianza:** "
                        f"{subscription.trust_status.value}"
                    )

                with detail2:

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

                        st.markdown("**Razones de detección:**")

                        for reason in subscription.detection_reasons:
                            st.write(f"- {reason}")

                    else:

                        st.caption(
                            "No hay razones detalladas disponibles "
                            "para este registro de demostración."
                        )

                st.divider()

                st.markdown("#### Historial asociado")

                if subscription.transaction_history:

                    for transaction_id in subscription.transaction_history:

                        transaction = bank.get_transaction_by_id(
                            transaction_id
                        )

                        if transaction is None:
                            continue

                        col_date, col_amount = st.columns([2, 1])

                        with col_date:
                            st.write(
                                transaction.date.strftime(
                                    "%d/%m/%Y"
                                )
                            )

                        with col_amount:
                            st.write(
                                format_clp(transaction.amount)
                            )

                else:

                    st.caption(
                        "No hay cobros registrados en el historial."
                    )
                st.divider()

                st.markdown("#### Gestión")

                if subscription.status.value == "ACTIVE":

                    st.warning(
                        "Cancelar esta suscripción cambiará su estado "
                        "dentro del gemelo digital."
                    )

                    confirm_cancel = st.checkbox(
                        "Confirmo que quiero cancelar esta suscripción",
                        key=f"confirm-cancel-{subscription.id}",
                    )

                    if st.button(
                        "Cancelar suscripción",
                        key=f"cancel-{subscription.id}",
                        use_container_width=True,
                        disabled=not confirm_cancel,
                    ):
                        from bank_app.app_models import SubscriptionStatus

                        subscription.status = SubscriptionStatus.CANCELLED

                        st.rerun()

                else:

                    st.error("Esta suscripción está cancelada.")

                    st.caption(
                        "En una implementación real, la cancelación "
                        "requeriría integración con el comercio, "
                        "proveedor o red de pagos."
                    )