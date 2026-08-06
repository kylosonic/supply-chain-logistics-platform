"""AI-assisted receipt extraction (TECH-10 / NB-10).

Provider-agnostic interface with a BYOK resolution chain and a
zero-confidence fallback. Phase 2 ships exactly ONE adapter (``mock``,
deterministic and controlled by ``settings.receipt_extraction_mode``);
real HTTP provider adapters are a NON-GOAL — the interface, key plumbing
and fallback are real, the wire call is not (blueprint decision #7).

Imports models + audit + ``security.decrypt_provider_key`` only — no
billing-internal imports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.provider_key import ProviderApiKey
from app.models.receipt_extraction import ReceiptExtraction
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.security import decrypt_provider_key

EXTRACTION_FIELDS = (
    'sender_name',
    'sender_account_number',
    'receiver_account_number',
    'receiver_name',
    'transfer_amount',
    'transfer_date',
    'reference_number',
    'bank_identifier',
)

LOW_CONFIDENCE_THRESHOLD = 0.60

ZERO_CONFIDENCE_WARNING = (
    'No AI provider key set on this organization — extraction will be returned '
    'at zero confidence; admin must manually read the receipt.'
)


class ProviderAdapterError(Exception):
    """Adapter missing or malformed output."""


@dataclass
class ExtractionResult:
    fields: dict[str, str | None]
    confidence: dict[str, float]
    provider_name: str | None
    key_id: str | None
    model_name: str | None
    has_key: bool
    error: str | None = None
    raw_response: dict | None = field(default_factory=dict)


def _empty_result(*, has_key: bool, error: str | None = None) -> ExtractionResult:
    return ExtractionResult(
        fields={name: None for name in EXTRACTION_FIELDS},
        confidence={name: 0.0 for name in EXTRACTION_FIELDS},
        provider_name=None,
        key_id=None,
        model_name=None,
        has_key=has_key,
        error=error,
    )


def resolve_extraction_key(db: Session, org: Organization) -> ProviderApiKey | None:
    """The org's preferred key, only when it is org-owned and active."""
    if not org.preferred_ai_key_id:
        return None
    key = db.get(ProviderApiKey, org.preferred_ai_key_id)
    if key is None or key.organization_id != org.id or key.status != 'active':
        return None
    return key


def extract_receipt(
    db: Session,
    org: Organization,
    receipt: PaymentReceipt,
    content_bytes: bytes,
    user: User | None,
    mock_extraction: dict | None = None,
) -> ExtractionResult:
    """Orchestrate BYOK resolution, adapter dispatch, fallback, persistence
    and audit. Never raises: extraction failures degrade to zero confidence
    (NB-10.2) and can never fail an upload."""
    key = resolve_extraction_key(db, org)
    result: ExtractionResult
    if key is None:
        result = _empty_result(has_key=False, error='no_ai_key')
    else:
        try:
            raw = _extract_with_provider(
                key.provider_name,
                decrypt_provider_key(key.encrypted_key),
                content_bytes,
                mock_extraction=mock_extraction,
            )
            fields, confidence, model_name = _validate_adapter_output(raw)
            result = ExtractionResult(
                fields=fields,
                confidence=confidence,
                provider_name=key.provider_name,
                key_id=key.id,
                model_name=model_name,
                has_key=True,
                raw_response=raw,
            )
        except (ProviderAdapterError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
            result = _empty_result(has_key=True, error=str(exc))

    row = ReceiptExtraction(
        receipt_id=receipt.id,
        provider_name=result.provider_name,
        key_id=result.key_id,
        model_name=result.model_name,
        fields=result.fields,
        confidence={name: float(value) for name, value in result.confidence.items()},
        raw_response=result.raw_response,
        error_message=result.error,
    )
    db.add(row)
    record_audit_event(
        db,
        event_type='receipts.extraction_completed',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=user,
        organization_id=org.id,
        description=f'Extraction completed for receipt {receipt.id}',
        payload={
            'provider_name': result.provider_name,
            'key_id': result.key_id,
            'has_key': result.has_key,
            'low_confidence_fields': [
                name for name in EXTRACTION_FIELDS if result.confidence[name] < LOW_CONFIDENCE_THRESHOLD
            ],
            'confidence_summary': {name: round(result.confidence[name], 2) for name in EXTRACTION_FIELDS},
            'error': result.error,
        },
    )
    return result


def _extract_with_provider(
    provider_name: str,
    api_key: str,
    content_bytes: bytes,
    *,
    mock_extraction: dict | None = None,
) -> dict:
    """Adapter registry dispatch. Unknown providers raise
    ``ProviderAdapterError`` -> zero-confidence fallback upstream."""
    if provider_name == 'mock':
        return _mock_adapter(content_bytes, mock_extraction)
    raise ProviderAdapterError(f'No extraction adapter registered for provider {provider_name!r}')


def _mock_adapter(content_bytes: bytes, mock_extraction: dict | None) -> dict:
    """Deterministic dev/test adapter (settings.receipt_extraction_mode).

    Mock mode parses the ``mock_extraction`` JSON sidecar when present;
    an absent or unparseable sidecar returns an EMPTY dict -> zero
    confidence (blueprint §2.2). Used ONLY in dev/test.
    """
    if settings.receipt_extraction_mode != 'mock':
        raise ProviderAdapterError('mock adapter disabled by receipt_extraction_mode')
    if not mock_extraction:
        raise ProviderAdapterError('mock_extraction sidecar missing')
    raw = dict(mock_extraction)
    if isinstance(raw.get('fields'), dict) and isinstance(raw.get('confidence'), dict):
        return raw
    raise ProviderAdapterError('malformed mock_extraction sidecar')


def _validate_adapter_output(raw: dict) -> tuple[dict, dict, str | None]:
    """Normalize adapter output: exactly the 8 keys + per-field confidence."""
    fields: dict = {}
    confidence: dict = {}
    model_name = raw.get('model_name')
    for name in EXTRACTION_FIELDS:
        if name not in raw.get('fields', {}):
            raise ProviderAdapterError(f'adapter output missing field {name!r}')
        value = raw['fields'][name]
        fields[name] = str(value) if value is not None else None
    for name in EXTRACTION_FIELDS:
        value = raw.get('confidence', {}).get(name, 0.0)
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ProviderAdapterError(f'adapter confidence for {name!r} is not numeric') from exc
        if not 0.0 <= score <= 1.0:
            raise ProviderAdapterError(f'adapter confidence for {name!r} out of range')
        confidence[name] = score
    return fields, confidence, model_name
