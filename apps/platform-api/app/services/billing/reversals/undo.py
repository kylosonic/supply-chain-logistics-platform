"""Silent Undo (TECH-18/19 / NB-18/19): the within-24h correction window.

Guards (decisions #7/#9): receipt exists (404) · status verified (409) ·
``reversal_status IS NULL`` (409 — one reversal per receipt) · now <=
``decided_at + 24h`` (409 — SERVER guard; UI hiding is UX only). Then the
shared core: restore balance from the original ``receipts.verified`` audit
payload, void available wallet credits, fraud-flag when the verify added
the sender, mark the four reversal columns, write the ``receipts.undo``
audit record, re-lock. NO Notification row, NO SMS (NB-19.3).

Commit-aware (blueprint risk #1): core mutations land first; the refresh's
internal commit persists everything together.

Imports: core + models only (never ``app.api``).
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.services.billing.reversals import core
from app.services.billing.reversals.core import ReversalError


def undo_verification(
    db: Session,
    admin_user: User,
    receipt_id: str,
    note: str | None = None,
    organization_id=None,
) -> PaymentReceipt:
    """Silent undo of a verified receipt within the 24h window (NB-19)."""
    receipt = db.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.id == receipt_id,
            PaymentReceipt.organization_id == organization_id,
        )
    ).scalar_one_or_none()
    if receipt is None:
        raise ReversalError(404, 'Receipt not found')
    if receipt.status != 'verified':
        raise ReversalError(409, f'Only verified receipts can be undone — receipt is {receipt.status}')
    if receipt.reversal_status is not None:
        raise ReversalError(409, 'This receipt has already been reversed — one reversal per receipt')

    now = core._now()
    decided = core._as_utc(receipt.decided_at)
    if decided is None or now > decided + timedelta(hours=core.UNDO_WINDOW_HOURS):
        raise ReversalError(409, 'Undo window closed — use Reverse for receipts older than 24 hours')

    org = db.get(Organization, receipt.organization_id)
    verified_event = core._load_verified_audit(db, receipt)
    invoice = db.get(SubscriptionInvoice, receipt.invoice_id) if receipt.invoice_id else None

    restored = core._restore_balance(db, org, invoice, verified_event)
    wallet_voided = core._void_available_wallet(db, org, receipt, 'undo')
    core._apply_fraud_flag_if_added(db, org, receipt, verified_event, 'undo', admin_user)
    core._mark_receipt(db, receipt, 'undo', note, admin_user)
    core._record_reversal_audit(
        db,
        org=org,
        receipt=receipt,
        verified_event=verified_event,
        admin_user=admin_user,
        reversal_kind='undo',
        note=note,
        restored_balance=restored,
        wallet_voided=wallet_voided,
    )
    # NO Notification row, NO SMS.
    core._relock(db, org, now)
    return receipt
