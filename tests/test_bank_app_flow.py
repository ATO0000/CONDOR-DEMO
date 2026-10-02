import json

import pytest

from bank_app.app_models import (
    AuthorizationStatus,
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
from bank_app.services.subscription_service import (
    confirm_subscription_candidate,
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

    assert len(bank.subscription_candidates) == 1

    balance_after_first_charge = bank.balance

    # --------------------------------------------------------
    # USUARIO CONFIRMA
    # --------------------------------------------------------

    candidate = bank.subscription_candidates[0]

    subscription = confirm_subscription_candidate(
        bank,
        candidate.id,
    )

    assert subscription.trust_status == TrustStatus.UNTRUSTED
    assert subscription.current_price == 5290

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