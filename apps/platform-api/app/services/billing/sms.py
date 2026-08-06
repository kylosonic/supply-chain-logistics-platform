"""SMS outbox (TECH-16 / NB-16) + generic REST gateway adapter (PROD-03).

``enqueue_sms`` writes a ``queued`` row and dispatches synchronously through
the provider-agnostic gateway adapter: POST JSON ``{to, sender, text, brand}``
to ``settings.sms_gateway_url`` with ``Authorization: Bearer <api_key>``.
Unconfigured deployments (no URL or no key) keep rows ``queued`` (outbox
semantics — a poller can attach later). Fail-soft is load-bearing:
``_dispatch_sms`` NEVER raises into the escalation decision path; gateway
failures flip the row to ``failed`` with a truncated ``error_message``.
Escalation is the ONLY SMS-triggering state (NB-16.4).

DAG: services.billing.sms -> models(3), core.config, services.audit
(acyclic; never imports app.api).
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.sms_message import SmsMessage
from app.services.audit import record_audit_event

ESCALATION_SMS_TEMPLATE = (
    'Hi {name}, FreightPilot has a question about your recent receipt. '
    'Please log in to your workspace to respond.'
)
_SMS_MAX_CHARS = 160
_GATEWAY_TIMEOUT_SECONDS = 15.0
_MAX_ERROR_MESSAGE_CHARS = 200


def mask_phone(phone: str) -> str:
    """Mask a phone for audit payloads: first 3 chars + last 2, stars between."""
    if len(phone) <= 4:
        return '*' * len(phone)
    return f'{phone[:3]}***{phone[-2:]}'


def _post_to_gateway(payload: dict) -> dict | None:
    """POST the payload to the configured gateway (test seam).

    Raises on transport errors and non-2xx — the caller converts to a
    ``failed`` row; dispatch never propagates to the escalation path.
    Returns the parsed JSON body when the gateway returns one (its ``id``
    is captured as ``gateway_message_id``).
    """
    response = httpx.post(
        settings.sms_gateway_url,
        json=payload,
        headers={'Authorization': f'Bearer {settings.sms_gateway_api_key}'},
        timeout=_GATEWAY_TIMEOUT_SECONDS,
    )
    if response.status_code >= 300:
        raise RuntimeError(f'SMS gateway returned HTTP {response.status_code}')
    try:
        return response.json()
    except ValueError:
        return None


def _dispatch_sms(row: SmsMessage) -> None:
    """Gateway dispatch (PROD-03). NEVER raises.

    Unconfigured (no URL or no key) -> return immediately; row stays
    ``queued`` (dev/test parity + poller-ready outbox). Configured ->
    POST ``{to, sender, text, brand}``; success -> ``sent`` +
    ``provider_name='generic_http'`` + ``sent_at``; any exception ->
    ``failed`` with truncated ``error_message``.
    """
    if not settings.sms_gateway_url or not settings.sms_gateway_api_key:
        return
    payload = {
        'to': row.to_phone,
        'sender': settings.sms_sender_name,
        'text': row.body,
        'brand': settings.sms_brand_name,
    }
    try:
        body = _post_to_gateway(payload)
    except Exception as exc:  # noqa: BLE001 — fail-soft is the contract
        row.status = 'failed'
        row.error_message = str(exc)[:_MAX_ERROR_MESSAGE_CHARS]
        return
    row.status = 'sent'
    row.provider_name = 'generic_http'
    row.sent_at = datetime.now(UTC)
    if isinstance(body, dict) and isinstance(body.get('id'), str):
        row.gateway_message_id = body['id']


def enqueue_sms(
    db: Session, *, organization_id, to_phone: str, body: str, receipt_id=None
) -> SmsMessage:
    """Write a ``queued`` outbox row + dispatch. Body is enforced <= 160 chars."""
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
    _dispatch_sms(row)  # never raises — fail-soft is the contract
    db.flush()  # callers observe the final status
    return row


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
            'to_phone': mask_phone(phone),
            'status': row.status,
            'brand': settings.sms_brand_name,
            'body_length': len(body),
        },
    )
    return row
