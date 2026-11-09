"""Pure pricing constants and date math for subscription billing.

No database access — this module is the single source of truth for the
locked ETB tier ladder (TECH-01 / NB-01) and billing-period arithmetic.

Import map: ``services.billing.pricing`` imports nothing app-internal.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

# Locked tier ladder

TIER_SPECS: dict[str, dict] = {
    'free': {
        'title': 'Free',
        'flat_price_etb': Decimal('0.00'),
        'billing_cycle': None,
        'included_units': {'delivery_tasks': 2500, 'route_optimizations': 50},
        'overage_rate_etb': {'delivery_tasks': None, 'route_optimizations': None},
        'trial_duration_hours': None,
    },
    'starter': {
        'title': 'Starter',
        'flat_price_etb': Decimal('4500.00'),
        'billing_cycle': 'monthly',
        'included_units': {'delivery_tasks': 2500, 'route_optimizations': 50},
        'overage_rate_etb': {
            'delivery_tasks': Decimal('0.20'),
            'route_optimizations': Decimal('1.50'),
        },
        'trial_duration_hours': 168,
    },
    'scale': {
        'title': 'Scale',
        'flat_price_etb': Decimal('10000.00'),
        'billing_cycle': 'quarterly',
        'included_units': {'delivery_tasks': 5000, 'route_optimizations': 250},
        'overage_rate_etb': {
            'delivery_tasks': Decimal('0.16'),
            'route_optimizations': Decimal('1.00'),
        },
        'trial_duration_hours': 168,
    },
    'enterprise': {
        'title': 'Enterprise',
        'flat_price_etb': Decimal('45000.00'),
        'billing_cycle': 'quarterly',
        'included_units': {'delivery_tasks': None, 'route_optimizations': None},
        'overage_rate_etb': {'delivery_tasks': None, 'route_optimizations': None},
        'trial_duration_hours': 168,
    },
}

PAID_TIERS = ('starter', 'scale', 'enterprise')
TRIAL_DURATION_HOURS = 168
FIRST_INVOICE_GRACE_DAYS = 3
SUBSEQUENT_INVOICE_GRACE_DAYS = 0

OVERAGE_LINE_KIND = {
    'delivery_tasks': 'overage_delivery_tasks',
    'route_optimizations': 'overage_route_optimizations',
}


def flat_price_etb(tier: str) -> Decimal:
    return TIER_SPECS[tier]['flat_price_etb']


def billing_cycle_for(tier: str) -> str | None:
    return TIER_SPECS[tier]['billing_cycle']


def included_units(tier: str, metric: str) -> int | None:
    return TIER_SPECS[tier]['included_units'].get(metric)


def overage_rate_etb(tier: str, metric: str) -> Decimal | None:
    return TIER_SPECS[tier]['overage_rate_etb'].get(metric)


def tier_title(tier: str) -> str:
    return TIER_SPECS[tier]['title']


# Billing-period math


def _first_of_month(d: date) -> date:
    return d.replace(day=1)


def _last_of_month(d: date) -> date:
    next_month = (_first_of_month(d).replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _quarter_bounds(d: date) -> tuple[date, date]:
    quarter_month = ((d.month - 1) // 3) * 3 + 1
    start = date(d.year, quarter_month, 1)
    if quarter_month == 10:
        end = date(d.year, 12, 31)
    else:
        end = date(d.year, quarter_month + 3, 1) - timedelta(days=1)
    return start, end


def period_for_tier(tier: str, anchor: date) -> tuple[date, date]:
    """Return the billing period containing ``anchor`` for the tier's cycle."""
    cycle = billing_cycle_for(tier)
    if cycle == 'quarterly':
        return _quarter_bounds(anchor)
    return _first_of_month(anchor), _last_of_month(anchor)


def next_period_start_after(anchor: date, cycle: str | None) -> date:
    """First day of the next billing period strictly after ``anchor``."""
    if cycle == 'quarterly':
        start, _ = _quarter_bounds(anchor)
        if anchor >= start:
            if start.month == 10:
                return date(start.year + 1, 1, 1)
            return date(start.year, start.month + 3, 1)
        return start
    next_month = (_first_of_month(anchor).replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month


def trial_period(start: datetime, hours: int = TRIAL_DURATION_HOURS) -> tuple[datetime, datetime]:
    """Return the (start, end) of a trial anchored at ``start``.

    Trials last exactly 168 hours (7 days) — NB-03.1.
    """
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    return start, start + timedelta(hours=hours)


def grace_days_for(invoice_ordinal: int) -> int:
    """3 days on the customer's first invoice ever, 0 on subsequent (NB-06)."""
    if invoice_ordinal <= 1:
        return FIRST_INVOICE_GRACE_DAYS
    return SUBSEQUENT_INVOICE_GRACE_DAYS
