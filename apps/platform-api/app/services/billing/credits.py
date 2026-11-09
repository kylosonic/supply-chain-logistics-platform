"""Credit-application core (TECH-08/09/13 — NB-08/09/13).

Chain: credits -> lifecycle -> invoices -> pricing; credits also imports
wallet (wallet imports nothing billing-internal — acyclic).

This module is the ONLY place invoice balances are mutated by receipts.
The credit state machine (blueprint §5) is deterministic and money is
``Decimal`` end-to-end with ``ROUND_HALF_UP`` quantization at every
credit boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.user import User
from app.services.audit import record_audit_event
from app.services.billing import lifecycle, wallet
from app.services.billing.money import quantize_money


class CreditError(Exception):
    """Invariant violation inside the credit-application core."""


@dataclass
class CreditOutcome:
    invoice_number: str
    balance_before_etb: Decimal
    credit_delta_etb: Decimal
    surplus_etb: Decimal
    wallet_credit_etb: Decimal
    invoice_paid: bool
    large_surplus_decision: str | None = None
    partial_credit_amount_etb: Decimal | None = None


def classify_surplus(amount_etb: Decimal, balance_etb: Decimal) -> str:
    """Pure surplus classification (NB-09).

    - 'exact'          amount == balance
    - 'partial'        amount <  balance
    - 'auto_forward'   balance < amount <= balance + 1,000
    - 'large_surplus'  amount >  balance + 1,000
    """
    if amount_etb < balance_etb:
        return 'partial'
    if amount_etb == balance_etb:
        return 'exact'
    tolerance = settings.wallet_auto_forward_tolerance_etb
    if amount_etb <= balance_etb + tolerance:
        return 'auto_forward'
    return 'large_surplus'


def _credit_invoice(db: Session, org: Organization, invoice: SubscriptionInvoice, amount_etb: Decimal) -> None:
    """Mutate balance (quantize ROUND_HALF_UP), set ``status='paid'`` at zero.

    The credit is floored: a credit larger than the remaining balance can
    never push the balance negative (credit_forward/credit_backward).
    """
    new_balance = quantize_money(max(Decimal('0.00'), invoice.balance_remaining_etb - amount_etb))
    invoice.balance_remaining_etb = new_balance
    if new_balance == 0:
        invoice.status = 'paid'
    db.add(invoice)


def _cascade_surplus(
    db: Session, org: Organization, amount_etb: Decimal, first_invoice: SubscriptionInvoice
) -> Decimal:
    """NB-07.3 surplus cascade: remaining credited excess flows to the
    next-oldest open invoice, and so on, applying the NB-09 tolerance rules
    recursively.

    Returns the amount that could not be absorbed by any open invoice
    (0.00 in the common case; the remainder is wallet-bound or audit-logged
    by the caller). Structural helper: at verify time the primary invoice's
    surplus is wallet/audit-bound per blueprint §5, so today this is
    exercised unit-level (multi-invoice coverage).
    """
    remaining = quantize_money(amount_etb)
    invoices = db.execute(
        select(SubscriptionInvoice)
        .where(
            SubscriptionInvoice.organization_id == org.id,
            SubscriptionInvoice.balance_remaining_etb > 0,
        )
        .order_by(SubscriptionInvoice.billing_period_start.asc())
    ).scalars().all()
    for invoice in invoices:
        if remaining <= 0:
            break
        if invoice.id == first_invoice.id:
            continue
        balance = quantize_money(invoice.balance_remaining_etb)
        classification = classify_surplus(remaining, balance)
        if classification in ('partial', 'exact'):
            _credit_invoice(db, org, invoice, remaining)
            remaining = Decimal('0.00')
        elif classification == 'auto_forward':
            _credit_invoice(db, org, invoice, balance)
            remaining = remaining - balance
        else:  # large_surplus: credit the balance and carry the rest forward
            _credit_invoice(db, org, invoice, balance)
            remaining = remaining - balance
    return quantize_money(remaining)


def apply_credit(
    db: Session,
    org: Organization,
    receipt: PaymentReceipt,
    decision: str | None = None,
    *,
    partial_amount: Decimal | None = None,
    admin_user: User | None = None,
    note: str | None = None,
    trusted_payer_action: str | None = None,
) -> CreditOutcome:
    """Apply the receipt amount against the primary invoice (blueprint §5).

    ``decision`` is the large-surplus 3-way (credit_forward /
    credit_backward / partial_ignore) and is REQUIRED when the surplus is
    large; ``partial_amount`` is required for partial_ignore. Validation
    lives in ``receipts.render_verdict``; this module re-checks the
    invariants and raises ``CreditError`` on violation (backstop).
    """
    invoice = db.get(SubscriptionInvoice, receipt.invoice_id)
    if invoice is None:
        raise CreditError('Receipt has no routed invoice to credit')
    if receipt.amount_etb is None:
        raise CreditError('Receipt has no extracted amount to credit')
    amount = quantize_money(receipt.amount_etb)
    balance = quantize_money(invoice.balance_remaining_etb)
    classification = classify_surplus(amount, balance)

    outcome = CreditOutcome(
        invoice_number=invoice.invoice_number,
        balance_before_etb=balance,
        credit_delta_etb=Decimal('0.00'),
        surplus_etb=Decimal('0.00'),
        wallet_credit_etb=Decimal('0.00'),
        invoice_paid=False,
        large_surplus_decision=decision,
        partial_credit_amount_etb=partial_amount,
    )

    if classification in ('partial', 'exact'):
        _credit_invoice(db, org, invoice, amount)
        outcome.credit_delta_etb = amount
    elif classification == 'auto_forward':
        _credit_invoice(db, org, invoice, balance)
        surplus = quantize_money(amount - balance)
        wallet.create_wallet_credit(db, org, receipt, surplus)
        wallet._wallet_notification(db, org, surplus)
        outcome.credit_delta_etb = balance
        outcome.surplus_etb = surplus
        outcome.wallet_credit_etb = surplus
    else:  # large_surplus — admin 3-way decision required
        if decision == 'credit_forward':
            _credit_invoice(db, org, invoice, amount)
            surplus = quantize_money(amount - balance)
            wallet.create_wallet_credit(db, org, receipt, surplus)
            wallet._wallet_notification(db, org, surplus)
            outcome.credit_delta_etb = amount
            outcome.surplus_etb = surplus
            outcome.wallet_credit_etb = surplus
        elif decision == 'credit_backward':
            # Full credit; surplus recorded in the audit payload ONLY
            # (offline refund — blueprint decision #9). No wallet row.
            _credit_invoice(db, org, invoice, amount)
            surplus = quantize_money(amount - balance)
            outcome.credit_delta_etb = amount
            outcome.surplus_etb = surplus
        elif decision == 'partial_ignore':
            if partial_amount is None:
                raise CreditError('partial_ignore requires partial_credit_amount_etb')
            amt = quantize_money(partial_amount)
            if amt <= 0 or amt > min(amount, balance):
                raise CreditError('partial_credit_amount_etb must be within (0, min(amount, balance)]')
            _credit_invoice(db, org, invoice, amt)
            outcome.credit_delta_etb = amt
            outcome.partial_credit_amount_etb = amt
        else:
            raise CreditError('large surplus requires credit_forward, credit_backward, or partial_ignore')

    outcome.invoice_paid = quantize_money(invoice.balance_remaining_etb) == 0

    receipt.status = 'verified'
    receipt.verdict = 'verify'
    receipt.decision_made_by_user_id = admin_user.id if admin_user else None
    receipt.decided_at = datetime.now(UTC)
    receipt.large_surplus_decision = outcome.large_surplus_decision
    receipt.partial_credit_amount_etb = outcome.partial_credit_amount_etb
    db.add(receipt)

    record_audit_event(
        db,
        event_type='receipts.verified',
        entity_type='payment_receipt',
        entity_id=receipt.id,
        actor=admin_user,
        organization_id=org.id,
        description=f'Verified receipt {receipt.reference_number or receipt.id} against {invoice.invoice_number}',
        payload={
            'invoice_number': invoice.invoice_number,
            'reference_number': receipt.reference_number,
            'sender_name': receipt.sender_name,
            'amount_etb': str(amount),
            'balance_before_etb': str(outcome.balance_before_etb),
            'decision': 'verified',
            'credit_delta_etb': str(outcome.credit_delta_etb),
            'note': note,
            'trusted_payer_action': trusted_payer_action,
            'wallet_credit_etb': str(outcome.wallet_credit_etb),
            'large_surplus_decision': outcome.large_surplus_decision,
            'surplus_etb': str(outcome.surplus_etb),
        },
    )
    return outcome


def unlock_evaluation(db: Session, org: Organization, now: datetime | None = None) -> None:
    """Pessimistic unlock: credits only ever take effect here, via the
    Phase 1 state engine (blueprint decision #4, risk note #1 — the
    refresh's internal commit persists credits + wallet + audit together)."""
    reference = now or datetime.now(UTC)
    lifecycle.refresh_workspace_state(db, org, reference)
