from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bank_app.app_models import SubscriptionCandidate, Transaction
from bank_app.state.bank_state import BankState
from bank_app.services.filter_adapter import FilterAnalysis


APP = Path(__file__).resolve().parents[1] / "bank_app" / "app.py"
LABELS = ["Sí, es una suscripción", "No estoy seguro", "No es una suscripción"]


@pytest.mark.parametrize("page", ["Suscripciones", "Simulador"])
@pytest.mark.parametrize("choice,status,verify", [
    (0, "CONFIRMED", False), (1, "UNSURE_BY_USER", True),
    (2, "REJECTED_BY_USER", None),
])
def test_candidate_responses_on_both_pages(page, choice, status, verify):
    bank = BankState(balance=100000)
    bank.add_transaction(Transaction("tx-test", "Test Service", "test", 5290, datetime.now()))
    bank.add_subscription_candidate(SubscriptionCandidate(
        "candidate-test", "tx-test", "Test Service", "test", "SUBSCRIPTION", .82, .68,
    ))
    app = AppTest.from_file(str(APP), default_timeout=10)
    app.session_state["bank_state"] = bank
    app.session_state["selected_page"] = page
    app.run()
    assert not app.exception
    assert [b.label for b in app.button if b.label in LABELS] == LABELS
    next(b for b in app.button if b.label == LABELS[choice]).click().run()
    assert not app.exception
    assert bank.subscription_candidates[0].status.value == status
    assert bank.balance == 100000
    assert not [b for b in app.button if b.label in LABELS]
    if verify is None:
        assert not bank.subscriptions
    else:
        assert bank.subscriptions[0].needs_user_verification is verify
    if verify:
        app.session_state["selected_page"] = "Suscripciones"
        app.run()
        assert not app.exception
        assert "Por verificar" in [c.value for c in app.caption]


def test_real_spotify_notification_without_question():
    bank = BankState()
    app = AppTest.from_file(str(APP), default_timeout=10)
    app.session_state["bank_state"] = bank
    app.session_state["selected_page"] = "Simulador"
    app.run()
    assert not app.exception
    selector = app.selectbox(key="incoming-transaction-selector")
    selector.select(next(option for option in selector.options if "SPOTIFY" in option)).run()
    app.button(key="process-new-transaction").click().run()
    assert not app.exception
    assert not app.error
    assert "Detectamos una nueva suscripción: SPOTIFY · $5.290" in [s.value for s in app.success]
    assert len(bank.subscriptions) == 1
    assert not bank.subscription_candidates
    assert not [b for b in app.button if b.label in LABELS]
    app.run()
    assert not app.exception
    assert not any("Detectamos una nueva suscripción" in s.value for s in app.success)


def test_medium_confidence_shows_uncertainty_and_three_choices(monkeypatch):
    monkeypatch.setattr(
        "bank_app.services.incoming_transaction_service.analyze_bank_transaction",
        lambda raw: FilterAnalysis(True, "SUBSCRIPTION", .82, .68, "TEST", True, None, []),
    )
    app = AppTest.from_file(str(APP), default_timeout=10)
    app.session_state["bank_state"] = BankState()
    app.session_state["selected_page"] = "Simulador"
    app.run()
    app.button(key="process-new-transaction").click().run()
    assert not app.exception
    assert not app.error
    assert "Posible suscripción detectada" in [w.value for w in app.warning]
    assert not any("Detectamos una nueva suscripción" in s.value for s in app.success)
    assert [b.label for b in app.button if b.label in LABELS] == LABELS


def test_pending_candidate_remains_actionable_without_available_demo_transactions(monkeypatch):
    monkeypatch.setattr("bank_app.components.simulator.load_evaluation_transactions", lambda: [])
    bank = BankState()
    bank.add_transaction(Transaction("tx-test", "Test Service", "test", 5290, datetime.now()))
    bank.add_subscription_candidate(SubscriptionCandidate(
        "candidate-test", "tx-test", "Test Service", "test", "SUBSCRIPTION", .82, .68,
    ))
    app = AppTest.from_file(str(APP), default_timeout=10)
    app.session_state["bank_state"] = bank
    app.session_state["selected_page"] = "Simulador"
    app.run()
    assert not app.exception
    assert [b.label for b in app.button if b.label in LABELS] == LABELS
    next(b for b in app.button if b.label == "No estoy seguro").click().run()
    assert not app.exception
    assert bank.subscriptions[0].needs_user_verification
