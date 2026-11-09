"""Shared reversal core (TECH-18..21 / NB-18..21, decision #1).

One mechanism, two eligibility windows: Undo (<= 24h, silent) and Reverse
(> 24h, customer notice) share every mutating primitive — balance
restoration from the ORIGINAL ``receipts.verified`` audit payload (read-only
source of truth, decision #3), wallet void of un-applied rows (decision #5),
the fraud-flag trigger (decision #6), the full NB-18 audit record (decision
#8), and the workspace re-lock via ``lifecycle.refresh_workspace_state``
(decision #4).

Commit-aware (blueprint risk #1): all mutations land on the session first;
``_relock``'s internal commit persists everything together — mirrors
``render_verdict``'s pessimistic pattern. Guards always raise BEFORE any
balance is touched.

Imports: models, audit, wallet, lifecycle, intake constants, fraud_flags.
Never ``app.api``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_event import AuditEvent
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.billing import lifecycle, wallet
from app.services.billing.money import quantize_money
from app.services.billing.receipts.intake import NOTIFICATION_EXPIRY_DAYS
from app.services.billing.reversals import fraud_flags

UNDO_WINDOW_HOURS = settings.reversal_undo_window_hours


class ReversalError(Exception):
    """Domain error surfaced by the endpoint as HTTPException.

    Mirror of ``ReceiptVerdictError``: ``(status_code, message)``.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _as_utc(value: datetime | None) -> datetime | None:
    """Normalize naive datetimes (sqlite round-trips) to UTC-aware."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)


def _now() -> datetime:
    return datetime.now(UTC)


def reversal_availability(db: Session, receipt: PaymentReceipt, now: datetime) -> dict:
    """Server-side window evaluation (decision #7).

    ``undo_available = status=='verified' AND reversal_status IS NULL AND
    now <= decided_at + 24h``. The boundary at exactly 24h is Undo-eligible.
    """
    if receipt.status != 'verified' or receipt.reversal_status is not None:
        return {'undo_available': False, 'undo_available_until': None, 'reverse_available': False}
    decided = _as_utc(receipt.decided_at)
    if decided is None:
        return {'undo_available': False, 'undo_available_until': None, 'reverse_available': False}
    deadline = decided + timedelta(hours=UNDO_WINDOW_HOURS)
    undo_available = now <= deadline
    return {
        'undo_available': undo_available,
        'undo_available_until': deadline,
        'reverse_available': not undo_available,
    }


def _load_verified_audit(db: Session, receipt: PaymentReceipt) -> AuditEvent:
    """The ORIGINAL ``receipts.verified`` event — read-only source of truth.

    The reversal's credit arithmetic reads ``credit_delta_etb`` /
    ``balance_before_etb`` from THIS payload, never from receipt columns
    (which do not store them). Missing event -> defensive 409: a silent
    inconsistency must not be papered over (blueprint risk #2).
    """
    event = db.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == 'receipts.verified',
            AuditEvent.entity_type == 'payment_receipt',
            AuditEvent.entity_id == str(receipt.id),
        ).order_by(AuditEvent.created_at.asc()).limit(1)
    ).scalars().first()
    if event is None:
        raise ReversalError(409, 'No verified audit record exists for this receipt — reversal blocked')
    return event


def _restore_balance(
    db: Session, org: Organization, invoice: SubscriptionInvoice | None, verified_event: AuditEvent
) -> Decimal:
    """Restore ``new = q(current_balance + credit_delta)`` (decision #3).

    ``status='issued'`` when the restored balance > 0; stays ``paid`` at
    zero — deterministic even when other receipts covered the same invoice
    (NB-08 multi-receipt case). Returns the restored balance.
    """
    if invoice is None:
        raise ReversalError(409, 'Receipt has no routed invoice to restore')
    payload = verified_event.payload or {}
    credit_delta = Decimal(str(payload.get('credit_delta_etb') or '0.00'))
    new_balance = quantize_money(invoice.balance_remaining_etb + credit_delta)
    invoice.balance_remaining_etb = new_balance
    if new_balance > 0:
        invoice.status = 'issued'
    db.add(invoice)
    return new_balance


def _void_available_wallet(db: Session, org: Organization, receipt: PaymentReceipt, reversal_kind: str) -> Decimal:
    """Void un-applied wallet credits; returns the voided amount (decision #5)."""
    return wallet.void_wallet_credits_for_receipt(db, org, receipt, reversal_kind)


def _apply_fraud_flag_if_added(
    db: Session,
    org: Organization,
    receipt: PaymentReceipt,
    verified_event: AuditEvent,
    reversal_kind: str,
    admin_user: User,
) -> None:
    """Badge the sender when the ORIGINAL verify added them to the trusted
    list (decision #6) — fires on undo AND reverse (a silent clawback is the
    stronger fraud signal; the badge is non-punitive)."""
    payload = verified_event.payload or {}
    if payload.get('trusted_payer_action') == 'added' and receipt.sender_name:
        fraud_flags.flag_sender_fraud(
            db,
            org,
            receipt.sender_name,
            admin_user,
            original_verified_event_id=str(verified_event.id),
        )


def _record_reversal_audit(
    db: Session,
    *,
    org: Organization,
    receipt: PaymentReceipt,
    verified_event: AuditEvent,
    admin_user: User,
    reversal_kind: str,
    note: str | None,
    restored_balance: Decimal,
    wallet_voided: Decimal,
    notification_sent: bool = False,
) -> AuditEvent:
    """Write ``receipts.undo`` / ``receipts.reversed`` — the full NB-18 field
    set (decision #3/#8). ``balance_before_etb`` = the pre-restoration
    balance (derived exactly: ``restored - credit_delta``)."""
    payload = verified_event.payload or {}
    delta = Decimal(str(payload.get('credit_delta_etb') or '0.00'))
    balance_before = quantize_money(restored_balance - delta)
    event_type = 'receipts.undo' if reversal_kind == 'undo' else 'receipts.reversed'
    fields = {
        'invoice_number': payload.get('invoice_number'),
        'reference_number': receipt.reference_number,
        'sender_name': receipt.sender_name,
        'amount_etb': payload.get('amount_etb'),
        'balance_before_etb': str(balance_before),
        'decision': reversal_kind,
        'credit_delta_etb': str(-delta),
        'note': note,
        'reversal_status': reversal_kind,
        'restored_balance_etb': str(restored_balance),
        'wallet_voided_etb': str(wallet_voided),
        'original_verified_event_id': str(verified_event.id),
    }
    if notification_sent:
        fields['notification_sent'] = True
    return record_audit_event(
        db,
        event_type=event_type,
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'{reversal_kind.title()} verification for receipt {receipt.reference_number or receipt.id}',
        payload=fields,
    )


def _mark_receipt(db: Session, receipt: PaymentReceipt, kind: str, note: str | None, admin_user: User) -> None:
    """Set the four reversal columns (decision #2 — status stays ``verified``)."""
    receipt.reversal_status = kind
    receipt.reversal_note = (note or '').strip() or None
    receipt.reversed_by_user_id = admin_user.id if admin_user else None
    receipt.reversed_at = _now()
    db.add(receipt)


def _relock(db: Session, org: Organization, now: datetime):
    """Re-lock via the Phase 1 engine (decision #4): GRACE|HARD_LOCKED are
    both read-only. The refresh's internal commit persists everything."""
    return lifecycle.refresh_workspace_state(db, org, now)
