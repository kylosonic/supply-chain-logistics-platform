from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.conftest import mock_extraction_payload, sample_receipt_bytes


def _headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def _upload(client: TestClient, token: str, reference: str) -> str:
    payload = mock_extraction_payload(
        fields={
            **mock_extraction_payload()['fields'],
            'reference_number': reference,
        }
    )
    response = client.post(
        '/api/v1/receipts/upload',
        headers=_headers(token),
        files={'file': ('receipt.png', sample_receipt_bytes(), 'image/png')},
        data={'mock_extraction': json.dumps(payload)},
    )
    assert response.status_code == 200, response.text
    return response.json()['receipt_id']


def test_receipt_queue_and_verdict_are_scoped_to_selected_workspace(
    client: TestClient,
    make_paid_org_with_open_invoice,
):
    _org_a, _invoice_a, token_a = make_paid_org_with_open_invoice(
        invoice_number='INV-TENANT-A'
    )
    _org_b, _invoice_b, token_b = make_paid_org_with_open_invoice(
        invoice_number='INV-TENANT-B'
    )
    receipt_a = _upload(client, token_a, 'TENANT-A-REF')
    receipt_b = _upload(client, token_b, 'TENANT-B-REF')

    queue_a = client.get('/api/v1/receipts/queue', headers=_headers(token_a))
    assert queue_a.status_code == 200, queue_a.text
    ids_a = {item['id'] for item in queue_a.json()}
    assert receipt_a in ids_a
    assert receipt_b not in ids_a

    foreign_file = client.get(
        f'/api/v1/receipts/queue/{receipt_b}/file',
        headers=_headers(token_a),
    )
    assert foreign_file.status_code == 404
    foreign_audit = client.get(
        f'/api/v1/receipts/{receipt_b}/audit-events',
        headers=_headers(token_a),
    )
    assert foreign_audit.status_code == 404
    foreign_decision = client.post(
        f'/api/v1/receipts/{receipt_b}/decision',
        headers=_headers(token_a),
        json={'verdict': 'reject_illegible'},
    )
    assert foreign_decision.status_code == 404

    own_decision = client.post(
        f'/api/v1/receipts/{receipt_a}/decision',
        headers=_headers(token_a),
        json={'verdict': 'reject_illegible'},
    )
    assert own_decision.status_code == 200, own_decision.text
