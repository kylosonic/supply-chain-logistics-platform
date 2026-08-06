"""Admin verdict state machine (blueprint §5) — the ONLY credit path.

Renders one of exactly five verdicts (NB-15) on a pending/escalated receipt:
escalate (the only SMS state, NB-16), the three rejections (NB-13/14/15)
and verify (credit application A/B/C with the large-surplus 3-way, NB-08/09).

Commit-aware (blueprint risk #1): credits + wallet + audit + notifications
land first, then ``credits.unlock_evaluation`` runs the Phase 1 refresh whose
internal commit persists everything together. A partial-unique IntegrityError
during credit application rolls back BEFORE any refresh so a partially-credited
state can never commit.

Imports: models, audit, ``credits``/``sms``/``trusted_payers`` and
``intake``'s constants + banner builders (one-directional).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.dispute_thread import DisputeThread
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.schemas.receipts import VerdictRequest
from app.services.audit import record_audit_event
from app.services.billing import credits, sms, trusted_payers
from app.services.billing.credits import CreditError
from app.services.billing.receipts.intake import (
    DUPLICATE_BANNER,
    DUPLICATE_REASON,
    ILLEGIBLE_REASON,
    NOTIFICATION_EXPIRY_DAYS,
    WRONG_BANK_REASON,
    ReceiptVerdictError,
    _find_verified_by_ref,
    _flag_duplicate_pair,
    _rejected_notification,
    _verified_notification,
)


def has_open_dispute(db: Session, receipt_id: str) -> bool:
    """True when the receipt carries an open dispute thread (NB-17)."""
    row = db.execute(
        select(DisputeThread.id).where(
            DisputeThread.receipt_id == receipt_id,
            DisputeThread.status == 'open',
        ).limit(1)
    ).first()
    return row is not None


def render_verdict(db: Session, admin_user: User, receipt_id: str, request: VerdictRequest) -> PaymentReceipt:
    """Render one of the five verdicts (NB-15) on a pending/escalated receipt."""
    receipt = db.get(PaymentReceipt, receipt_id)
    if receipt is None:
        raise ReceiptVerdictError(404, 'Receipt not found')
    if receipt.status not in ('pending', 'escalated'):
        raise ReceiptVerdictError(409, f'Receipt is already {receipt.status}')
    org = db.get(Organization, receipt.organization_id)
    verdict = request.verdict.value

    if verdict == 'escalate':
        return _escalate(db, org, receipt, request, admin_user)
    if verdict == 'verify':
        invoice = db.get(SubscriptionInvoice, receipt.invoice_id) if receipt.invoice_id else None
        return _apply_verify(db, org, receipt, invoice, request, admin_user)
    return _apply_rejection(db, org, receipt, verdict, request, admin_user)


def _escalate(
    db: Session, org: Organization, receipt: PaymentReceipt, request: VerdictRequest, admin_user: User
) -> PaymentReceipt:
    """Escalation: the ONLY SMS-triggering state (NB-16.1/16.4).

    The mandatory admin note IS the escalation question (decision #12).
    No credit, no phase change: a locked workspace stays locked (NB-16.5).
    """
    note = (request.note or '').strip()
    if not note:
        raise ReceiptVerdictError(422, 'Escalation requires a note — it is the question shown to the customer')
    receipt.status = 'escalated'
    receipt.verdict = 'escalate'
    receipt.admin_note = note
    receipt.decision_made_by_user_id = admin_user.id if admin_user else None
    receipt.decided_at = datetime.now(UTC)
    db.add(receipt)
    record_audit_event(
        db,
        event_type='receipts.escalated',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Escalated receipt {receipt.reference_number or receipt.id}',
        payload={'note': note, 'reference_number': receipt.reference_number},
    )
    notification = Notification(
        organization_id=org.id,
        kind='receipt_escalated',
        title='Receipt question',
        message=note,
        payload={'question': note, 'reference_number': receipt.reference_number},
        expires_at=datetime.now(UTC) + timedelta(days=NOTIFICATION_EXPIRY_DAYS),
    )
    db.add(notification)
    sms.send_escalation_sms(db, org, receipt)  # fail-soft: banner fires regardless
    return receipt


def _apply_rejection(
    db: Session, org: Organization, receipt: PaymentReceipt, verdict: str, request: VerdictRequest, admin_user: User
) -> PaymentReceipt:
    """All three rejection verdicts (NB-13/14/15). No SMS, ever (NB-15.4)."""
    if verdict == 'reject_wrong_bank':
        bank = (receipt.bank_code or '').casefold()
        if bank in {'cbe', 'dashen'}:
            # Server guard (decision #11): only out-of-portfolio banks are
            # rejectable as wrong-bank — the verdict is a safety valve.
            raise ReceiptVerdictError(
                422, 'This receipt landed within the FreightPilot bank portfolio — use verify or a different verdict.'
            )
        reason = WRONG_BANK_REASON
    elif verdict == 'reject_duplicate':
        reason = DUPLICATE_REASON
        original = _find_verified_by_ref(db, receipt.reference_number) if receipt.reference_number else None
        if original is not None:
            _flag_duplicate_pair(db, org, receipt, original)
        else:
            record_audit_event(
                db,
                event_type='receipts.duplicate_attempt',
                entity_type='payment_receipt',
                entity_id=receipt.id,
                organization_id=org.id,
                description=f'Duplicate reference {receipt.reference_number} rejected',
                payload={'reference_number': receipt.reference_number, 'original_receipt_id': None},
            )
    elif verdict == 'reject_illegible':
        reason = ILLEGIBLE_REASON
    else:
        raise ReceiptVerdictError(422, f'Unsupported verdict {verdict!r}')

    receipt.status = 'rejected'
    receipt.verdict = verdict
    receipt.rejection_reason = reason
    receipt.decision_made_by_user_id = admin_user.id if admin_user else None
    receipt.decided_at = datetime.now(UTC)
    db.add(receipt)
    banner = DUPLICATE_BANNER.format(ref=receipt.reference_number) if verdict == 'reject_duplicate' else reason
    _rejected_notification(db, org, receipt, banner)
    record_audit_event(
        db,
        event_type='receipts.rejected',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Rejected receipt {receipt.reference_number or receipt.id}',
        payload={'verdict': verdict, 'reference_number': receipt.reference_number, 'reason': reason},
    )
    return receipt


def _apply_verify(
    db: Session,
    org: Organization,
    receipt: PaymentReceipt,
    invoice: SubscriptionInvoice | None,
    request: VerdictRequest,
    admin_user: User,
) -> PaymentReceipt:
    """Verify -> the credit-application path (blueprint §5 A/B/C)."""
    # System-wide dedup backstop first: a verified receipt with the same ref
    # makes this verify impossible (partial-unique index). The 409 takes
    # priority over every other validation — including the large-surplus
    # 422 that would otherwise fire when the primary invoice is already paid.
    if receipt.reference_number:
        verified_other = _find_verified_by_ref(db, receipt.reference_number)
        if verified_other is not None and str(verified_other.id) != str(receipt.id):
            raise ReceiptVerdictError(
                409,
                'This reference number has already been credited. '
                'Only one verified receipt per reference — reject the duplicate.',
            )
    if invoice is None:
        raise ReceiptVerdictError(422, 'Receipt has no routed invoice to credit')
    if receipt.is_large_surplus and request.large_surplus_decision is None:
        raise ReceiptVerdictError(
            422, 'Large surplus requires a 3-way admin decision: credit_forward, credit_backward, or partial_ignore'
        )
    if request.large_surplus_decision is not None and request.large_surplus_decision.value == 'partial_ignore':
        if request.partial_credit_amount_etb is None:
            raise ReceiptVerdictError(422, 'partial_ignore requires partial_credit_amount_etb')

    try:
        outcome = credits.apply_credit(
            db,
            org,
            receipt,
            decision=request.large_surplus_decision.value if request.large_surplus_decision else None,
            partial_amount=request.partial_credit_amount_etb,
            admin_user=admin_user,
            note=request.admin_note,
            trusted_payer_action=request.trusted_payer_action.value if request.trusted_payer_action else None,
        )
        # Surface the partial-unique backstop deterministically BEFORE any
        # refresh/commit (blueprint risk #1): a second verified receipt with
        # the same reference must roll back cleanly -> 409.
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ReceiptVerdictError(
            409, 'This reference number has already been credited. Only one verified receipt per reference — reject the duplicate.'
        ) from exc
    except CreditError as exc:
        raise ReceiptVerdictError(422, str(exc)) from exc

    if request.trusted_payer_action is not None and request.trusted_payer_action.value == 'added':
        if receipt.sender_name:
            trusted_payers.add_trusted_payer(db, org, receipt.sender_name, admin_user)
        receipt.trusted_payer_action = 'added'
    elif request.trusted_payer_action is not None:
        receipt.trusted_payer_action = request.trusted_payer_action.value
    if request.admin_note:
        receipt.admin_note = request.admin_note
    db.add(receipt)
    _verified_notification(db, org, receipt, outcome)
    credits.unlock_evaluation(db, org)  # pessimistic unlock: refresh commits credits + wallet + audit together
    return receipt
