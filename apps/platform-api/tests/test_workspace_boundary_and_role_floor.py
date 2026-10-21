from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.freight_invoice import FreightInvoice
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.order import HistoricalOrder
from app.models.organization import Organization
from app.models.user import User
from app.models.warehouse import Warehouse


def _headers(token: str, org_id: str | None = None) -> dict[str, str]:
    headers = {'Authorization': f'Bearer {token}'}
    if org_id:
        headers['X-Organization-Id'] = org_id
    return headers


def _org(name: str, slug: str) -> Organization:
    return Organization(
        name=name,
        slug=slug,
        primary_email_domain=None,
        subscription_tier='free',
        subscription_status='active',
        billing_phase='free',
        is_active=True,
    )


def test_selected_workspace_is_used_for_item_and_warehouse_writes(
    client: TestClient,
    db_session: Session,
    operator_token: str,
):
    org_a = _org('Selected Workspace A', 'selected-workspace-a')
    org_b = _org('Selected Workspace B', 'selected-workspace-b')
    db_session.add_all([org_a, org_b])
    db_session.flush()
    operator = db_session.execute(select(User).where(User.username == 'operator')).scalar_one()
    db_session.add_all(
        [
            OrganizationMembership(
                organization_id=org_a.id,
                user_id=operator.id,
                role='operator',
                is_active=True,
            ),
            OrganizationMembership(
                organization_id=org_b.id,
                user_id=operator.id,
                role='viewer',
                is_active=True,
            ),
        ]
    )
    warehouse_a = Warehouse(
        code='SEL-WH-A',
        name='A warehouse',
        address='A address',
        city='Addis Ababa',
        state='Addis Ababa',
        country='ET',
        latitude=9.0,
        longitude=38.75,
        capacity_units=1000,
        organization_id=org_a.id,
    )
    warehouse_b = Warehouse(
        code='SEL-WH-B',
        name='B warehouse',
        address='B address',
        city='Addis Ababa',
        state='Addis Ababa',
        country='ET',
        latitude=9.01,
        longitude=38.76,
        capacity_units=1000,
        organization_id=org_b.id,
    )
    item_a = Item(
        sku='SEL-SKU-A',
        name='A item',
        category='test',
        unit_cost=1,
        reorder_level=1,
        organization_id=org_a.id,
    )
    item_b = Item(
        sku='SEL-SKU-B',
        name='B item',
        category='test',
        unit_cost=1,
        reorder_level=1,
        organization_id=org_b.id,
    )
    db_session.add_all([warehouse_a, warehouse_b, item_a, item_b])
    db_session.commit()

    foreign_warehouse = client.patch(
        f'/api/v1/warehouses/{warehouse_b.id}',
        headers=_headers(operator_token, str(org_a.id)),
        json={'name': 'Cross-tenant mutation'},
    )
    assert foreign_warehouse.status_code == 404
    foreign_item = client.patch(
        f'/api/v1/items/{item_b.id}',
        headers=_headers(operator_token, str(org_a.id)),
        json={'name': 'Cross-tenant mutation'},
    )
    assert foreign_item.status_code == 404

    listed_items = client.get(
        '/api/v1/items',
        headers=_headers(operator_token, str(org_a.id)),
    )
    assert listed_items.status_code == 200, listed_items.text
    assert {row['sku'] for row in listed_items.json()} == {'SEL-SKU-A'}

    shipment = client.post(
        '/api/v1/shipments',
        headers=_headers(operator_token, str(org_a.id)),
        json={
            'shipment_no': 'SEL-SHIP-1',
            'origin_warehouse_code': 'SEL-WH-A',
            'destination_warehouse_code': 'SEL-WH-A',
            'sku': 'SEL-SKU-A',
            'quantity_units': 1,
        },
    )
    assert shipment.status_code == 201, shipment.text
    audit_event = db_session.execute(
        select(AuditEvent)
        .where(AuditEvent.event_type == 'shipment.created')
        .order_by(AuditEvent.created_at.desc())
    ).scalars().first()
    assert audit_event is not None
    audit_org = audit_event.organization_id
    assert str(audit_org) == str(org_a.id)


def test_freight_invoices_are_tenant_scoped_and_order_checked(
    client: TestClient,
    db_session: Session,
    signup_workspace,
):
    org_a, token_a = signup_workspace('Freight Invoice A')
    org_b, token_b = signup_workspace('Freight Invoice B')
    warehouse_a = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_a)).limit(1)
    ).scalar_one()
    item_a = db_session.execute(
        select(Item).where(Item.organization_id == UUID(org_a)).limit(1)
    ).scalar_one()
    warehouse_b = db_session.execute(
        select(Warehouse).where(Warehouse.organization_id == UUID(org_b)).limit(1)
    ).scalar_one()
    item_b = db_session.execute(
        select(Item).where(Item.organization_id == UUID(org_b)).limit(1)
    ).scalar_one()
    order_a = HistoricalOrder(
        order_date=date(2026, 10, 21),
        warehouse_id=warehouse_a.id,
        item_id=item_a.id,
        organization_id=UUID(org_a),
        quantity=10,
        unit_price=100.0,
    )
    order_b = HistoricalOrder(
        order_date=date(2026, 10, 21),
        warehouse_id=warehouse_b.id,
        item_id=item_b.id,
        organization_id=UUID(org_b),
        quantity=10,
        unit_price=200.0,
    )
    db_session.add_all([order_a, order_b])
    db_session.commit()

    cross_upload = client.post(
        '/api/v1/invoices/upload',
        headers=_headers(token_a),
        files={
            'file': (
                'invoices.csv',
                f'order_id,carrier_id,actual_rate\n{order_b.id},carrier-b,2000\n'.encode(),
                'text/csv',
            )
        },
    )
    assert cross_upload.status_code == 200, cross_upload.text
    assert cross_upload.json() == []

    own_upload = client.post(
        '/api/v1/invoices/upload',
        headers=_headers(token_a),
        files={
            'file': (
                'invoices.csv',
                f'order_id,carrier_id,actual_rate\n{order_a.id},carrier-a,1000\n'.encode(),
                'text/csv',
            )
        },
    )
    assert own_upload.status_code == 200, own_upload.text
    assert len(own_upload.json()) == 1
    invoice = db_session.get(FreightInvoice, db_session.execute(select(FreightInvoice.id)).scalar_one())
    assert invoice is not None
    assert str(invoice.organization_id) == org_a

    other_view = client.get('/api/v1/invoices', headers=_headers(token_b))
    assert other_view.status_code == 200, other_view.text
    assert other_view.json() == []


def test_membership_admin_cannot_exceed_global_account_role(
    client: TestClient,
    db_session: Session,
    viewer_token: str,
):
    org = _org('Role Floor Workspace', 'role-floor-workspace')
    db_session.add(org)
    db_session.flush()
    viewer = db_session.execute(select(User).where(User.username == 'viewer')).scalar_one()
    db_session.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=viewer.id,
            role='admin',
            is_active=True,
        )
    )
    db_session.commit()
    headers = _headers(viewer_token, str(org.id))

    team = client.get('/api/v1/team/members', headers=headers)
    assert team.status_code == 403, team.text
    receipts = client.get('/api/v1/receipts/queue', headers=headers)
    assert receipts.status_code == 403, receipts.text
