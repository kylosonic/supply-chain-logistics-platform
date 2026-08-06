"""AI-assisted receipt extraction (TECH-10 / NB-10).

Provider-agnostic interface with a BYOK resolution chain and a
zero-confidence fallback. PROD-02 ships TWO adapters: ``mock``
(deterministic, dev/test-only, controlled by
``settings.receipt_extraction_mode``) and ``openai`` (generic
OpenAI-compatible chat-completions wire contract — works with OpenAI,
Groq, Together, or any OpenAI-compatible gateway, keyed on
``settings.receipt_extraction_base_url`` + ``receipt_extraction_model``).
Production config validation (``settings.effective_receipt_extraction_mode``)
forces mode ∈ {``real``, ``zero_confidence``}; the zero-confidence admin-queue
workflow is the deliberate fallback.

Imports models + audit + ``security.decrypt_provider_key`` only — no
billing-internal imports. DAG: models(4), core.config, services.audit,
services.security (acyclic; never imports app.api).
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

import httpx
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
    if settings.effective_receipt_extraction_mode == 'zero_confidence':
        # PROD-02: deliberate fallback mode — resolve the org key (for audit
        # `has_key` truth) but NEVER call the provider; the admin queue
        # manual-review workflow handles the receipt.
        result = _empty_result(has_key=key is not None, error='zero_confidence_mode')
    elif key is None:
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
    if provider_name == 'openai':
        return _openai_compatible_adapter(content_bytes, api_key)
    raise ProviderAdapterError(f'No extraction adapter registered for provider {provider_name!r}')


def _sniff_mime(content_bytes: bytes) -> str:
    """MIME from magic bytes: PNG/JPEG/PDF, else octet-stream."""
    if content_bytes.startswith(b'\x89PNG'):
        return 'image/png'
    if content_bytes.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if content_bytes.startswith(b'%PDF'):
        return 'application/pdf'
    return 'application/octet-stream'


def _post_chat_completion(url: str, api_key: str, payload: dict) -> dict:
    """Chat-completions POST seam (monkeypatchable in tests). Any transport
    failure, non-2xx, or non-JSON body raises ``ProviderAdapterError`` so the
    upstream zero-confidence fallback always handles it."""
    try:
        response = httpx.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=30.0,
        )
    except httpx.HTTPError as exc:
        raise ProviderAdapterError(f'chat-completions HTTP error: {exc}') from exc
    if response.status_code >= 300:
        raise ProviderAdapterError(f'chat-completions returned HTTP {response.status_code}')
    try:
        return response.json()
    except ValueError as exc:
        raise ProviderAdapterError(f'chat-completions returned non-JSON body: {exc}') from exc


def _openai_compatible_adapter(content_bytes: bytes, api_key: str) -> dict:
    """Generic OpenAI-compatible chat-completions adapter (PROD-02).

    Sends the receipt as a base64 data URI (MIME-sniffed) with a strict-JSON
    system prompt; parses ``choices[0].message.content`` into the canonical
    8-field + per-field-confidence contract. Never requires ``response_format``
    so endpoints without JSON-mode support still work. Missing keys, malformed
    JSON, or transport errors raise ``ProviderAdapterError``.
    """
    mime = _sniff_mime(content_bytes)
    data_uri = f'data:{mime};base64,{base64.b64encode(content_bytes).decode("ascii")}'
    payload = {
        'model': settings.receipt_extraction_model,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You extract bank-transfer receipt data into strict JSON with exactly '
                    f'the keys: {", ".join(EXTRACTION_FIELDS)}. Include a "confidence" object '
                    'mapping every key to a confidence value between 0 and 1. '
                    'Respond with only the JSON object, no prose.'
                ),
            },
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'Extract the receipt fields from this image.'},
                    {'type': 'image_url', 'image_url': {'url': data_uri}},
                ],
            },
        ],
    }
    url = f'{settings.receipt_extraction_base_url.rstrip("/")}/chat/completions'
    response = _post_chat_completion(url, api_key, payload)
    try:
        content = response['choices'][0]['message']['content']
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderAdapterError(f'malformed chat-completions response: {exc}') from exc
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ProviderAdapterError(f'chat-completions content is not JSON: {exc}') from exc
    missing = [name for name in EXTRACTION_FIELDS if name not in parsed]
    if missing:
        raise ProviderAdapterError(f'adapter output missing field {missing[0]!r}')
    fields = {name: parsed[name] for name in EXTRACTION_FIELDS}
    conf = parsed.get('confidence')
    confidence = {
        name: float(conf[name]) if isinstance(conf, dict) and name in conf else 0.0
        for name in EXTRACTION_FIELDS
    }
    return {
        'fields': fields,
        'confidence': confidence,
        'model_name': response.get('model'),
    }


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
