from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _setup(client: TestClient, token: str):
    customer = client.post(
        '/api/v1/dispatch/customers',
        headers=_headers(token),
        json={
            'code': 'CUST-001',
            'name': 'Blue Nile Retail',
            'phone': '+251911111111',
            'address': 'Bole, Addis Ababa',
            'latitude': 8.99,
            'longitude': 38.78,
        },
    )
    assert customer.status_code == 201, customer.text
    customer_two = client.post(
        '/api/v1/dispatch/customers',
        headers=_headers(token),
        json={
            'code': 'CUST-002',
            'name': 'Merkato Wholesale',
            'address': 'Merkato, Addis Ababa',
            'latitude': 9.03,
            'longitude': 38.74,
        },
    )
    assert customer_two.status_code == 201, customer_two.text

    first = client.post(
        '/api/v1/dispatch/orders',
        headers=_headers(token),
        json={
            'order_no': 'DO-001',
            'customer_id': customer.json()['id'],
            'quantity_units': 10,
            'cod_amount_etb': '500.00',
            'window_start': '2026-10-22T08:00:00+00:00',
            'window_end': '2026-10-22T10:00:00+00:00',
            'service_minutes': 15,
            'priority': 5,
        },
    )
    assert first.status_code == 201, first.text
    second = client.post(
        '/api/v1/dispatch/orders',
        headers=_headers(token),
        json={
            'order_no': 'DO-002',
            'customer_id': customer_two.json()['id'],
            'quantity_units': 20,
            'cod_amount_etb': '750.00',
            'service_minutes': 20,
            'priority': 3,
        },
    )
    assert second.status_code == 201, second.text
    driver = client.post(
        '/api/v1/drivers',
        headers=_headers(token),
        json={
            'full_name': 'Dispatch Driver',
            'phone': '+251922222222',
            'vehicle_plate': 'ET-3-12345',
        },
    )
    assert driver.status_code == 201, driver.text
    return first.json(), second.json(), driver.json()


def test_dispatch_run_driver_manifest_proof_and_cash_close(client: TestClient, signup_workspace):
    _org, token = signup_workspace('Dispatch Workspace')
    first, second, driver = _setup(client, token)

    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Thursday customer run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id'], second['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
            'average_speed_kmh': 30,
        },
    )
    assert planned.status_code == 201, planned.text
    run = planned.json()
    assert len(run['stops']) == 2
    assert [stop['sequence'] for stop in run['stops']] == [1, 2]

    link = client.post(
        f"/api/v1/dispatch/runs/{run['id']}/driver-link",
        headers=_headers(token),
    )
    assert link.status_code == 200, link.text
    driver_token = link.json()['token']
    assert '/driver#token=' in link.json()['driver_url']

    manifest = client.get(
        '/api/v1/dispatch/driver/manifest',
        headers={'X-Driver-Token': driver_token},
    )
    assert manifest.status_code == 200, manifest.text
    assert manifest.json()['driver_name'] == 'Dispatch Driver'
    assert len(manifest.json()['stops']) == 2

    first_stop = manifest.json()['stops'][0]
    delivered = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/status",
        headers={'X-Driver-Token': driver_token},
        json={'status': 'delivered'},
    )
    assert delivered.status_code == 200, delivered.text

    unexplained_shortfall = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/cash",
        headers={'X-Driver-Token': driver_token},
        json={'collected_etb': '400.00'},
    )
    assert unexplained_shortfall.status_code == 422, unexplained_shortfall.text

    over_declared = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/cash",
        headers={'X-Driver-Token': driver_token},
        json={'collected_etb': '600.00', 'note': 'Incorrect amount'},
    )
    assert over_declared.status_code == 422, over_declared.text

    cash = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/cash",
        headers={'X-Driver-Token': driver_token},
        json={'collected_etb': '400.00', 'note': 'Customer paid partially'},
    )
    assert cash.status_code == 200, cash.text
    assert cash.json()['collected_cash_etb'] == '400.00'

    proof = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/proof",
        headers={'X-Driver-Token': driver_token},
        data={'recipient_name': 'Store manager', 'notes': 'Parcel handed over'},
        files={'file': ('proof.png', b'\x89PNG\r\n\x1a\nproof', 'image/png')},
    )
    assert proof.status_code == 201, proof.text
    assert proof.json()['proof_kind'] == 'photo'

    proof_file = client.get(
        f"/api/v1/dispatch/orders/{first_stop['order_id']}/proofs/{proof.json()['id']}/file",
        headers=_headers(token),
    )
    assert proof_file.status_code == 200, proof_file.text
    assert proof_file.headers['content-type'] == 'image/png'
    assert proof_file.content.startswith(b'\x89PNG\r\n\x1a\n')

    spoofed = client.post(
        f"/api/v1/dispatch/driver/orders/{first_stop['order_id']}/proof",
        headers={'X-Driver-Token': driver_token},
        files={'file': ('fake.png', b'not-an-image', 'image/png')},
    )
    assert spoofed.status_code == 415, spoofed.text

    for stop in manifest.json()['stops'][1:]:
        response = client.post(
            f"/api/v1/dispatch/driver/orders/{stop['order_id']}/status",
            headers={'X-Driver-Token': driver_token},
            json={'status': 'delivered'},
        )
        assert response.status_code == 200, response.text

    close = client.post(
        f"/api/v1/dispatch/runs/{run['id']}/close-cash",
        headers=_headers(token),
    )
    assert close.status_code == 200, close.text
    assert close.json()['expected_etb'] == '1250.00'
    assert close.json()['collected_etb'] == '400.00'
    assert close.json()['shortfall_etb'] == '850.00'
    assert close.json()['terminal_stops'] == 2


def test_dispatch_is_tenant_scoped(client: TestClient, signup_workspace):
    _org_a, token_a = signup_workspace('Dispatch A')
    _org_b, token_b = signup_workspace('Dispatch B')
    first, _second, _driver = _setup(client, token_a)

    order = client.get('/api/v1/dispatch/orders', headers=_headers(token_b))
    assert order.status_code == 200
    assert order.json() == []

    foreign = client.get(
        f"/api/v1/dispatch/orders/{first['id']}",
        headers=_headers(token_b),
    )
    assert foreign.status_code == 404

    denied = client.post(
        '/api/v1/dispatch/customers',
        headers=_headers(token_b),
        json={
            'code': 'CUST-001',
            'name': 'Collision',
            'address': 'Other',
            'latitude': 9.0,
            'longitude': 38.7,
        },
    )
    assert denied.status_code == 201


def test_failed_stop_does_not_create_a_cash_obligation(
    client: TestClient, signup_workspace
):
    _org, token = signup_workspace('Failed Stop Workspace')
    first, second, driver = _setup(client, token)
    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Failed stop run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id'], second['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
        },
    )
    assert planned.status_code == 201, planned.text
    run = planned.json()
    link = client.post(
        f"/api/v1/dispatch/runs/{run['id']}/driver-link",
        headers=_headers(token),
    )
    assert link.status_code == 200, link.text
    driver_headers = {'X-Driver-Token': link.json()['token']}
    stops = client.get('/api/v1/dispatch/driver/manifest', headers=driver_headers).json()['stops']

    for stop in stops:
        status = 'failed' if stop['order_id'] == first['id'] else 'delivered'
        updated = client.post(
            f"/api/v1/dispatch/driver/orders/{stop['order_id']}/status",
            headers=driver_headers,
            json={'status': status},
        )
        assert updated.status_code == 200, updated.text

    close = client.post(
        f"/api/v1/dispatch/runs/{run['id']}/close-cash",
        headers=_headers(token),
    )
    assert close.status_code == 200, close.text
    assert close.json()['expected_etb'] == '750.00'
    assert close.json()['shortfall_etb'] == '750.00'


def test_delivery_proof_file_is_tenant_scoped(client: TestClient, signup_workspace):
    _org_a, token_a = signup_workspace('Proof Tenant A')
    _org_b, token_b = signup_workspace('Proof Tenant B')
    first, _second, driver = _setup(client, token_a)
    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token_a),
        json={
            'route_name': 'Proof run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
        },
    )
    assert planned.status_code == 201, planned.text
    link = client.post(
        f"/api/v1/dispatch/runs/{planned.json()['id']}/driver-link",
        headers=_headers(token_a),
    )
    assert link.status_code == 200, link.text
    proof = client.post(
        f"/api/v1/dispatch/driver/orders/{first['id']}/proof",
        headers={'X-Driver-Token': link.json()['token']},
        files={'file': ('proof.png', b'\x89PNG\r\n\x1a\nproof', 'image/png')},
    )
    assert proof.status_code == 201, proof.text

    denied = client.get(
        f"/api/v1/dispatch/orders/{first['id']}/proofs/{proof.json()['id']}/file",
        headers=_headers(token_b),
    )
    assert denied.status_code == 404


def test_proof_upload_limit_is_atomic(client: TestClient, signup_workspace):
    _org, token = signup_workspace('Proof Limit Workspace')
    first, _second, driver = _setup(client, token)
    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Proof limit run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
        },
    )
    assert planned.status_code == 201, planned.text
    link = client.post(
        f"/api/v1/dispatch/runs/{planned.json()['id']}/driver-link",
        headers=_headers(token),
    )
    assert link.status_code == 200, link.text
    driver_headers = {'X-Driver-Token': link.json()['token']}

    for sequence in range(1, 6):
        proof = client.post(
            f"/api/v1/dispatch/driver/orders/{first['id']}/proof",
            headers=driver_headers,
            files={
                'file': (
                    f'proof-{sequence}.png',
                    b'\x89PNG\r\n\x1a\nproof',
                    'image/png',
                )
            },
        )
        assert proof.status_code == 201, proof.text
    sixth = client.post(
        f"/api/v1/dispatch/driver/orders/{first['id']}/proof",
        headers=driver_headers,
        files={'file': ('proof-6.png', b'\x89PNG\r\n\x1a\nproof', 'image/png')},
    )
    assert sixth.status_code == 409, sixth.text
    proofs = client.get(
        f"/api/v1/dispatch/orders/{first['id']}/proofs",
        headers=_headers(token),
    )
    assert proofs.status_code == 200, proofs.text
    assert len(proofs.json()) == 5


def test_deactivated_driver_capability_is_rejected(
    client: TestClient, signup_workspace
):
    _org, token = signup_workspace('Driver Revocation Workspace')
    first, _second, driver = _setup(client, token)
    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Revocation run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 100,
            'max_stops': 10,
        },
    )
    assert planned.status_code == 201, planned.text
    link = client.post(
        f"/api/v1/dispatch/runs/{planned.json()['id']}/driver-link",
        headers=_headers(token),
    )
    assert link.status_code == 200, link.text
    driver_token = link.json()['token']

    deactivated = client.delete(
        f"/api/v1/drivers/{driver['id']}",
        headers=_headers(token),
    )
    assert deactivated.status_code == 204, deactivated.text

    manifest = client.get(
        '/api/v1/dispatch/driver/manifest',
        headers={'X-Driver-Token': driver_token},
    )
    assert manifest.status_code == 403


def test_capacity_exclusions_are_reported_and_not_counted_as_expected_cash(
    client: TestClient, signup_workspace
):
    _org, token = signup_workspace('Dispatch Capacity Workspace')
    first, second, driver = _setup(client, token)
    planned = client.post(
        '/api/v1/dispatch/runs',
        headers=_headers(token),
        json={
            'route_name': 'Capacity-constrained run',
            'plan_date': '2026-10-22',
            'start_label': 'Main depot',
            'start_latitude': 9.0,
            'start_longitude': 38.75,
            'order_ids': [first['id'], second['id']],
            'driver_id': driver['id'],
            'vehicle_capacity_units': 15,
            'max_stops': 10,
        },
    )
    assert planned.status_code == 201, planned.text
    body = planned.json()
    assert len(body['stops']) == 1
    assert body['expected_cash_etb'] == '500.00'
    assert len(body['unassigned']) == 1
    assert body['unassigned'][0]['order_id'] == second['id']
    assert body['unassigned'][0]['reason'] == 'exceeds_remaining_capacity'
