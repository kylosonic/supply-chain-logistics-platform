from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.services.billing.pricing import (
    TIER_SPECS,
    billing_cycle_for,
    flat_price_etb,
    grace_days_for,
    included_units,
    next_period_start_after,
    overage_rate_etb,
    period_for_tier,
    trial_period,
)


def test_flat_prices_locked():
    assert flat_price_etb('starter') == Decimal('4500.00')
    assert flat_price_etb('scale') == Decimal('10000.00')
    assert flat_price_etb('enterprise') == Decimal('45000.00')
    assert flat_price_etb('free') == Decimal('0.00')


def test_billing_cycles():
    assert billing_cycle_for('starter') == 'monthly'
    assert billing_cycle_for('scale') == 'quarterly'
    assert billing_cycle_for('enterprise') == 'quarterly'
    assert billing_cycle_for('free') is None


def test_monthly_period_math():
    start, end = period_for_tier('starter', date(2026, 8, 5))
    assert start == date(2026, 8, 1)
    assert end == date(2026, 8, 31)


def test_quarterly_period_math():
    start, end = period_for_tier('scale', date(2026, 8, 5))
    assert start == date(2026, 7, 1)
    assert end == date(2026, 9, 30)


def test_next_period_start_monthly():
    assert next_period_start_after(date(2026, 8, 5), 'monthly') == date(2026, 9, 1)
    assert next_period_start_after(date(2026, 8, 1), 'monthly') == date(2026, 9, 1)
    assert next_period_start_after(date(2026, 12, 15), 'monthly') == date(2027, 1, 1)


def test_next_period_start_quarterly():
    assert next_period_start_after(date(2026, 8, 5), 'quarterly') == date(2026, 10, 1)
    assert next_period_start_after(date(2026, 6, 30), 'quarterly') == date(2026, 7, 1)
    assert next_period_start_after(date(2026, 12, 31), 'quarterly') == date(2027, 1, 1)


def test_grace_days_first_vs_subsequent():
    assert grace_days_for(1) == 3
    assert grace_days_for(2) == 0
    assert grace_days_for(5) == 0


def test_free_tier_quotas_no_overage():
    assert included_units('free', 'delivery_tasks') == 2500
    assert included_units('free', 'route_optimizations') == 50
    assert overage_rate_etb('free', 'delivery_tasks') is None
    assert overage_rate_etb('free', 'route_optimizations') is None


def test_included_units_and_overage_rates_match_metering():
    assert included_units('starter', 'delivery_tasks') == 2500
    assert included_units('starter', 'route_optimizations') == 50
    assert overage_rate_etb('starter', 'delivery_tasks') == Decimal('0.20')
    assert overage_rate_etb('starter', 'route_optimizations') == Decimal('1.50')
    assert included_units('scale', 'delivery_tasks') == 5000
    assert included_units('scale', 'route_optimizations') == 250
    assert overage_rate_etb('scale', 'delivery_tasks') == Decimal('0.16')
    assert overage_rate_etb('scale', 'route_optimizations') == Decimal('1.00')
    assert included_units('enterprise', 'delivery_tasks') is None


def test_trial_period_is_168_hours():
    start = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    trial_start, trial_end = trial_period(start)
    assert trial_start == start
    assert trial_end == start + timedelta(hours=168)
    assert trial_end - trial_start == timedelta(hours=168)


def test_tier_specs_are_decimal():
    for tier, spec in TIER_SPECS.items():
        if tier == 'free':
            continue
        assert isinstance(spec['flat_price_etb'], Decimal)
        for metric, rate in spec['overage_rate_etb'].items():
            if rate is not None:
                assert isinstance(rate, Decimal)
