"""Surplus wallet ledger (TECH-09 / NB-09.2-9.3, blueprint decision #8).

Imports models + audit ONLY — deliberately no lifecycle/invoices import,
breaking the potential import cycle (invoices -> wallet is the one-way
edge; wallet never imports back).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.wallet_credit import WalletCredit
from app.services.audit import record_audit_event
from app.services.billing.money import quantize_money

_WALLET_NOTIFICATION_EXPIRY_DAYS = 3


def create_wallet_credit(db: Session, org: Organization, receipt: PaymentReceipt, amount_etb: Decimal) -> WalletCredit:
    """Record a surplus credit from a verified receipt (available state)."""
    amount = quantize_money(amount_etb)
    credit = WalletCredit(
        organization_id=org.id,
        receipt_id=receipt.id,
        amount_etb=amount,
        status='available',
    )
    db.add(credit)
    return credit


def available_wallet_credit(db: Session, org: Organization) -> Decimal:
    """Sum of not-yet-applied wallet credits (FIFO pool)."""
    total = db.execute(
        select(WalletCredit.amount_etb).where(
            WalletCredit.organization_id == org.id,
            WalletCredit.status == 'available',
        )
    ).scalars().all()
    return quantize_money(sum(total, Decimal('0.00')))


def apply_available_wallet_credits(
    db: Session, org: Organization, invoice: SubscriptionInvoice, total_etb: Decimal
) -> tuple[Decimal, Decimal]:
    """Apply available credits FIFO (oldest first) against a fresh invoice.

    Returns ``(applied, remaining_available)``. Application is floored at
    ``total_etb``: any excess stays ``available`` and rolls to the invoice
    after that (blueprint decision #8).
    """
    remaining = quantize_money(total_etb)
    applied = Decimal('0.00')
    rows = db.execute(
        select(WalletCredit)
        .where(
            WalletCredit.organization_id == org.id,
            WalletCredit.status == 'available',
        )
        .order_by(WalletCredit.created_at.asc())
    ).scalars().all()
    for row in rows:
        if remaining <= 0:
            break
        if row.amount_etb <= remaining:
            row.status = 'applied'
            row.applied_to_invoice_id = invoice.id
            row.applied_at = datetime.now(UTC)
            db.add(row)
            applied += row.amount_etb
            remaining -= row.amount_etb
        else:
            # Single credit exceeding the invoice total: apply only what the
            # invoice needs and roll the excess forward as a NEW available
            # row (blueprint decision #8 — excess stays available, FIFO).
            excess = quantize_money(row.amount_etb - remaining)
            row.status = 'applied'
            row.applied_to_invoice_id = invoice.id
            row.applied_at = datetime.now(UTC)
            db.add(row)
            db.add(
                WalletCredit(
                    organization_id=org.id,
                    receipt_id=row.receipt_id,
                    amount_etb=excess,
                    status='available',
                )
            )
            applied += remaining
            remaining = Decimal('0.00')
    # Flush BEFORE recomputing the pool so callers' audit payloads and any
    # follow-up queries see the applied state (autoflush is off).
    db.flush()
    return quantize_money(applied), available_wallet_credit(db, org)


def void_wallet_credits_for_receipt(
    db: Session, org: Organization, receipt: PaymentReceipt, reversal_kind: str = 'undo'
) -> Decimal:
    """Void every AVAILABLE wallet credit for the receipt (decision #5).

    Deliberate asymmetry: rows already ``applied`` to a later invoice are
    LEFT UNTOUCHED — unwinding a consumed credit would mutate a different
    invoice than the reversed one (NB-20.5 limits reversal effects to the
    reversed invoice's balance and the lock state). ``available_wallet_credit``
    recomputes correctly because it filters ``status == 'available'``, and
    the customer wallet list surfaces the voided rows with their status.
    Audits ``wallet.voided``; returns the voided total.
    """
    rows = db.execute(
        select(WalletCredit).where(
            WalletCredit.organization_id == org.id,
            WalletCredit.receipt_id == receipt.id,
            WalletCredit.status == 'available',
        )
    ).scalars().all()
    total = Decimal('0.00')
    for row in rows:
        row.status = 'voided'
        row.voided_at = datetime.now(UTC)
        db.add(row)
        total += row.amount_etb
    total = quantize_money(total)
    if rows:
        record_audit_event(
            db,
            event_type='wallet.voided',
            entity_type='payment_receipt',
            entity_id=receipt.id,
            organization_id=org.id,
            description=f'Voided {len(rows)} available wallet credit(s) for receipt {receipt.reference_number or receipt.id}',
            payload={'receipt_id': str(receipt.id), 'amount_etb': str(total), 'reversal_kind': reversal_kind},
        )
    return total


def _wallet_notification(db: Session, org: Organization, amount_etb: Decimal) -> Notification:
    """In-product wallet banner (NB-09.2 copy)."""
    notification = Notification(
        organization_id=org.id,
        kind='wallet_credit',
        title='Wallet credit',
        message=f'Wallet balance: +{quantize_money(amount_etb)} ETB applies to next invoice.',
        payload={'amount_etb': str(quantize_money(amount_etb))},
        expires_at=datetime.now(UTC) + timedelta(days=_WALLET_NOTIFICATION_EXPIRY_DAYS),
    )
    db.add(notification)
    return notification
