"""Reversal package (TECH-18..21 / NB-18..21) — one mechanism, two windows.

Undo (<= 24h, silent — NB-19) and Reverse (> 24h, customer notice — NB-20)
share the core in ``core``; the fraud-risk badge ledger lives in
``fraud_flags`` (NB-21). The package contract (decision #1): the same
balance restoration, the same wallet-void rule, the same fraud-flag
trigger, the same NB-18-complete audit payload — differing only in the
window, the mandatory reason (reverse), and the customer notification
(reverse only).

Imports: models, audit, billing submodules (wallet/lifecycle/intake
constants) — never ``app.api``.
"""

from __future__ import annotations

from app.services.billing.reversals.core import (  # noqa: F401
    ReversalError,
    reversal_availability,
)
from app.services.billing.reversals.fraud_flags import (  # noqa: F401
    flag_sender_fraud,
    is_fraud_flagged,
)
from app.services.billing.reversals.reverse import reverse_verification  # noqa: F401
from app.services.billing.reversals.undo import undo_verification  # noqa: F401

__all__ = [
    'ReversalError',
    'reversal_availability',
    'undo_verification',
    'reverse_verification',
    'is_fraud_flagged',
    'flag_sender_fraud',
]
