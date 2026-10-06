import json

import pytest

from bank_app.app_models import (
    AuthorizationStatus,
    SubscriptionCandidateStatus,
    SubscriptionStatus,
    TransactionStatus,
    TrustStatus,
)
from bank_app.data.demo_data import seed_demo_data
from bank_app.services.authorization_service import (
    approve_authorization,
    reject_authorization,
)
from bank_app.services.incoming_transaction_service import (
    process_incoming_transaction,
)
from bank_app.services.filter_adapter import FilterAnalysis
from bank_app.services.subscription_service import (
    confirm_subscription_candidate,
    reject_subscription_candidate,
    mark_subscription_candidate_unsure,
)
from bank_app.services.transaction_service import (
    simulate_subscription_charge,
)
from bank_app.state.bank_state import BankState


def create_demo_bank() -> BankState:
    bank = BankState()
    seed_demo_data(bank)
    return bank


# ============================================================
# 1. UNTRUSTED + PRICE INCREASE -> PENDING
# ============================================================

def test_untrusted_price_increase_is_held_before_payment():
    bank = create_demo_bank()

    spotify = bank.get_subscription_by_id("sub-spotify")

    initial_balance = bank.balance
    initial_price = spotify.current_price

    transaction = simulate_subscription_charge(
        bank=bank,
        subscription_id="sub-spotify",
        attempted_amount=6490,
    )

    assert transaction.status == TransactionStatus.PENDING_APPROVAL

    assert bank.balance == initial_balance
    assert spotify.current_price == initial_price

    assert len(bank.pending_authorizations) == 1

    authorization = bank.pending_authorizations[0]

    assert authorization.status == AuthorizationStatus.PENDING
    assert authorization.previous_amount == 5290
    assert authorization.attempted_amount == 6490


# ============================================================
# 2. REJECT -> NO MONEY MOVES
# ============================================================

def test_rejected_price_increase_does_not_charge_user():
    bank = create_demo_bank()

    spotify = bank.get_subscription_by_id("sub-spotify")

    initial_balance = bank.balance

    transaction = simulate_subscription_charge(
        bank=bank,
        subscription_id="sub-spotify",
        attempted_amount=6490,
    )

    authorization = bank.pending_authorizations[0]

    reject_authorization(
        bank,
        authorization.id,
    )

    assert authorization.status == AuthorizationStatus.REJECTED
    assert transaction.status == TransactionStatus.REJECTED

    assert bank.balance == initial_balance
    assert spotify.current_price == 5290


# ============================================================
# 3. APPROVE -> CHARGE + UPDATE PRICE
# ============================================================

def test_approved_price_increase_charges_and_updates_price():
    bank = create_demo_bank()

    spotify = bank.get_subscription_by_id("sub-spotify")

    initial_balance = bank.balance

    transaction = simulate_subscription_charge(
        bank=bank,
        subscription_id="sub-spotify",
        attempted_amount=6490,
    )

    authorization = bank.pending_authorizations[0]

    approve_authorization(
        bank,
        authorization.id,
    )

    assert authorization.status == AuthorizationStatus.APPROVED
    assert transaction.status == TransactionStatus.APPROVED

    assert bank.balance == initial_balance - 6490
    assert spotify.current_price == 6490

    assert transaction.id in spotify.transaction_history


# ============================================================
# 4. TRUSTED -> LOWER FRICTION
# ============================================================

def test_trusted_subscription_price_increase_is_processed():
    bank = create_demo_bank()

    netflix = bank.get_subscription_by_id("sub-netflix")

    assert netflix.trust_status == TrustStatus.TRUSTED

    initial_balance = bank.balance

    transaction = simulate_subscription_charge(
        bank=bank,
        subscription_id="sub-netflix",
        attempted_amount=11990,
    )

    assert transaction.status == TransactionStatus.COMPLETED

    assert bank.balance == initial_balance - 11990
    assert netflix.current_price == 11990

    assert len(bank.pending_authorizations) == 0


# ============================================================
# 5. CANCELLED CANNOT BE CHARGED
# ============================================================

def test_cancelled_subscription_cannot_be_charged():
    bank = create_demo_bank()

    spotify = bank.get_subscription_by_id("sub-spotify")

    spotify.status = SubscriptionStatus.CANCELLED

    initial_balance = bank.balance

    with pytest.raises(
        ValueError,
        match="Cannot charge a cancelled subscription",
    ):
        simulate_subscription_charge(
            bank=bank,
            subscription_id="sub-spotify",
            attempted_amount=6490,
        )

    assert bank.balance == initial_balance


# ============================================================
# 6. AUTHORIZATION CANNOT BE RESOLVED TWICE
# ============================================================

def test_authorization_cannot_be_approved_twice():
    bank = create_demo_bank()

    simulate_subscription_charge(
        bank=bank,
        subscription_id="sub-spotify",
        attempted_amount=6490,
    )

    authorization = bank.pending_authorizations[0]

    approve_authorization(
        bank,
        authorization.id,
    )

    with pytest.raises(
        ValueError,
        match="Authorization has already been resolved",
    ):
        approve_authorization(
            bank,
            authorization.id,
        )


# ============================================================
# 7. FULL FLOW USING REAL FILTER
# ============================================================

def test_full_new_subscription_protection_flow():
    bank = BankState()
    initial_balance = bank.balance

    with open(
        "evaluation_transactions.json",
        "r",
        encoding="utf-8",
    ) as file:
        evaluation_transactions = json.load(file)

    spotify_raw = next(
        transaction
        for transaction in evaluation_transactions
        if transaction["merchant"] == "SPOTIFY"
    ).copy()

    # Ground truth del dataset.
    # No puede llegar al filtro.
    spotify_raw.pop("true_type", None)

    # --------------------------------------------------------
    # PRIMER COBRO
    # --------------------------------------------------------

    first_transaction, analysis = process_incoming_transaction(
        bank,
        spotify_raw,
    )

    assert analysis.is_recurring is True
    assert analysis.recurring_type == "SUBSCRIPTION"

    assert first_transaction.status == TransactionStatus.COMPLETED
    assert len(bank.transactions) == 1
    assert bank.balance == initial_balance - first_transaction.amount
    assert bank.subscription_candidates == []
    assert len(bank.subscriptions) == 1

    balance_after_first_charge = bank.balance

    # --------------------------------------------------------
    # REGISTRO AUTOMÁTICO, SIN CONFIRMACIÓN
    # --------------------------------------------------------

    subscription = bank.subscriptions[0]

    assert subscription.needs_user_verification is False
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.trust_status == TrustStatus.UNTRUSTED
    assert subscription.current_price == 5290

    assert subscription.last_charge_date == first_transaction.date
    assert subscription.recurrence_confidence == analysis.recurrence_confidence
    assert subscription.type_confidence == analysis.type_confidence
    assert subscription.detection_reasons == analysis.reasons
    assert subscription.detection_reasons is not analysis.reasons
    assert subscription.transaction_history == [first_transaction.id]

    # --------------------------------------------------------
    # COBRO POSTERIOR CON AUMENTO
    # --------------------------------------------------------

    second_transaction = simulate_subscription_charge(
        bank=bank,
        subscription_id=subscription.id,
        attempted_amount=6490,
    )

    assert (
        second_transaction.status
        == TransactionStatus.PENDING_APPROVAL
    )

    # Requisito central:
    # el dinero todavía NO se mueve.
    assert bank.balance == balance_after_first_charge

    # Tampoco aceptamos el nuevo precio aún.
    assert subscription.current_price == 5290

@pytest.fixture
def controlled_analysis(monkeypatch):
    """Controla solo la salida del adaptador; no altera datasets ni el filtro."""
    analysis = FilterAnalysis(
        is_recurring=True,
        recurring_type="SUBSCRIPTION",
        recurrence_confidence=0.82,
        type_confidence=0.68,
        detection_level="TEST",
        needs_user_confirmation=True,
        merchant_recurring_probability=None,
        reasons=["Señales de recurrencia para la prueba"],
    )
    monkeypatch.setattr(
        "bank_app.services.incoming_transaction_service.analyze_bank_transaction",
        lambda raw: analysis,
    )
    return analysis


def incoming_raw(**overrides):
    return {
        "customer_id": "customer-test",
        "merchant_id": "merchant-test",
        "merchant": "Test Service",
        "amount": 5290,
        **overrides,
    }


def test_medium_confidence_candidate_can_still_be_confirmed(controlled_analysis):
    bank = BankState()
    initial_balance = bank.balance
    transaction, analysis = process_incoming_transaction(bank, incoming_raw())

    assert analysis is controlled_analysis
    assert transaction.status == TransactionStatus.COMPLETED
    assert bank.balance == initial_balance - transaction.amount
    assert bank.subscriptions == []
    assert len(bank.subscription_candidates) == 1
    candidate = bank.subscription_candidates[0]
    assert candidate.status == SubscriptionCandidateStatus.PENDING_CONFIRMATION
    assert candidate.transaction_id == transaction.id
    assert candidate.recurrence_confidence == analysis.recurrence_confidence
    assert candidate.type_confidence == analysis.type_confidence
    assert candidate.reasons == analysis.reasons

    subscription = confirm_subscription_candidate(bank, candidate.id)

    assert candidate.status == SubscriptionCandidateStatus.CONFIRMED
    assert subscription.needs_user_verification is False
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.trust_status == TrustStatus.UNTRUSTED
    assert subscription.current_price == transaction.amount
    assert subscription.last_charge_date == transaction.date
    assert subscription.transaction_history == [transaction.id]
    assert subscription.detection_reasons == candidate.reasons
    assert bank.balance == initial_balance - transaction.amount
    with pytest.raises(ValueError, match="already been resolved"):
        confirm_subscription_candidate(bank, candidate.id)
    assert len(bank.subscriptions) == 1


def test_medium_confidence_candidate_can_still_be_rejected(controlled_analysis):
    bank = BankState()
    process_incoming_transaction(bank, incoming_raw())
    balance_after_charge = bank.balance
    candidate = bank.subscription_candidates[0]

    reject_subscription_candidate(bank, candidate.id)

    assert candidate.status == SubscriptionCandidateStatus.REJECTED_BY_USER
    assert bank.subscriptions == []
    assert bank.balance == balance_after_charge


@pytest.mark.parametrize(
    "is_recurring,recurring_type",
    [(False, "NON_RECURRING"), (True, "RECURRING_BILL"), (True, "UNKNOWN_RECURRING")],
)
def test_none_action_only_processes_payment(
    controlled_analysis, is_recurring, recurring_type
):
    controlled_analysis.is_recurring = is_recurring
    controlled_analysis.recurring_type = recurring_type
    bank = BankState()
    initial_balance = bank.balance

    transaction, _ = process_incoming_transaction(bank, incoming_raw())

    assert transaction.status == TransactionStatus.COMPLETED
    assert bank.transactions == [transaction]
    assert bank.balance == initial_balance - transaction.amount
    assert bank.subscriptions == []
    assert bank.subscription_candidates == []


@pytest.mark.parametrize(
    "merchant_id,merchant",
    [("merchant-test", "Different Name"), ("different-id", "  tEsT sErViCe  ")],
)
def test_auto_detection_does_not_duplicate_active_subscription(
    controlled_analysis, merchant_id, merchant
):
    controlled_analysis.recurrence_confidence = 0.9855
    controlled_analysis.type_confidence = 0.85
    bank = BankState()
    initial_balance = bank.balance
    first, _ = process_incoming_transaction(bank, incoming_raw())
    subscription = bank.subscriptions[0]

    second, _ = process_incoming_transaction(
        bank,
        incoming_raw(customer_id="another-customer", merchant_id=merchant_id, merchant=merchant),
    )

    assert bank.subscriptions == [subscription]
    assert bank.subscription_candidates == []
    assert bank.balance == initial_balance - first.amount - second.amount
    assert subscription.transaction_history == [first.id]


def test_repeated_demo_transaction_does_not_charge_twice(controlled_analysis):
    controlled_analysis.recurrence_confidence = 0.9855
    controlled_analysis.type_confidence = 0.85
    bank = BankState()
    process_incoming_transaction(bank, incoming_raw())
    balance_after_charge = bank.balance

    with pytest.raises(ValueError, match="ya fue procesada"):
        process_incoming_transaction(bank, incoming_raw())

    assert bank.balance == balance_after_charge
    assert len(bank.transactions) == 1
    assert len(bank.subscriptions) == 1


def test_manual_confirmation_still_rejects_duplicate_subscription(controlled_analysis):
    bank = BankState()
    process_incoming_transaction(bank, incoming_raw())
    candidate = bank.subscription_candidates[0]
    controlled_analysis.recurrence_confidence = 0.9855
    controlled_analysis.type_confidence = 0.85
    process_incoming_transaction(bank, incoming_raw(customer_id="another-customer"))
    balance_after_charges = bank.balance

    with pytest.raises(ValueError, match="already registered"):
        confirm_subscription_candidate(bank, candidate.id)

    assert len(bank.subscriptions) == 1
    assert candidate.status == SubscriptionCandidateStatus.PENDING_CONFIRMATION
    assert bank.balance == balance_after_charges



def test_unsure_creates_supervised_subscription_and_holds_increase(controlled_analysis):
    bank = BankState()
    initial_balance = bank.balance
    transaction, analysis = process_incoming_transaction(bank, incoming_raw())
    candidate = bank.subscription_candidates[0]
    subscription = mark_subscription_candidate_unsure(bank, candidate.id)

    assert candidate.status == SubscriptionCandidateStatus.UNSURE_BY_USER
    assert subscription.needs_user_verification is True
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.trust_status == TrustStatus.UNTRUSTED
    assert subscription.current_price == transaction.amount
    assert subscription.last_charge_date == transaction.date
    assert subscription.transaction_history == [transaction.id]
    assert subscription.recurrence_confidence == analysis.recurrence_confidence
    assert subscription.type_confidence == analysis.type_confidence
    assert subscription.detection_reasons == analysis.reasons
    assert bank.balance == initial_balance - transaction.amount

    charge = simulate_subscription_charge(bank, subscription.id, 6490)
    assert charge.status == TransactionStatus.PENDING_APPROVAL
    assert bank.balance == initial_balance - transaction.amount
    assert subscription.current_price == transaction.amount


@pytest.mark.parametrize("first", [confirm_subscription_candidate,
    mark_subscription_candidate_unsure, reject_subscription_candidate])
@pytest.mark.parametrize("second", [confirm_subscription_candidate,
    mark_subscription_candidate_unsure, reject_subscription_candidate])
def test_resolved_candidate_cannot_be_resolved_again(controlled_analysis, first, second):
    bank = BankState()
    process_incoming_transaction(bank, incoming_raw())
    candidate = bank.subscription_candidates[0]
    first(bank, candidate.id)
    status, balance, count = candidate.status, bank.balance, len(bank.subscriptions)
    with pytest.raises(ValueError, match="already been resolved"):
        second(bank, candidate.id)
    assert (candidate.status, bank.balance, len(bank.subscriptions)) == (status, balance, count)
    assert len(bank.transactions) == 1


@pytest.mark.parametrize("problem", ["missing_candidate", "missing_transaction", "duplicate_id", "duplicate_name"])
def test_unsure_validates_before_resolving(controlled_analysis, problem):
    bank = BankState()
    process_incoming_transaction(bank, incoming_raw())
    candidate = bank.subscription_candidates[0]
    candidate_id = candidate.id
    message = "already registered"
    if problem == "missing_candidate":
        candidate_id = "missing"
        message = "candidate not found"
    elif problem == "missing_transaction":
        bank.transactions.clear()
        message = "Original transaction not found"
    else:
        controlled_analysis.recurrence_confidence = 0.99
        controlled_analysis.type_confidence = 0.85
        raw = incoming_raw(customer_id="second")
        if problem == "duplicate_name":
            raw.update(merchant_id="other", merchant="  TEST SERVICE  ")
        process_incoming_transaction(bank, raw)
    balance, count = bank.balance, len(bank.subscriptions)
    with pytest.raises(ValueError, match=message):
        mark_subscription_candidate_unsure(bank, candidate_id)
    assert candidate.status == SubscriptionCandidateStatus.PENDING_CONFIRMATION
    assert bank.balance == balance
    assert len(bank.subscriptions) == count
