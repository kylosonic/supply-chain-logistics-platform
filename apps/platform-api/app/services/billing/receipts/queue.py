"""Read surfaces: customer receipt history, the admin verification queue,
queue-item payload building and the wallet view (TECH-07/09).

Imports: models + ``intake.recommended_verdict`` + ``receipt_extraction``
constants only — one-directional (``queue`` is never imported by the other
package modules).
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dispute_thread import DisputeThread
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.receipt_extraction import ReceiptExtraction
from app.models.wallet_credit import WalletCredit
from app.services.billing.receipt_extraction import (
    EXTRACTION_FIELDS,
    ZERO_CONFIDENCE_WARNING,
)
from app.services.billing.receipts.intake import recommended_verdict


def list_customer_receipts(db: Session, org: Organization) -> list[PaymentReceipt]:
    return list(
        db.execute(
            select(PaymentReceipt)
            .where(PaymentReceipt.organization_id == org.id)
            .order_by(PaymentReceipt.created_at.desc())
        ).scalars()
    )


def list_queue(db: Session) -> list[PaymentReceipt]:
    """Queue = pending + escalated, oldest first. Unrouteable uploads never
    appear here: the upload endpoint rolls them back before commit."""
    return list(
        db.execute(
            select(PaymentReceipt)
            .where(PaymentReceipt.status.in_(['pending', 'escalated']))
            .order_by(PaymentReceipt.created_at.asc())
        ).scalars()
    )


def get_queue_item(db: Session, receipt_id: str) -> PaymentReceipt | None:
    return db.get(PaymentReceipt, receipt_id)


def queue_item_payload(db: Session, receipt: PaymentReceipt) -> dict:
    """Build the admin queue-item dict (schema: ReceiptQueueItemRead)."""
    extraction = db.execute(
        select(ReceiptExtraction).where(ReceiptExtraction.receipt_id == receipt.id)
    ).scalar_one_or_none()
    field_columns = {
        'sender_name': receipt.sender_name,
        'sender_account_number': receipt.sender_account_number,
        'receiver_account_number': receipt.receiver_account_number,
        'receiver_name': receipt.receiver_name,
        'transfer_amount': str(receipt.amount_etb) if receipt.amount_etb is not None else None,
        'transfer_date': str(receipt.transfer_date) if receipt.transfer_date else None,
        'reference_number': receipt.reference_number,
        'bank_identifier': receipt.bank_code,
    }
    if extraction is not None:
        fields = {name: extraction.fields.get(name) for name in EXTRACTION_FIELDS}
        confidence = {name: float(extraction.confidence.get(name, 0.0)) for name in EXTRACTION_FIELDS}
    else:
        fields = field_columns
        confidence = {name: 0.0 for name in EXTRACTION_FIELDS}

    org = db.get(Organization, receipt.organization_id)
    thread = db.execute(
        select(DisputeThread).where(DisputeThread.receipt_id == receipt.id)
    ).scalar_one_or_none()
    invoice = receipt.invoice

    return {
        'id': receipt.id,
        'organization_id': receipt.organization_id,
        'organization_name': org.name if org else '',
        'invoice_number': invoice.invoice_number if invoice else None,
        'designated_bank_code': invoice.designated_account.bank_code if invoice else None,
        'status': receipt.status,
        'verdict': receipt.verdict,
        'extracted_fields': fields,
        'confidence': confidence,
        'low_confidence_fields': receipt.low_confidence_fields or [],
        'is_new_sender': receipt.is_new_sender,
        'is_cash_sender': receipt.is_cash_sender,
        'is_wrong_bank_within_portfolio': receipt.is_wrong_bank_within_portfolio,
        'is_large_surplus': receipt.is_large_surplus,
        'is_duplicate': receipt.is_duplicate,
        'has_zero_confidence': receipt.has_zero_confidence,
        'zero_confidence_warning': ZERO_CONFIDENCE_WARNING if receipt.has_zero_confidence else None,
        'recommended_verdict': recommended_verdict(db, receipt, invoice),
        'surplus_etb': receipt.surplus_etb,
        'large_surplus_decision': receipt.large_surplus_decision,
        'partial_credit_amount_etb': receipt.partial_credit_amount_etb,
        'trusted_payer_action': receipt.trusted_payer_action,
        'admin_note': receipt.admin_note,
        'dispute_text': thread.dispute_text if thread else None,
        'dispute_status': thread.status if thread else None,
        'file_name': receipt.file_name,
        'content_type': receipt.content_type,
        'file_size_bytes': receipt.file_size_bytes,
        'created_at': receipt.created_at,
    }


def list_wallet(db: Session, org: Organization) -> tuple[Decimal, list[WalletCredit]]:
    from app.services.billing.wallet import available_wallet_credit

    credits_rows = list(
        db.execute(
            select(WalletCredit)
            .where(WalletCredit.organization_id == org.id)
            .order_by(WalletCredit.created_at.desc())
        ).scalars()
    )
    return available_wallet_credit(db, org), credits_rows
