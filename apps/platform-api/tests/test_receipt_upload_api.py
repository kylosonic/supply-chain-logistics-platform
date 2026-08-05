from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from tests.conftest import bad_format_bytes, mock_extraction_payload, pdf_bytes, sample_receipt_bytes


def _upload(client: TestClient, token: str, *, filename='receipt.png', content=None, content_type='image/png', mock=None, mock_json=None):
    files = {'file': (filename, content if content is not None else sample_receipt_bytes(), content_type)}
    data = {}
    if mock_json is not None:
        data['mock_extraction'] = mock_json
    elif mock is not None:
        import json as _json

        data['mock_extraction'] = _json.dumps(mock)
    return client.post('/api/v1/receipts/upload', headers={'Authorization': f'Bearer {token}'}, files=files, data=data)


def test_upload_accepts_png_jpg_pdf(
    client: TestClient, make_paid_org_with_open_invoice, upload_receipt
):
    _, _, token = make_paid_org_with_open_invoice()
    payload = mock_extraction_payload()

    png = upload_receipt(token, filename='receipt.png', content=sample_receipt_bytes(), content_type='image/png', mock_extraction=payload)
    assert png.status_code == 200

    jpg = upload_receipt(token, filename='receipt.jpg', content=sample_receipt_bytes(), content_type='image/jpeg', mock_extraction=payload)
    assert jpg.status_code == 200

    pdf = upload_receipt(token, filename='receipt.pdf', content=pdf_bytes(), content_type='application/pdf', mock_extraction=payload)
    assert pdf.status_code == 200


def test_upload_rejects_txt_with_unsupported_format(
    client: TestClient, make_paid_org_with_open_invoice, upload_receipt
):
    _, _, token = make_paid_org_with_open_invoice()
    resp = upload_receipt(token, filename='receipt.txt', content=bad_format_bytes(), content_type='text/plain')
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'Unsupported file format.'


def test_upload_rejects_oversized_file(client: TestClient, make_paid_org_with_open_invoice, upload_receipt):
    _, _, token = make_paid_org_with_open_invoice()
    big = b'x' * (5 * 1024 * 1024 + 1)
    resp = upload_receipt(token, filename='receipt.png', content=big, content_type='image/png')
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'Receipt too large — maximum 5 MB.'


def test_upload_confirmation_message_exact_copy(
    client: TestClient, make_paid_org_with_open_invoice, upload_receipt
):
    _, _, token = make_paid_org_with_open_invoice()
    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 200
    body = resp.json()
    assert body['message'] == 'Receipt received — verification typically takes ≤24 hours.'
    assert body['receipt_id']


def test_upload_ok_while_hard_locked(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, upload_receipt
):
    """EXEMPTION PROOF: a hard-locked org can still upload (200, no 423)."""
    org, invoice, token = make_paid_org_with_open_invoice()
    invoice.grace_ends_at = (datetime.now(UTC) - timedelta(days=1)).date()
    db_session.add(invoice)
    db_session.commit()

    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 200
    org = db_session.get(Organization, org.id)
    assert org.billing_phase == 'hard_locked'


def test_upload_ok_during_grace(
    client: TestClient, make_paid_org_with_open_invoice, upload_receipt
):
    _, _, token = make_paid_org_with_open_invoice()
    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 200


def test_upload_no_open_invoice_returns_400(client: TestClient, db_session: Session, upload_receipt):
    """Paid org in limbo (trial ended, no invoice yet): no open invoice."""
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'No Invoice Co',
            'company_email': 'owner-noinv@receiptco.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': 'starter',
        },
    )
    token = resp.json()['access_token']
    up = client.post('/api/v1/subscriptions/select-tier', headers={'Authorization': f'Bearer {token}'}, json={'tier': 'starter'})
    assert up.status_code == 200

    org_id = resp.json()['organization']['id']
    org = db_session.get(Organization, org_id)
    now = datetime.now(UTC)
    org.trial_started_at = now - timedelta(hours=170)
    org.trial_ends_at = now - timedelta(hours=2)
    from app.models.trial_record import TrialRecord

    trial = db_session.execute(
        select(TrialRecord).where(TrialRecord.organization_id == org_id)
    ).scalars().one()
    trial.started_at = now - timedelta(hours=170)
    trial.ended_at = now - timedelta(hours=2)
    db_session.commit()

    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'You have no open invoice to apply this receipt to.'

    # No zombie row: an unrouteable upload must never reach the queue
    # (QA finding — blueprint §2.1 + risk note 8).
    rows = db_session.execute(select(PaymentReceipt)).scalars().all()
    assert rows == []


def test_upload_free_org_returns_400(client: TestClient, upload_receipt):
    resp = client.post(
        '/api/v1/auth/company-signup',
        json={
            'company_name': 'Free Org Co',
            'company_email': 'owner-freeorg@receiptco.com',
            'password': 'VeryStrongPass9',
            'full_name': 'Owner User',
            'subscription_tier': 'free',
        },
    )
    token = resp.json()['access_token']
    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 400
    assert resp.json()['detail'] == 'You have no open invoice to apply this receipt to.'


def test_upload_routes_to_oldest_open_invoice(
    client: TestClient, db_session: Session, make_paid_org_with_open_invoice, upload_receipt
):
    import datetime as _dt
    from decimal import Decimal

    from app.models.collection_account import CollectionAccount
    from app.models.subscription_invoice import SubscriptionInvoice

    org, invoice_old, token = make_paid_org_with_open_invoice(period_start=_dt.date(2026, 6, 1))
    account = db_session.execute(
        select(CollectionAccount).where(CollectionAccount.bank_code == 'dashen')
    ).scalar_one()
    today = _dt.date.today()
    db_session.add(
        SubscriptionInvoice(
            organization_id=org.id,
            invoice_number='INV-000200',
            tier='starter',
            billing_period_start=_dt.date(2026, 8, 1),
            billing_period_end=_dt.date(2026, 8, 31),
            flat_amount_etb=Decimal('4500.00'),
            total_etb=Decimal('4500.00'),
            balance_remaining_etb=Decimal('4500.00'),
            due_date=_dt.date(2026, 8, 1),
            grace_days=3,
            grace_ends_at=today + timedelta(days=1),
            designated_account_id=account.id,
            status='issued',
        )
    )
    db_session.commit()

    resp = upload_receipt(token, mock_extraction=mock_extraction_payload())
    assert resp.status_code == 200
    receipt = db_session.execute(
        select(PaymentReceipt).where(PaymentReceipt.organization_id == org.id)
    ).scalars().one()
    assert receipt.invoice_id == invoice_old.id


def test_upload_unauthenticated_401(client: TestClient, upload_receipt):
    resp = upload_receipt('not-a-token')
    assert resp.status_code == 401
