"""Post-24h Reverse (TECH-18/20 / NB-20): mandatory reason + customer notice.

Guards: receipt exists (404) · status verified (409) · ``reversal_status IS
NULL`` (409 — one reversal per receipt) · now > ``decided_at + 24h`` (409 —
inside the window use Undo) · stripped non-empty reason (422, NB-20.2).
Then the identical core steps with kind ``reversed``, plus the in-product
Notification with the EXACT NB-20.3 copy (decision #8). NO SMS, NO automatic
refund execution (NB-20.5); applied wallet rows stay untouched (decision #5).

Commit-aware (blueprint risk #1): core mutations + Notification land first;
the refresh's internal commit persists everything together.

Imports: core + models + Notification + intake constants (never ``app.api``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.services.billing.receipts.intake import NOTIFICATION_EXPIRY_DAYS
from app.services.billing.reversals import core
from app.services.billing.reversals.core import ReversalError

REVERSAL_NOTIFICATION_KIND = 'receipt_reversed'
REVERSAL_MESSAGE_TEMPLATE = (
    'Your payment of {amount} ETB credited on {date} against Invoice #{invoice} has been reversed. '
    'Reason: {reason}. Please contact us if you believe this is in error. Your workspace may be locked.'
)
_ADDIS = ZoneInfo('Africa/Addis_Ababa')
_MONTHS_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _format_addis_date(value: datetime) -> str:
    """``decided_at`` rendered in Africa/Addis_Ababa as ``%d %b %Y``.

    Month abbreviations are hardcoded so the copy is locale-independent
    (Python's ``%b`` follows the process locale).
    """
    local = value.astimezone(_ADDIS)
    return f'{local.day:02d} {_MONTHS_ABBR[local.month - 1]} {local.year}'


def build_reversal_message(verified_payload: dict, decided_at: datetime | None, reason: str) -> str:
    """The EXACT NB-20.3 copy with amount/date/invoice/reason interpolated.

    Single source of the message text: reverse.py writes it to the
    Notification row AND the endpoint re-reads it from here for
    ``ReversalRead.message`` — the copy can never drift.
    """
    decided = core._as_utc(decided_at)
    return REVERSAL_MESSAGE_TEMPLATE.format(
        amount=verified_payload.get('amount_etb'),
        date=_format_addis_date(decided) if decided is not None else '',
        invoice=verified_payload.get('invoice_number'),
        reason=reason,
    )


def reverse_verification(db: Session, admin_user: User, receipt_id: str, reason: str) -> PaymentReceipt:
    """Explicit reverse of a verified receipt after the 24h window (NB-20)."""
    reason = (reason or '').strip()
    if not reason:
        raise ReversalError(422, 'Reverse requires a reason note (NB-20.2)')

    receipt = db.get(PaymentReceipt, receipt_id)
    if receipt is None:
        raise ReversalError(404, 'Receipt not found')
    if receipt.status != 'verified':
        raise ReversalError(409, f'Only verified receipts can be reversed — receipt is {receipt.status}')
    if receipt.reversal_status is not None:
        raise ReversalError(409, 'This receipt has already been reversed — one reversal per receipt')

    now = core._now()
    decided = core._as_utc(receipt.decided_at)
    if decided is None or now <= decided + timedelta(hours=core.UNDO_WINDOW_HOURS):
        raise ReversalError(409, 'Use Undo within 24 hours — Reverse is for receipts older than 24 hours')

    org = db.get(Organization, receipt.organization_id)
    verified_event = core._load_verified_audit(db, receipt)
    invoice = db.get(SubscriptionInvoice, receipt.invoice_id) if receipt.invoice_id else None

    restored = core._restore_balance(db, org, invoice, verified_event)
    wallet_voided = core._void_available_wallet(db, org, receipt, 'reversed')
    core._apply_fraud_flag_if_added(db, org, receipt, verified_event, 'reversed', admin_user)
    core._mark_receipt(db, receipt, 'reversed', reason, admin_user)
    core._record_reversal_audit(
        db,
        org=org,
        receipt=receipt,
        verified_event=verified_event,
        admin_user=admin_user,
        reversal_kind='reversed',
        note=reason,
        restored_balance=restored,
        wallet_voided=wallet_voided,
        notification_sent=True,
    )

    # The EXACT NB-20.3 copy, in-product only (NO SMS — NB-16 is the only
    # SMS state; NO refund execution — NB-20.5).
    message = build_reversal_message(verified_event.payload or {}, decided, reason)
    db.add(
        Notification(
            organization_id=org.id,
            kind=REVERSAL_NOTIFICATION_KIND,
            title='Receipt reversed',
            message=message,
            payload={
                'receipt_id': str(receipt.id),
                'reference_number': receipt.reference_number,
                'invoice_number': (verified_event.payload or {}).get('invoice_number'),
                'reason': reason,
            },
            expires_at=now + timedelta(days=NOTIFICATION_EXPIRY_DAYS),
        )
    )
    core._relock(db, org, now)
    return receipt
