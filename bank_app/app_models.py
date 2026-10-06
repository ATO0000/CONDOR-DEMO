from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


# ============================================================
# ENUMS
# ============================================================

class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TrustStatus(str, Enum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class SubscriptionCandidateStatus(str, Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    REJECTED_BY_USER = "REJECTED_BY_USER"
    UNSURE_BY_USER = "UNSURE_BY_USER"


class AuthorizationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ============================================================
# TRANSACTION
# ============================================================

@dataclass
class Transaction:
    id: str
    merchant: str
    merchant_id: str
    amount: float
    date: datetime

    status: TransactionStatus = TransactionStatus.COMPLETED

    recurring_type: Optional[str] = None
    recurrence_confidence: Optional[float] = None
    type_confidence: Optional[float] = None

    detection_reasons: List[str] = field(default_factory=list)


# ============================================================
# SUBSCRIPTION
# ============================================================

@dataclass
class Subscription:
    id: str
    merchant: str
    merchant_id: str

    current_price: float
    frequency: str
    last_charge_date: datetime

    recurring_type: str

    trust_status: TrustStatus = TrustStatus.UNTRUSTED
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    recurrence_confidence: Optional[float] = None
    type_confidence: Optional[float] = None

    detection_reasons: List[str] = field(default_factory=list)
    transaction_history: List[str] = field(default_factory=list)
    needs_user_verification: bool = False


# ============================================================
# POSSIBLE NEW SUBSCRIPTION
# ============================================================

@dataclass
class SubscriptionCandidate:
    id: str
    transaction_id: str

    merchant: str
    merchant_id: str

    detected_type: str

    recurrence_confidence: float
    type_confidence: float

    reasons: List[str] = field(default_factory=list)

    status: SubscriptionCandidateStatus = (
        SubscriptionCandidateStatus.PENDING_CONFIRMATION
    )


# ============================================================
# PENDING AUTHORIZATION
# ============================================================

@dataclass
class PendingAuthorization:
    id: str

    transaction_id: str
    subscription_id: str

    previous_amount: float
    attempted_amount: float
    percentage_change: float

    reason: str

    status: AuthorizationStatus = AuthorizationStatus.PENDING