"""Disputes (NB-17): rejection -> escalation conversion and resolution.

``submit_dispute`` converts a rejected receipt into an escalated queue item
with an open thread (one thread per receipt — decision #14). ``resolve_dispute``
is the admin's final decision on a disputed receipt: verify routes through the
normal credit path (A/B/C), any rejection maintains the rejection with a
``dispute_resolved`` banner.

Imports: models, audit, and ``verdicts``' credit/rejection helpers
(one-directional: disputes -> verdicts -> intake).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dispute_thread import DisputeThread
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.schemas.receipts import VerdictRequest
from app.services.audit import record_audit_event
from app.services.billing.receipts.intake import NOTIFICATION_EXPIRY_DAYS, ReceiptVerdictError
from app.services.billing.receipts.verdicts import _apply_rejection, _apply_verify


def submit_dispute(db: Session, org: Organization, user: User, receipt_id: str, text: str) -> DisputeThread:
    """Customer dispute on a rejected receipt; converts it to ``escalated``."""
    receipt = db.get(PaymentReceipt, receipt_id)
    if receipt is None or receipt.organization_id != org.id:
        raise ReceiptVerdictError(404, 'Receipt not found')
    if receipt.status != 'rejected':
        raise ReceiptVerdictError(409, 'Only rejected receipts can be disputed')
    existing = db.execute(
        select(DisputeThread.id).where(DisputeThread.receipt_id == receipt.id).limit(1)
    ).first()
    if existing is not None:
        raise ReceiptVerdictError(409, 'A dispute thread already exists for this receipt')
    thread = DisputeThread(
        receipt_id=receipt.id,
        organization_id=org.id,
        dispute_text=text,
        submitted_by_user_id=user.id if user else None,
        status='open',
    )
    db.add(thread)
    receipt.status = 'escalated'
    db.add(receipt)
    record_audit_event(
        db,
        event_type='receipts.dispute_submitted',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=user,
        organization_id=org.id,
        description=f'Dispute submitted for receipt {receipt.reference_number or receipt.id}',
        payload={'text': text, 'reference_number': receipt.reference_number},
    )
    return thread


def resolve_dispute(
    db: Session, admin_user: User, receipt_id: str, request: VerdictRequest
) -> PaymentReceipt:
    """Admin's final decision on a disputed receipt (NB-17.4).

    verify -> the normal credit path (A/B/C) + thread resolved; any
    rejection -> maintain_rejection + ``dispute_resolved`` banner.
    """
    receipt = db.get(PaymentReceipt, receipt_id)
    if receipt is None:
        raise ReceiptVerdictError(404, 'Receipt not found')
    thread = db.execute(
        select(DisputeThread).where(
            DisputeThread.receipt_id == receipt.id,
            DisputeThread.status == 'open',
        )
    ).scalar_one_or_none()
    if thread is None:
        raise ReceiptVerdictError(409, 'No open dispute thread for this receipt')
    org = db.get(Organization, receipt.organization_id)
    verdict = request.verdict.value

    if verdict == 'verify':
        invoice = db.get(SubscriptionInvoice, receipt.invoice_id) if receipt.invoice_id else None
        receipt = _apply_verify(db, org, receipt, invoice, request, admin_user)
        thread.status = 'resolved'
        thread.resolution = 'verify'
    else:
        _apply_rejection(db, org, receipt, verdict, request, admin_user)
        thread.status = 'resolved'
        thread.resolution = 'maintain_rejection'
        db.add(
            Notification(
                organization_id=org.id,
                kind='dispute_resolved',
                title='Dispute resolved',
                message='Your dispute was reviewed. The original decision stands — your receipt remains rejected.',
                payload={'resolution': 'maintain_rejection', 'reference_number': receipt.reference_number},
                expires_at=datetime.now(UTC) + timedelta(days=NOTIFICATION_EXPIRY_DAYS),
            )
        )
    thread.resolved_by_user_id = admin_user.id if admin_user else None
    thread.resolved_at = datetime.now(UTC)
    db.add(thread)
    record_audit_event(
        db,
        event_type='receipts.dispute_resolved',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Dispute resolved with {thread.resolution} for receipt {receipt.reference_number or receipt.id}',
        payload={'resolution': thread.resolution, 'receipt_id': str(receipt.id)},
    )
    return receipt
