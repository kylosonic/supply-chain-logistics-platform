"""Invoice persistence and composition (TECH-01, TECH-02, TECH-05).

Chain: pricing (pure) -> invoices (persistence) -> lifecycle (state engine).
No scheduler exists — issuance is lazy via ``try_issue_invoice`` at every
guard evaluation / billing-state read, with at-most-once enforced by the
unique constraint ``uq_subscription_invoice_org_period``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.billing_counter import BillingCounter
from app.models.collection_account import CollectionAccount
from app.models.invoice_line_item import InvoiceLineItem
from app.models.notification import Notification
from app.models.organization import Organization
from app.models.subscription_invoice import SubscriptionInvoice
from app.models.trial_record import TrialRecord
from app.models.usage_meter import OrganizationUsageCounter
from app.services.audit import record_audit_event
from app.services.billing import pricing, wallet
from app.services.billing.money import quantize_money

_INVOICE_WARNING_EXPIRY_DAYS = 3


def designate_account(db: Session, org: Organization, ordinal: int) -> CollectionAccount:
    """Per-org rotation: the org's Nth invoice -> accounts[(N-1) % 2].

    First invoice is always CBE, second Dashen (NB-02.3). Only
    ``bank_code in {'cbe','dashen'}`` and ``is_active = true`` are eligible
    (NB-02.4).
    """
    accounts = db.execute(
        select(CollectionAccount)
        .where(CollectionAccount.is_active.is_(True))
        .order_by(CollectionAccount.bank_code)
    ).scalars().all()
    eligible = [account for account in accounts if account.bank_code in {'cbe', 'dashen'}]
    if len(eligible) < 2:
        raise ValueError('Both CBE and Dashen collection accounts must be active to issue invoices')
    return eligible[(ordinal - 1) % 2]


def next_invoice_number(db: Session) -> str:
    """Monotonic invoice number from the single-row ``billing_counters``."""
    counter = db.get(BillingCounter, 1)
    if counter is None:
        counter = BillingCounter(id=1, last_value=0)
        db.add(counter)
        db.flush()
    counter.last_value += 1
    db.flush()
    return f'INV-{counter.last_value:06d}'


def _trial_anchor(db: Session, org: Organization) -> TrialRecord | None:
    return db.execute(
        select(TrialRecord)
        .where(TrialRecord.organization_id == org.id)
        .order_by(TrialRecord.started_at.desc())
    ).scalars().first()


def _as_date(value: datetime | date) -> date:
    return value.date() if isinstance(value, datetime) else value


def _overage_units(
    db: Session, org: Organization, tier: str, window_start: datetime | date, window_end: datetime | date
) -> dict[str, int]:
    """Overage units per metric over counters overlapping the window.

    ``max(0, sum(used over overlapping counters) - tier_quota_for_billing_cycle)``
    (blueprint decision #6). Enterprise has no quota -> never returns
    overage (NB-01.4).
    """
    overage: dict[str, int] = {}
    for metric in ('delivery_tasks', 'route_optimizations'):
        included = pricing.included_units(tier, metric)
        if included is None:
            continue
        rows = db.execute(
            select(OrganizationUsageCounter).where(
                OrganizationUsageCounter.organization_id == org.id,
                OrganizationUsageCounter.metric == metric,
                OrganizationUsageCounter.period_start <= _as_date(window_end),
                OrganizationUsageCounter.period_end >= _as_date(window_start),
            )
        ).scalars().all()
        used = sum(row.used_units for row in rows)
        excess = max(0, used - included)
        if excess > 0:
            overage[metric] = excess
    return overage


def _build_warning_notification(db: Session, invoice: SubscriptionInvoice, now: datetime) -> Notification:
    """3-day warning fired at issuance (NB-05): invoice number, flat amount,
    designated bank, due date. In-product only; persists for 3 days."""
    account = db.get(CollectionAccount, invoice.designated_account_id)
    if account is None:
        raise ValueError(f'Designated collection account {invoice.designated_account_id} missing')
    notification = Notification(
        organization_id=invoice.organization_id,
        kind='invoice_warning',
        title=f'Invoice {invoice.invoice_number} issued',
        message=(
            f'Invoice {invoice.invoice_number} for {invoice.total_etb} ETB is due on {invoice.due_date}. '
            f'Pay to {account.bank_name} ({account.account_number}) and upload your receipt.'
        ),
        payload={
            'invoice_number': invoice.invoice_number,
            'amount_etb': str(invoice.total_etb),
            'flat_amount_etb': str(invoice.flat_amount_etb),
            'bank_name': account.bank_name,
            'bank_account': account.account_number,
            'bank_code': account.bank_code,
            'due_date': str(invoice.due_date),
            'grace_ends_at': str(invoice.grace_ends_at),
        },
        expires_at=now + timedelta(days=_INVOICE_WARNING_EXPIRY_DAYS),
    )
    db.add(notification)
    return notification


def _issue_invoice(
    db: Session,
    org: Organization,
    tier: str,
    period_start: date,
    period_end: date,
    overage: dict[str, int],
    ordinal: int,
    now: datetime,
    wallet_credit_etb: Decimal = Decimal('0.00'),
) -> SubscriptionInvoice:
    flat = pricing.flat_price_etb(tier)
    account = designate_account(db, org, ordinal)
    grace_days = pricing.grace_days_for(ordinal)
    due_date = period_start
    invoice = SubscriptionInvoice(
        organization_id=org.id,
        invoice_number=next_invoice_number(db),
        tier=tier,
        billing_period_start=period_start,
        billing_period_end=period_end,
        flat_amount_etb=flat,
        total_etb=flat,
        balance_remaining_etb=flat,
        due_date=due_date,
        grace_days=grace_days,
        grace_ends_at=due_date + timedelta(days=grace_days),
        designated_account_id=account.id,
        status='issued',
    )
    db.add(invoice)
    db.flush()

    invoice.lines = [
        InvoiceLineItem(
            kind='flat',
            description=f'{pricing.tier_title(tier)} subscription flat fee',
            quantity=1,
            unit_price_etb=flat,
            amount_etb=flat,
        )
    ]
    total = flat
    for metric, units in overage.items():
        rate = pricing.overage_rate_etb(tier, metric)
        if rate is None:
            # No overage rate for this metric on this tier — skip the line.
            continue
        amount = quantize_money(Decimal(units) * rate)
        invoice.lines.append(
            InvoiceLineItem(
                kind=pricing.OVERAGE_LINE_KIND[metric],
                description=f'Overage - {metric}',
                quantity=units,
                unit_price_etb=rate,
                amount_etb=amount,
            )
        )
        total = total + amount

    # Wallet credit reduces the TOTAL (and balance), never the flat amount;
    # carried as a negative line so the math stays legible (decision #8).
    # Floored at 0; excess wallet stays available and rolls to the next invoice.
    if wallet_credit_etb > 0:
        applied = min(wallet_credit_etb, total)
        invoice.lines.append(
            InvoiceLineItem(
                kind='wallet_credit',
                description='Wallet credit applied',
                quantity=None,
                unit_price_etb=None,
                amount_etb=-applied,
            )
        )
        total = max(Decimal('0.00'), total - applied)
    invoice.total_etb = total
    invoice.balance_remaining_etb = total
    db.add_all(invoice.lines)

    _build_warning_notification(db, invoice, now)
    record_audit_event(
        db,
        event_type='billing.invoice_issued',
        entity_type='subscription_invoice',
        entity_id=invoice.id,
        organization_id=org.id,
        description=f'Issued {invoice.invoice_number} for {org.name}',
        payload={
            'invoice_number': invoice.invoice_number,
            'tier': tier,
            'total_etb': str(total),
            'flat_amount_etb': str(flat),
            'period_start': str(period_start),
            'period_end': str(period_end),
            'designated_account': account.bank_code,
            'grace_days': grace_days,
            'wallet_credit_etb': str(wallet_credit_etb),
        },
    )
    return invoice


def issue_first_invoice(db: Session, org: Organization, now: datetime) -> SubscriptionInvoice:
    """First invoice = trial-end anchor (blueprint decision #4).

    Billed in advance for the upcoming period; ``due_date = period_start``;
    includes trial-period overage; 3-day grace (first invoice ever).
    """
    anchor_rec = _trial_anchor(db, org)
    if anchor_rec is None:
        raise ValueError('No trial record; cannot issue the first invoice')
    anchor = anchor_rec.ended_at or anchor_rec.started_at + timedelta(hours=pricing.TRIAL_DURATION_HOURS)
    cycle = pricing.billing_cycle_for(anchor_rec.tier)
    if not cycle:
        raise ValueError(f'No billing cycle for tier {anchor_rec.tier!r}')
    period_start = pricing.next_period_start_after(anchor.date(), cycle)
    period_end = pricing.period_for_tier(anchor_rec.tier, period_start)[1]
    overage = _overage_units(db, org, anchor_rec.tier, anchor_rec.started_at, anchor)
    return _issue_invoice(db, org, anchor_rec.tier, period_start, period_end, overage, ordinal=1, now=now)


def issue_next_invoice(db: Session, org: Organization, now: datetime) -> SubscriptionInvoice:
    """Second and every subsequent invoice: 0-day grace (NB-06.2), account
    rotation continues, overage from the prior paid period. Available
    wallet credits reduce the new total at issuance (blueprint decision #8);
    rows are marked applied FIFO."""
    last = _latest_invoice(db, org)
    if last is None:
        raise ValueError('No prior invoice; use issue_first_invoice')
    period_start = last.billing_period_end + timedelta(days=1)
    start, end = pricing.period_for_tier(last.tier, period_start)
    count = db.execute(
        select(SubscriptionInvoice.id).where(SubscriptionInvoice.organization_id == org.id)
    ).scalars().all()
    ordinal = len(count) + 1
    overage = _overage_units(db, org, last.tier, last.billing_period_start, last.billing_period_end)

    flat = pricing.flat_price_etb(last.tier)
    pre_wallet_total = flat
    for metric, units in overage.items():
        rate = pricing.overage_rate_etb(last.tier, metric)
        if rate is None:
            continue
        pre_wallet_total = pre_wallet_total + quantize_money(Decimal(units) * rate)

    available = wallet.available_wallet_credit(db, org)
    wallet_credit_etb = min(available, pre_wallet_total)
    invoice = _issue_invoice(
        db,
        org,
        last.tier,
        start,
        end,
        overage,
        ordinal=ordinal,
        now=now,
        wallet_credit_etb=wallet_credit_etb,
    )
    applied, _remaining = wallet.apply_available_wallet_credits(db, org, invoice, pre_wallet_total)
    record_audit_event(
        db,
        event_type='billing.wallet_applied',
        entity_type='subscription_invoice',
        entity_id=invoice.id,
        organization_id=org.id,
        description=f'Wallet credit applied to {invoice.invoice_number}',
        payload={'invoice_number': invoice.invoice_number, 'wallet_applied_etb': str(applied)},
    )
    return invoice


def try_issue_invoice(db: Session, org: Organization, now: datetime) -> SubscriptionInvoice | None:
    """Lazily issue the first invoice when the trial-end boundary is crossed.

    Free tier never invoices (NB-01.5); no invoice during the trial
    (NB-03.3). At-most-once: the unique constraint
    ``uq_subscription_invoice_org_period`` absorbs concurrent issuance —
    IntegrityError rolls back and the existing invoice is returned.
    """
    if org.subscription_tier == 'free':
        return None
    anchor_rec = _trial_anchor(db, org)
    if anchor_rec is None:
        return None
    anchor = anchor_rec.ended_at or anchor_rec.started_at + timedelta(hours=pricing.TRIAL_DURATION_HOURS)
    cycle = pricing.billing_cycle_for(anchor_rec.tier)
    if not cycle:
        return None
    next_start = pricing.next_period_start_after(anchor.date(), cycle)
    if now.date() < next_start:
        return None

    existing = db.execute(
        select(SubscriptionInvoice).where(
            SubscriptionInvoice.organization_id == org.id,
            SubscriptionInvoice.billing_period_start == next_start,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    try:
        invoice = issue_first_invoice(db, org, now)
        db.commit()
        db.refresh(invoice)
        return invoice
    except IntegrityError:
        db.rollback()
        return db.execute(
            select(SubscriptionInvoice).where(
                SubscriptionInvoice.organization_id == org.id,
                SubscriptionInvoice.billing_period_start == next_start,
            )
        ).scalar_one_or_none()


def _latest_invoice(db: Session, org: Organization) -> SubscriptionInvoice | None:
    return db.execute(
        select(SubscriptionInvoice)
        .where(SubscriptionInvoice.organization_id == org.id)
        .order_by(SubscriptionInvoice.billing_period_start.desc())
        .limit(1)
    ).scalars().first()


def list_invoices(db: Session, org: Organization) -> list[SubscriptionInvoice]:
    return list(
        db.execute(
            select(SubscriptionInvoice)
            .where(SubscriptionInvoice.organization_id == org.id)
            .order_by(SubscriptionInvoice.billing_period_start.desc())
        ).scalars()
    )


def get_invoice(db: Session, org: Organization, invoice_number: str) -> SubscriptionInvoice | None:
    return db.execute(
        select(SubscriptionInvoice).where(
            SubscriptionInvoice.organization_id == org.id,
            SubscriptionInvoice.invoice_number == invoice_number,
        )
    ).scalar_one_or_none()
