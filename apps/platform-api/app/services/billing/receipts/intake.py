"""Upload intake: format/size validation, sha256, extraction trigger, dedup,
routing and flag computation (TECH-07/14 — NB-07/14).

Also carries the shared notification builders used by the dedup hard-reject
path at upload and by the verdict state machine — kept here so the module
graph stays acyclic (``intake`` imports nothing from ``queue``/``verdicts``/
``disputes``; those import from here).

Imports: models, audit, ``receipt_extraction`` and ``trusted_payers`` only —
no billing-internal cycle, never ``app.api``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.billing import receipt_extraction, trusted_payers
from app.services.billing.receipt_extraction import (
    EXTRACTION_FIELDS,
    LOW_CONFIDENCE_THRESHOLD,
)

UPLOAD_CONFIRMATION_MESSAGE = 'Receipt received — verification typically takes ≤24 hours.'
NO_OPEN_INVOICE_MESSAGE = 'You have no open invoice to apply this receipt to.'
UNSUPPORTED_FORMAT_MESSAGE = 'Unsupported file format.'

WRONG_BANK_REASON = 'Payment must land at CBE or Dashen. Please re-send to the account listed on your invoice.'
DUPLICATE_REASON = 'This reference number has already been credited.'
ILLEGIBLE_REASON = "We couldn't read your receipt clearly. Please re-upload a clearer copy."
DUPLICATE_BANNER = (
    'Your receipt (ref {ref}) was rejected. Reason: This reference number has already been '
    'credited. Please upload a new receipt for your current invoice.'
)
NOTIFICATION_EXPIRY_DAYS = 3

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
ALLOWED_CONTENT_TYPES = {'image/png', 'image/jpeg', 'application/pdf'}


class ReceiptVerdictError(Exception):
    """Domain error surfaced by the endpoint as HTTPException."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def upload_receipt(
    db: Session,
    org: Organization,
    *,
    file_name: str,
    content_type: str,
    file_bytes: bytes,
    user: User | None,
    mock_extraction: dict | None = None,
) -> PaymentReceipt:
    """Persist the receipt, run extraction, then dedup + route (NB-07)."""
    receipt = PaymentReceipt(
        organization_id=org.id,
        file_name=file_name,
        content_type=content_type,
        file_size_bytes=len(file_bytes),
        file_data=file_bytes,
        file_sha256=hashlib.sha256(file_bytes).hexdigest(),
        status='pending',
    )
    db.add(receipt)
    db.flush()

    result = receipt_extraction.extract_receipt(
        db, org, receipt, file_bytes, user, mock_extraction=mock_extraction
    )
    _apply_extraction_fields(receipt, result)
    receipt.has_zero_confidence = all(score == 0.0 for score in result.confidence.values())
    receipt.low_confidence_fields = [
        name for name in EXTRACTION_FIELDS if result.confidence[name] < LOW_CONFIDENCE_THRESHOLD
    ]

    _dedup_and_route(db, org, receipt)
    record_audit_event(
        db,
        event_type='receipts.uploaded',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=user,
        organization_id=org.id,
        description=f'Uploaded receipt {receipt.file_name}',
        payload={
            'file_name': receipt.file_name,
            'content_type': receipt.content_type,
            'file_size_bytes': receipt.file_size_bytes,
            'file_sha256': receipt.file_sha256,
            'invoice_number': receipt.invoice.invoice_number if receipt.invoice else None,
        },
    )
    return receipt


def _apply_extraction_fields(receipt: PaymentReceipt, result) -> None:
    """Copy the 8 extracted fields onto the receipt row. Per-field parse
    failures leave the column None (zero-confidence field); malformed
    extraction never fails the upload (NB-10.2)."""
    receipt.reference_number = _as_str(result.fields.get('reference_number'))
    receipt.sender_name = _as_str(result.fields.get('sender_name'))
    receipt.sender_account_number = _as_str(result.fields.get('sender_account_number'))
    receipt.receiver_account_number = _as_str(result.fields.get('receiver_account_number'))
    receipt.receiver_name = _as_str(result.fields.get('receiver_name'))
    receipt.bank_code = _as_str(result.fields.get('bank_identifier'))
    if receipt.bank_code:
        receipt.bank_code = receipt.bank_code.casefold()
    amount = _as_str(result.fields.get('transfer_amount'))
    if amount:
        try:
            receipt.amount_etb = Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            receipt.amount_etb = None
    transfer_date = _as_str(result.fields.get('transfer_date'))
    if transfer_date:
        try:
            from datetime import date as _date

            receipt.transfer_date = _date.fromisoformat(transfer_date)
        except ValueError:
            receipt.transfer_date = None


def _as_str(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _dedup_and_route(db: Session, org: Organization, receipt: PaymentReceipt) -> None:
    """System-wide dedup (NB-14) then routing to the oldest open invoice
    (NB-07.2). A duplicate is hard-rejected: NO queue item, NO SMS, NO
    routing; the fraud-flag audit pair fires. Unrouteable uploads (no open
    invoice) stay ``pending`` with ``invoice_id=None``; the endpoint layer
    rejects them with HTTP 400 and rolls the row back so the queue never
    surfaces a zombie (blueprint risk note 8)."""
    ref = receipt.reference_number
    if ref:
        original = _find_verified_by_ref(db, ref)
        if original is not None:
            receipt.status = 'rejected'
            receipt.verdict = 'reject_duplicate'
            receipt.is_duplicate = True
            receipt.rejection_reason = DUPLICATE_REASON
            receipt.invoice_id = None
            db.add(receipt)
            _flag_duplicate_pair(db, org, receipt, original)
            _rejected_notification(db, org, receipt, DUPLICATE_BANNER.format(ref=ref))
            return

    invoice = _oldest_open_invoice(db, org)
    if invoice is not None:
        receipt.invoice_id = invoice.id
    _compute_flags(db, receipt, invoice)
    db.add(receipt)


def _oldest_open_invoice(db: Session, org: Organization) -> SubscriptionInvoice | None:
    """Open invoice = ``balance_remaining_etb > 0`` (blueprint decision #3);
    oldest first by period start."""
    return db.execute(
        select(SubscriptionInvoice)
        .where(
            SubscriptionInvoice.organization_id == org.id,
            SubscriptionInvoice.balance_remaining_etb > 0,
        )
        .order_by(SubscriptionInvoice.billing_period_start.asc())
        .limit(1)
    ).scalars().first()


def _find_verified_by_ref(db: Session, ref: str) -> PaymentReceipt | None:
    """System-wide lookup (blueprint decision #5): NO organization filter."""
    return db.execute(
        select(PaymentReceipt).where(
            PaymentReceipt.reference_number == ref,
            PaymentReceipt.status == 'verified',
        ).limit(1)
    ).scalars().first()


def _flag_duplicate_pair(db: Session, org: Organization, attempt: PaymentReceipt, original: PaymentReceipt) -> None:
    """NB-14.4 fraud-flag pair: attempt + flagged (attached to the original)."""
    record_audit_event(
        db,
        event_type='receipts.duplicate_attempt',
        entity_type='payment_receipt',
        entity_id=attempt.id,
        organization_id=org.id,
        description=f'Duplicate reference {attempt.reference_number} attempted',
        payload={
            'reference_number': attempt.reference_number,
            'original_receipt_id': original.id,
        },
    )
    record_audit_event(
        db,
        event_type='receipts.duplicate_flagged',
        entity_type='payment_receipt',
        entity_id=original.id,
        organization_id=original.organization_id,
        description=f'Original receipt flagged: duplicate reference {attempt.reference_number}',
        payload={
            'reference_number': attempt.reference_number,
            'duplicate_receipt_id': attempt.id,
        },
    )


def _compute_flags(db: Session, receipt: PaymentReceipt, invoice: SubscriptionInvoice | None) -> None:
    """The six persisted booleans + surplus (blueprint §5 FLAGS)."""
    sender = receipt.sender_name
    receipt.is_new_sender = bool(sender) and not trusted_payers.is_trusted(
        db, receipt.organization_id, sender
    )
    receipt.is_cash_sender = bool(sender) and sender.casefold() == 'cash'
    bank = (receipt.bank_code or '').casefold()
    designated = invoice.designated_account.bank_code if invoice else None
    receipt.is_wrong_bank_within_portfolio = bool(bank) and bank in {'cbe', 'dashen'} and bank != designated
    amount = receipt.amount_etb
    balance = invoice.balance_remaining_etb if invoice else None
    tolerance = settings.wallet_auto_forward_tolerance_etb
    if amount is not None and balance is not None:
        receipt.is_large_surplus = amount > balance + tolerance
        receipt.surplus_etb = max(Decimal('0.00'), amount - balance)
    else:
        receipt.is_large_surplus = False
        receipt.surplus_etb = Decimal('0.00')


def recommended_verdict(db: Session, receipt: PaymentReceipt, invoice: SubscriptionInvoice | None) -> str | None:
    """Pre-fill rule (NB-11.3 / NB-13.1): trusted payer OR wrong-bank-within-
    portfolio -> 'verify'. CASH always overrides to None (NB-12.3)."""
    if receipt.is_cash_sender:
        return None
    if receipt.sender_name and not receipt.is_new_sender:
        return 'verify'
    if receipt.is_wrong_bank_within_portfolio:
        return 'verify'
    return None


# ---------------------------------------------------------------------------
# Shared banner builders (used by intake dedup AND verdicts)
# ---------------------------------------------------------------------------


def _rejected_notification(db: Session, org: Organization, receipt: PaymentReceipt, banner: str) -> Notification:
    notification = Notification(
        organization_id=org.id,
        kind='receipt_rejected',
        title='Receipt rejected',
        message=banner,
        payload={
            'reference_number': receipt.reference_number,
            'verdict': receipt.verdict,
            'rejection_reason': receipt.rejection_reason,
            'can_reupload': True,
        },
        expires_at=datetime.now(UTC) + timedelta(days=NOTIFICATION_EXPIRY_DAYS),
    )
    db.add(notification)
    return notification


def _verified_notification(db: Session, org: Organization, receipt: PaymentReceipt, outcome) -> Notification:
    if outcome.invoice_paid:
        message = f'Invoice #{outcome.invoice_number} paid. Your workspace is unlocked.'
    else:
        invoice = receipt.invoice
        remaining = invoice.balance_remaining_etb if invoice else Decimal('0.00')
        message = (
            f'Receipt credited against invoice #{outcome.invoice_number}. '
            f'Remaining balance: {remaining} ETB.'
        )
    notification = Notification(
        organization_id=org.id,
        kind='receipt_verified',
        title='Receipt verified',
        message=message,
        payload={
            'invoice_number': outcome.invoice_number,
            'reference_number': receipt.reference_number,
            'credit_delta_etb': str(outcome.credit_delta_etb),
            'invoice_paid': outcome.invoice_paid,
            'wallet_credit_etb': str(outcome.wallet_credit_etb),
        },
        expires_at=datetime.now(UTC) + timedelta(days=NOTIFICATION_EXPIRY_DAYS),
    )
    db.add(notification)
    return notification
