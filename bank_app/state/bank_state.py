from dataclasses import dataclass, field
from typing import List, Set

from bank_app.app_models import (
    Transaction,
    Subscription,
    SubscriptionCandidate,
    PendingAuthorization,
)


@dataclass
class BankState:
    balance: float = 1_250_000

    transactions: List[Transaction] = field(default_factory=list)
    subscriptions: List[Subscription] = field(default_factory=list)
    subscription_candidates: List[SubscriptionCandidate] = field(default_factory=list)
    pending_authorizations: List[PendingAuthorization] = field(default_factory=list)

    processed_demo_transactions: Set[str] = field(
        default_factory=set
    )

    def add_transaction(
        self,
        transaction: Transaction,
    ) -> None:
        self.transactions.append(transaction)

    def add_subscription(
        self,
        subscription: Subscription,
    ) -> None:
        self.subscriptions.append(subscription)

    def add_subscription_candidate(
        self,
        candidate: SubscriptionCandidate,
    ) -> None:
        self.subscription_candidates.append(candidate)

    def add_pending_authorization(
        self,
        authorization: PendingAuthorization,
    ) -> None:
        self.pending_authorizations.append(authorization)

    def get_subscription_by_id(
        self,
        subscription_id: str,
    ):
        for subscription in self.subscriptions:
            if subscription.id == subscription_id:
                return subscription

        return None

    def get_transaction_by_id(
        self,
        transaction_id: str,
    ):
        for transaction in self.transactions:
            if transaction.id == transaction_id:
                return transaction

        return None