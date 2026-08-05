"""SMS outbox (TECH-16 / NB-16). No real gateway call exists in Phase 2.

``enqueue_sms`` writes a ``queued`` row; ``_dispatch_sms`` raises
``NotImplementedError`` (swallowed) — the gateway attaches later by
polling ``status='queued'``. Escalation is the ONLY SMS-triggering state.

Imports models + audit only.
"""

from __future__ import annotations

from app.core.config import settings
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.sms_message import SmsMessage
from app.services.audit import record_audit_event
from sqlalchemy.orm import Session

ESCALATION_SMS_TEMPLATE = (
    'Hi {name}, FreightPilot has a question about your recent receipt. '
    'Please log in to your workspace to respond.'
)
_SMS_MAX_CHARS = 160


def _mask_phone(phone: str) -> str:
    if len(phone) <= 4:
        return '*' * len(phone)
    return f'{phone[:3]}***{phone[-2:]}'


def enqueue_sms(
    db: Session, *, organization_id, to_phone: str, body: str, receipt_id=None
) -> SmsMessage:
    """Write a ``queued`` outbox row. Body is enforced <= 160 chars."""
    if len(body) > _SMS_MAX_CHARS:
        raise ValueError(f'SMS body exceeds {_SMS_MAX_CHARS} characters')
    row = SmsMessage(
        organization_id=organization_id,
        receipt_id=receipt_id,
        to_phone=to_phone,
        body=body,
        status='queued',
    )
    db.add(row)
    db.flush()
    try:
        _dispatch_sms(row)
    except NotImplementedError:
        pass  # gateway not attached — row stays queued
    return row


def _dispatch_sms(row: SmsMessage) -> None:
    """Gateway attachment point (Phase 3+). Never implemented in Phase 2."""
    raise NotImplementedError(
        'SMS gateway not attached; dispatch attaches later by polling sms_messages where status=queued'
    )


def send_escalation_sms(db: Session, org: Organization, receipt: PaymentReceipt) -> SmsMessage:
    """The only SMS state (NB-16.4): escalation.

    Missing ``org.contact_phone`` -> ``failed`` row with
    ``no_phone_on_file`` (fail-soft — the in-product banner still fires).
    """
    phone = (org.contact_phone or '').strip()
    if not phone:
        row = SmsMessage(
            organization_id=org.id,
            receipt_id=receipt.id,
            to_phone='',
            body=ESCALATION_SMS_TEMPLATE.format(name=org.name),
            status='failed',
            error_message='no_phone_on_file',
        )
        db.add(row)
        db.flush()
        record_audit_event(
            db,
            event_type='sms.enqueued',
            entity_type='payment_receipt',
            entity_id=receipt.id,
            organization_id=org.id,
            description='Escalation SMS could not be queued: no phone on file',
            payload={'to_phone': None, 'status': 'failed', 'error_message': 'no_phone_on_file'},
        )
        return row

    body = ESCALATION_SMS_TEMPLATE.format(name=org.name)
    assert len(body) <= _SMS_MAX_CHARS, 'escalation SMS template exceeds 160 characters'
    row = enqueue_sms(
        db,
        organization_id=org.id,
        to_phone=phone,
        body=body,
        receipt_id=receipt.id,
    )
    record_audit_event(
        db,
        event_type='sms.enqueued',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        organization_id=org.id,
        description='Escalation SMS queued',
        payload={
            'to_phone': _mask_phone(phone),
            'status': row.status,
            'brand': settings.sms_brand_name,
            'body_length': len(body),
        },
    )
    return row
