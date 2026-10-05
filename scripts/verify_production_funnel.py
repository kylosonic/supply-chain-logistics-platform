#!/usr/bin/env python3
"""Production funnel verification for FreightPilot.

Walks the exact journey a brand-new Ethiopian logistics operator takes, against a
live deployment, and reports PASS/FAIL per step with the observed value. Written
for the pre-presentation check: it answers "if I demo this on stage right now,
where does it break?"

It is deliberately stdlib-only (no `requests`) so it runs on a bare Python
install, and it never asserts silently -- every step prints what it actually saw.

Usage
-----
    python scripts/verify_production_funnel.py
    python scripts/verify_production_funnel.py --base-url http://localhost:8000
    python scripts/verify_production_funnel.py --keep-going

Exit code is 0 only when every step passed.

NOTE: this script performs real writes. Against production it creates a genuine
free-tier workspace (a company, an owner user, seeded sample data, one route
plan, one driver, one shipment and one cash record). That is intentional -- a
pre-warmed demo workspace is a useful by-product -- but it does mean repeated
runs leave repeated companies behind. Each run's company name is stamped with a
UTC timestamp so they are identifiable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

DEFAULT_BASE_URL = 'https://platform-api-smoky.vercel.app'


class Result:
    """One checked step."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ok = False
        self.detail = ''

    def passed(self, detail: str) -> 'Result':
        self.ok = True
        self.detail = detail
        return self

    def failed(self, detail: str) -> 'Result':
        self.ok = False
        self.detail = detail
        return self


class Funnel:
    def __init__(self, base_url: str, keep_going: bool) -> None:
        self.base = base_url.rstrip('/')
        self.keep_going = keep_going
        self.results: list[Result] = []
        self.token: str | None = None
        self.org_id: str | None = None
        self.stamp = datetime.now(UTC).strftime('%Y%m%d-%H%M%S')

    # -- transport ---------------------------------------------------------

    def call(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        token: str | None = None,
        expect: int | tuple[int, ...] = 200,
    ) -> tuple[int, object]:
        url = f'{self.base}{path}'
        data = json.dumps(body).encode() if body is not None else None
        headers = {'Accept': 'application/json'}
        if data is not None:
            headers['Content-Type'] = 'application/json'
        auth = token if token is not None else self.token
        if auth:
            headers['Authorization'] = f'Bearer {auth}'

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode('utf-8', 'replace')
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', 'replace')
            status = exc.code
        except Exception as exc:  # noqa: BLE001 - transport failure is a result, not a crash
            return 0, f'{type(exc).__name__}: {exc}'

        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw[:400]

        expected = (expect,) if isinstance(expect, int) else expect
        if status not in expected:
            return status, parsed
        return status, parsed

    # -- reporting ---------------------------------------------------------

    def check(self, name: str, ok: bool, detail: str) -> Result:
        result = Result(name)
        result.passed(detail) if ok else result.failed(detail)
        self.results.append(result)
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {name} -- {detail}')
        if not ok and not self.keep_going:
            self.report()
            sys.exit(1)
        return result

    def report(self) -> None:
        passed = sum(1 for r in self.results if r.ok)
        failed = [r for r in self.results if not r.ok]
        print('\n' + '=' * 78)
        print(f'  {passed} passed, {len(failed)} failed (of {len(self.results)})')
        print(f'  Base URL : {self.base}')
        print(f'  Org      : {self.org_id or "(signup did not complete)"}')
        print(f'  Run stamp: {self.stamp}')
        if failed:
            print('\n  FAILED STEPS:')
            for r in failed:
                print(f'    - {r.name}: {r.detail}')
        print('=' * 78)

    # -- steps -------------------------------------------------------------

    def run(self) -> None:
        print(f'\nFreightPilot production funnel verification')
        print(f'Target: {self.base}   (stamp {self.stamp})\n')

        print('1. Platform health')
        status, health = self.call('GET', '/health')
        self.check(
            'GET /health reachable',
            status == 200 and isinstance(health, dict),
            f'HTTP {status} {health}',
        )
        self.check(
            'database reachable (db: ok)',
            isinstance(health, dict) and health.get('db') == 'ok',
            f'db={health.get("db") if isinstance(health, dict) else health!r}',
        )

        print('\n2. Company signup (the first thing the audience sees)')
        company = f'Addis Freight Demo {self.stamp}'
        email = f'owner+{self.stamp}@addisfreight-demo.et'
        status, signup = self.call(
            'POST',
            '/api/v1/auth/company-signup',
            {
                'company_name': company,
                'company_email': email,
                'password': 'DemoPassw0rd!2026',
                'full_name': 'Dawit Lemma',
                'subscription_tier': 'free',
            },
            token='',
            expect=(201, 400, 409, 429),
        )
        if status != 201 or not isinstance(signup, dict):
            self.check(
                'POST /auth/company-signup',
                False,
                f'HTTP {status} {signup} -- signup is the demo entry point; this must be 201',
            )
            return
        self.token = signup.get('access_token')
        org = signup.get('organization') or {}
        self.org_id = org.get('id')
        self.check(
            'POST /auth/company-signup returns a workspace',
            bool(self.token) and bool(self.org_id),
            f'HTTP 201, org={org.get("name")!r} slug={org.get("slug")!r} tier={org.get("subscription_tier")}',
        )
        self.check(
            'signup is rate-limited to 3/min (demo caution)',
            True,
            'limit is 3/minute per IP -- a fourth attempt inside 60s returns 429',
        )

        print('\n3. Identity and workspace')
        status, me = self.call('GET', '/api/v1/auth/me')
        self.check('GET /auth/me', status == 200, f'HTTP {status} user={me.get("username") if isinstance(me, dict) else me!r}')

        status, activation = self.call('GET', '/api/v1/activation')
        self.check('GET /activation', status == 200, f'HTTP {status} {_brief(activation)}')

        print('\n4. The workspace must not be empty on first login (NB-25 seeding)')
        status, warehouses = self.call('GET', '/api/v1/warehouses')
        wh_list = warehouses if isinstance(warehouses, list) else []
        self.check(
            'GET /warehouses has seeded rows',
            status == 200 and len(wh_list) > 0,
            f'HTTP {status}, {len(wh_list)} warehouses'
            + (f' e.g. {wh_list[0].get("code")} {wh_list[0].get("city")}' if wh_list else ''),
        )

        status, items = self.call('GET', '/api/v1/items')
        item_list = items if isinstance(items, list) else []
        self.check(
            'GET /items has seeded rows',
            status == 200 and len(item_list) > 0,
            f'HTTP {status}, {len(item_list)} items' + (f' e.g. {item_list[0].get("sku")}' if item_list else ''),
        )

        status, inventory = self.call('GET', '/api/v1/inventory')
        inv_list = inventory if isinstance(inventory, list) else []
        self.check('GET /inventory has seeded rows', status == 200 and len(inv_list) > 0, f'HTTP {status}, {len(inv_list)} rows')

        status, overview = self.call('GET', '/api/v1/inventory/overview')
        self.check('GET /inventory/overview', status == 200, f'HTTP {status} {_brief(overview)}')

        status, orders = self.call('GET', '/api/v1/orders')
        order_list = orders if isinstance(orders, list) else []
        self.check('GET /orders has seeded rows', status == 200 and len(order_list) > 0, f'HTTP {status}, {len(order_list)} orders')

        print('\n5. Commercial surfaces an incubator will ask about')
        status, plans = self.call('GET', '/api/v1/subscriptions/plans')
        plan_list = plans if isinstance(plans, list) else (plans or {}).get('plans') if isinstance(plans, dict) else []
        self.check('GET /subscriptions/plans', status == 200 and bool(plan_list), f'HTTP {status}, {len(plan_list or [])} plans {_brief(plan_list)}')

        status, sub = self.call('GET', '/api/v1/subscriptions/me')
        self.check('GET /subscriptions/me', status == 200, f'HTTP {status} {_brief(sub)}')

        status, usage = self.call('GET', '/api/v1/subscriptions/usage/me')
        self.check('GET /subscriptions/usage/me', status == 200, f'HTTP {status} {_brief(usage)}')

        status, billing = self.call('GET', '/api/v1/billing/state')
        self.check('GET /billing/state', status == 200, f'HTTP {status} {_brief(billing)}')

        print('\n6. The "aha": first route optimisation (the centrepiece of the demo)')
        if not wh_list:
            self.check('route optimisation', False, 'skipped -- no warehouses to route between')
        else:
            codes = [w.get('code') for w in wh_list if w.get('code')]
            start = codes[0]
            targets = codes[1:4] or codes[:1]
            payload = {
                'route_name': f'Addis morning run {self.stamp}',
                'schedule_date': datetime.now(UTC).date().isoformat(),
                'start_warehouse_code': start,
                'deliveries': [{'warehouse_code': c, 'demand_units': 12} for c in targets],
                'vehicle_capacity_units': 40,
                'max_stops': 20,
                'speed_kmh': 45.0,
                'cost_per_km': 1.5,
                'persist_schedule': True,
            }
            status, route = self.call('POST', '/api/v1/routes/optimize', payload, expect=(200, 400, 404, 422))
            ok = status == 200 and isinstance(route, dict) and route.get('stops')
            self.check(
                'POST /routes/optimize produces a real plan',
                bool(ok),
                f'HTTP {status}, {route.get("total_distance_km") if isinstance(route, dict) else route} km, '
                f'{route.get("total_cost") if isinstance(route, dict) else "?"} ETB, '
                f'{len(route.get("stops") or []) if isinstance(route, dict) else 0} stops, '
                f'objective={route.get("objective") if isinstance(route, dict) else "?"}',
            )

            status, history = self.call('GET', '/api/v1/routes/history')
            self.check('GET /routes/history lists the run', status == 200 and bool(history), f'HTTP {status}, {len(history) if isinstance(history, list) else "?"} runs')

            status, schedules = self.call('GET', '/api/v1/routes/schedules')
            self.check('GET /routes/schedules persists the plan', status == 200 and bool(schedules), f'HTTP {status}, {len(schedules) if isinstance(schedules, list) else "?"} schedules')

        print('\n7. Operational surfaces')
        for label, path in [
            ('ops metrics', '/api/v1/ops/metrics'),
            ('ops readiness', '/api/v1/ops/ready'),
            ('exception feed', '/api/v1/ops/exception-feed'),
            ('audit timeline', '/api/v1/ops/audit-timeline'),
            ('dock appointments', '/api/v1/ops/dock-appointments'),
            ('weather risk zones', '/api/v1/weather/risk-zones'),
            ('alerts', '/api/v1/alerts'),
            ('replenishment plans', '/api/v1/planning/replenishment'),
            ('notifications', '/api/v1/notifications'),
            ('provider keys', '/api/v1/providers/keys'),
            ('provider preference', '/api/v1/providers/preference'),
            ('receipt queue', '/api/v1/receipts/queue'),
            ('receipt wallet', '/api/v1/receipts/wallet'),
            ('billing invoices', '/api/v1/billing/invoices'),
            ('inventory rows', '/api/v1/inventory'),
        ]:
            status, payload = self.call('GET', path)
            self.check(f'GET {path} ({label})', status == 200, f'HTTP {status} {_brief(payload)}')

        # These two are POST, not GET (the console calls them the same way).
        status, forecast = self.call('POST', '/api/v1/forecast/weekly-demand', {'horizon_weeks': 4}, expect=(200, 400))
        self.check(
            'POST /forecast/weekly-demand returns a real model',
            status == 200 and isinstance(forecast, dict) and forecast.get('points'),
            f'HTTP {status} model={forecast.get("model_name") if isinstance(forecast, dict) else forecast} '
            f'points={len(forecast.get("points") or []) if isinstance(forecast, dict) else 0}',
        )

        if wh_list:
            status, eta = self.call(
                'POST',
                '/api/v1/ops/live-eta',
                {
                    'warehouse_id': wh_list[0].get('id'),
                    'truck_id': 'TRUCK-1001',
                    'expected_time': (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
                },
                expect=(200, 400, 404, 422),
            )
            self.check('POST /ops/live-eta writes a dock appointment', status == 200, f'HTTP {status} {_brief(eta)}')
        else:
            self.check('POST /ops/live-eta', False, 'skipped -- no warehouse id available')

        print('\n8. Driver roster and cash-on-delivery (the daily Ethiopian operator loop)')
        phone = f'+2519{int(time.time()) % 100000000:08d}'
        status, driver = self.call(
            'POST',
            '/api/v1/drivers',
            {
                'full_name': 'Yohannes Tesfaye',
                'phone': phone,
                'license_no': 'ET-DRV-99123',
                'vehicle_plate': 'AA-3-B12345',
                'status': 'active',
                'notes': 'Assigned to the Bole-Kality run',
            },
            expect=(201, 409, 400),
        )
        driver_id = driver.get('id') if isinstance(driver, dict) else None
        self.check('POST /drivers creates a driver', status == 201 and bool(driver_id), f'HTTP {status} {_brief(driver)}')

        status, roster = self.call('GET', '/api/v1/drivers')
        self.check('GET /drivers lists the roster', status == 200 and bool(roster), f'HTTP {status}, {len(roster) if isinstance(roster, list) else "?"} drivers')

        # Duplicate phone must be a clean 409, not a 500.
        status, dup = self.call('POST', '/api/v1/drivers', {'full_name': 'Duplicate Driver', 'phone': phone}, expect=(201, 409, 400, 500))
        self.check('duplicate driver phone returns 409 (not 500)', status == 409, f'HTTP {status} {_brief(dup)}')

        if driver_id and wh_list:
            codes = [w.get('code') for w in wh_list if w.get('code')]
            ship_no = f'DEMO-{self.stamp}'
            status, shipment = self.call(
                'POST',
                '/api/v1/shipments',
                {
                    'shipment_no': ship_no,
                    'origin_warehouse_code': codes[0],
                    'destination_warehouse_code': codes[-1],
                    'sku': item_list[0].get('sku') if item_list else 'SKU-001',
                    'quantity_units': 10,
                    'driver_id': driver_id,
                    'cod_amount_etb': 2500.00,
                    'client_ref': f'CLIENT-{self.stamp}',
                },
                expect=(201, 400, 404, 409, 422),
            )
            shipment_id = shipment.get('id') if isinstance(shipment, dict) else None
            self.check(
                'POST /shipments creates a COD shipment',
                status == 201 and bool(shipment_id),
                f'HTTP {status} no={shipment.get("shipment_no") if isinstance(shipment, dict) else "?"} '
                f'cod={shipment.get("cod_amount_etb") if isinstance(shipment, dict) else "?"} ETB '
                f'driver={shipment.get("driver_name") if isinstance(shipment, dict) else "?"}',
            )

            status, ledger_before = self.call('GET', '/api/v1/cash-collections/ledger')
            self.check(
                'ledger before delivery is empty (a cash record opens at delivery)',
                status == 200
                and isinstance(ledger_before, dict)
                and ledger_before.get('outstanding_count', 0) == 0,
                f'HTTP {status} {_brief(ledger_before)} -- note: a COD shipment still in '
                'transit is NOT yet counted as cash exposure',
            )

            if shipment_id:
                status, delivered = self.call(
                    'POST',
                    f'/api/v1/shipments/{shipment_id}/status',
                    {'status': 'delivered', 'cash_collected_etb': 2000.00, 'cash_note': 'Customer paid part in cash'},
                    expect=(200, 400, 404, 409, 422),
                )
                self.check(
                    'delivery with partial cash opens the shortfall',
                    status == 200,
                    f'HTTP {status} {_brief(delivered)}',
                )

                status, collections = self.call('GET', '/api/v1/cash-collections')
                record = None
                if isinstance(collections, list):
                    for row in collections:
                        if row.get('shipment_no') == ship_no:
                            record = row
                            break
                self.check(
                    'cash record shows 2500 expected / 2000 collected / 500 shortfall',
                    record is not None
                    and str(record.get('expected_etb')) == '2500.00'
                    and str(record.get('collected_etb')) == '2000.00'
                    and str(record.get('shortfall_etb')) == '500.00',
                    f'{_brief(record)}',
                )

                status, ledger_after = self.call('GET', '/api/v1/cash-collections/ledger')
                self.check(
                    'ledger after delivery shows the collection and the 500 ETB shortfall',
                    status == 200
                    and isinstance(ledger_after, dict)
                    and ledger_after.get('collected_count', 0) >= 1
                    and str(ledger_after.get('shortfall_etb')) == '500.00',
                    f'HTTP {status} {_brief(ledger_after)}',
                )

                if record:
                    status, settled = self.call(
                        'POST',
                        f'/api/v1/cash-collections/{record.get("id")}/settle',
                        {'note': 'Office accepted the 500 ETB shortfall'},
                        expect=(200, 400, 404, 409),
                    )
                    self.check('POST /cash-collections/{id}/settle closes the record', status == 200, f'HTTP {status} {_brief(settled)}')

        print('\n9. Tenant isolation (the question an incubator always asks)')
        status, other = self.call(
            'POST',
            '/api/v1/auth/company-signup',
            {
                'company_name': f'Second Carrier {self.stamp}',
                'company_email': f'owner+second-{self.stamp}@secondcarrier-demo.et',
                'password': 'DemoPassw0rd!2026',
                'full_name': 'Second Owner',
                'subscription_tier': 'free',
            },
            token='',
            expect=(201, 400, 409, 429),
        )
        if status == 201 and isinstance(other, dict):
            other_token = other.get('access_token')
            status, other_drivers = self.call('GET', '/api/v1/drivers', token=other_token)
            count = len(other_drivers) if isinstance(other_drivers, list) else '?'
            self.check(
                'a second company sees none of the first company\'s drivers',
                status == 200 and isinstance(other_drivers, list) and len(other_drivers) == 0,
                f'HTTP {status}, second org sees {count} drivers (expected 0)',
            )
            if driver_id:
                status, cross = self.call(
                    'GET', f'/api/v1/drivers/{driver_id}', token=other_token, expect=(200, 403, 404)
                )
                self.check(
                    'cross-company driver read is 404, not 200',
                    status == 404,
                    f'HTTP {status} {_brief(cross)}',
                )
        else:
            self.check('second company signup for isolation test', False, f'HTTP {status} {_brief(other)}')

        self.report()


def _brief(value: object, limit: int = 150) -> str:
    if value is None:
        return 'null'
    text = json.dumps(value, default=str) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + '...'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL, help=f'API base URL (default {DEFAULT_BASE_URL})')
    parser.add_argument('--keep-going', action='store_true', help='do not stop at the first failure')
    args = parser.parse_args()

    funnel = Funnel(args.base_url, args.keep_going)
    funnel.run()
    return 0 if all(r.ok for r in funnel.results) else 1


if __name__ == '__main__':
    sys.exit(main())
