from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from bank_app.data.demo_data import seed_demo_data
from bank_app.services import incoming_transaction_service as incoming
from bank_app.services.controlled_demo_service import (
    DEMO_AMOUNT, DEMO_MERCHANT, DEMO_MERCHANT_ID, DEMO_NOTICE,
    DEMO_TRANSACTION_KEY, intermediate_demo_analysis, process_intermediate_demo,
)
from bank_app.services.subscription_detection_policy import decide_subscription_action
from bank_app.services.subscription_service import (
    confirm_subscription_candidate, mark_subscription_candidate_unsure,
    reject_subscription_candidate,
)
from bank_app.services.transaction_service import simulate_subscription_charge
from bank_app.state.bank_state import BankState


APP = Path(__file__).resolve().parents[1] / "bank_app" / "app.py"
LABELS = ["Sí, es una suscripción", "No estoy seguro", "No es una suscripción"]


def test_controlled_analysis_uses_real_policy():
    analysis = intermediate_demo_analysis()
    assert analysis.is_recurring
    assert analysis.recurring_type == "SUBSCRIPTION"
    assert (analysis.recurrence_confidence, analysis.type_confidence) == (.82, .68)
    assert decide_subscription_action(analysis).value == "NEEDS_CONFIRMATION"
    assert analysis.detection_level == "DEMO_CONTROLLED"
    assert DEMO_NOTICE in analysis.reasons[0]


def test_controlled_charge_without_filter_and_without_duplicate_debit(monkeypatch):
    real_filter = Mock(side_effect=AssertionError("El escenario no debe llamar al filtro"))
    monkeypatch.setattr(incoming, "analyze_bank_transaction", real_filter)
    bank = BankState()
    initial_balance = bank.balance
    transaction, analysis = process_intermediate_demo(bank)
    assert bank.transactions == [transaction]
    assert transaction.status.value == "COMPLETED"
    assert transaction.merchant_id == DEMO_MERCHANT_ID
    assert bank.balance == initial_balance - DEMO_AMOUNT
    assert bank.processed_demo_transactions == {DEMO_TRANSACTION_KEY}
    candidate, = bank.subscription_candidates
    assert candidate.transaction_id == transaction.id
    assert candidate.status.value == "PENDING_CONFIRMATION"
    assert candidate.reasons == analysis.reasons
    assert not bank.subscriptions
    with pytest.raises(ValueError, match="ya fue procesada"):
        process_intermediate_demo(bank)
    assert bank.balance == initial_balance - DEMO_AMOUNT
    assert len(bank.transactions) == len(bank.subscription_candidates) == 1
    real_filter.assert_not_called()


@pytest.mark.parametrize("resolve,status,verify", [
    (confirm_subscription_candidate, "CONFIRMED", False),
    (mark_subscription_candidate_unsure, "UNSURE_BY_USER", True),
    (reject_subscription_candidate, "REJECTED_BY_USER", None),
])
def test_controlled_candidate_reuses_existing_responses(resolve, status, verify):
    bank = BankState()
    transaction, _ = process_intermediate_demo(bank)
    balance = bank.balance
    candidate, = bank.subscription_candidates
    resolve(bank, candidate.id)
    assert candidate.status.value == status
    assert bank.balance == balance
    if verify is None:
        assert not bank.subscriptions
    else:
        subscription, = bank.subscriptions
        assert subscription.status.value == "ACTIVE"
        assert subscription.trust_status.value == "UNTRUSTED"
        assert subscription.needs_user_verification is verify
        assert subscription.current_price == DEMO_AMOUNT
        assert subscription.transaction_history == [transaction.id]
    with pytest.raises(ValueError, match="ya fue procesada"):
        process_intermediate_demo(bank)
    assert bank.balance == balance


def test_unsure_price_increase_uses_existing_protection():
    bank = BankState()
    process_intermediate_demo(bank)
    subscription = mark_subscription_candidate_unsure(bank, bank.subscription_candidates[0].id)
    balance = bank.balance
    transaction = simulate_subscription_charge(bank, subscription.id, 29990)
    assert transaction.status.value == "PENDING_APPROVAL"
    assert bank.balance == balance
    assert subscription.current_price == DEMO_AMOUNT
    authorization, = bank.pending_authorizations
    assert authorization.transaction_id == transaction.id
    assert authorization.subscription_id == subscription.id
    assert authorization.status.value == "PENDING"


def simulator_app():
    app = AppTest.from_file(str(APP), default_timeout=10)
    app.session_state["bank_state"] = BankState()
    app.session_state["selected_page"] = "Simulador"
    app.run()
    assert not app.exception
    return app


@pytest.mark.parametrize("choice,status", list(enumerate([
    "CONFIRMED", "UNSURE_BY_USER", "REJECTED_BY_USER",
])))
def test_controlled_scenario_visible_and_actionable(choice, status):
    app = simulator_app()
    assert DEMO_NOTICE not in [i.value for i in app.info]
    app.segmented_control(key="first-charge-scenario").set_value("Confianza intermedia").run()
    assert not app.exception
    assert DEMO_NOTICE in [i.value for i in app.info]
    assert not [s for s in app.selectbox if s.key == "incoming-transaction-selector"]
    app.button(key="process-controlled-demo").click().run()
    assert not app.exception
    assert not app.error
    assert "Posible suscripción detectada" in [w.value for w in app.warning]
    assert [b.label for b in app.button if b.label in LABELS] == LABELS
    assert app.button(key="process-controlled-demo").disabled
    bank = app.session_state["bank_state"]
    balance = bank.balance
    next(b for b in app.button if b.label == LABELS[choice]).click().run()
    assert not app.exception
    assert bank.subscription_candidates[0].status.value == status
    assert bank.balance == balance
    assert app.button(key="process-controlled-demo").disabled
    assert not [b for b in app.button if b.label in LABELS]


def test_ui_unsure_increase_and_reset():
    app = simulator_app()
    app.segmented_control(key="first-charge-scenario").set_value("Confianza intermedia").run()
    app.button(key="process-controlled-demo").click().run()
    next(b for b in app.button if b.label == "No estoy seguro").click().run()
    assert not app.exception
    bank = app.session_state["bank_state"]
    subscription, = bank.subscriptions
    app.selectbox(key="known-subscription-selector").select(DEMO_MERCHANT).run()
    app.number_input(key=f"amount-{subscription.id}").set_value(29990).run()
    balance = bank.balance
    app.button(key="simulate-known-charge").click().run()
    assert not app.exception
    assert bank.transactions[-1].status.value == "PENDING_APPROVAL"
    assert bank.balance == balance
    assert bank.pending_authorizations
    app.session_state["selected_page"] = "Suscripciones"
    app.run()
    assert "Por verificar" in [c.value for c in app.caption]
    app.button(key="reset-demo").click().run()
    assert not app.exception
    reset = app.session_state["bank_state"]
    expected = BankState()
    seed_demo_data(expected)
    assert reset == expected
    assert not reset.processed_demo_transactions
    process_intermediate_demo(reset)
    assert reset.balance == expected.balance - DEMO_AMOUNT


def test_normal_spotify_still_calls_real_filter(monkeypatch):
    real_filter = Mock(wraps=incoming.analyze_bank_transaction)
    monkeypatch.setattr(incoming, "analyze_bank_transaction", real_filter)
    app = simulator_app()
    selector = app.selectbox(key="incoming-transaction-selector")
    selector.select(next(o for o in selector.options if "SPOTIFY" in o)).run()
    app.button(key="process-new-transaction").click().run()
    assert not app.exception
    real_filter.assert_called_once()
    bank = app.session_state["bank_state"]
    subscription, = bank.subscriptions
    assert subscription.merchant == "SPOTIFY"
    assert not bank.subscription_candidates
    assert not [b for b in app.button if b.label in LABELS]
    assert DEMO_NOTICE not in [i.value for i in app.info]
    assert any("Detectamos una nueva suscripción: SPOTIFY" in s.value for s in app.success)
