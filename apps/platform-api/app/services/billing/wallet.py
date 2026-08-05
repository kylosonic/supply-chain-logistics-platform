"""Surplus wallet ledger (TECH-09 / NB-09.2-9.3, blueprint decision #8).

Imports models + audit ONLY — deliberately no lifecycle/invoices import,
breaking the potential import cycle (invoices -> wallet is the one-way
edge; wallet never imports back).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.wallet_credit import WalletCredit

_WALLET_NOTIFICATION_EXPIRY_DAYS = 3


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def create_wallet_credit(db: Session, org: Organization, receipt: PaymentReceipt, amount_etb: Decimal) -> WalletCredit:
    """Record a surplus credit from a verified receipt (available state)."""
    amount = _q(amount_etb)
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
    return _q(sum(total, Decimal('0.00')))


def apply_available_wallet_credits(
    db: Session, org: Organization, invoice: SubscriptionInvoice, total_etb: Decimal
) -> tuple[Decimal, Decimal]:
    """Apply available credits FIFO (oldest first) against a fresh invoice.

    Returns ``(applied, remaining_available)``. Application is floored at
    ``total_etb``: any excess stays ``available`` and rolls to the invoice
    after that (blueprint decision #8).
    """
    remaining = _q(total_etb)
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
            excess = _q(row.amount_etb - remaining)
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
    return _q(applied), available_wallet_credit(db, org)


def _wallet_notification(db: Session, org: Organization, amount_etb: Decimal) -> Notification:
    """In-product wallet banner (NB-09.2 copy)."""
    notification = Notification(
        organization_id=org.id,
        kind='wallet_credit',
        title='Wallet credit',
        message=f'Wallet balance: +{_q(amount_etb)} ETB applies to next invoice.',
        payload={'amount_etb': str(_q(amount_etb))},
        expires_at=datetime.now(UTC) + timedelta(days=_WALLET_NOTIFICATION_EXPIRY_DAYS),
    )
    db.add(notification)
    return notification
