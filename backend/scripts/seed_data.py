from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.services.security import hash_password

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'sample-data'


def seed_users(db):
    defaults = [
        ('admin', 'admin12345', UserRole.ADMIN),
        ('operator', 'operator12345', UserRole.OPERATOR),
        ('viewer', 'viewer12345', UserRole.VIEWER),
    ]
    for username, raw_password, role in defaults:
        exists = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
        if exists:
            continue
        db.add(
            User(
                username=username,
                password_hash=hash_password(raw_password),
                role=role,
                is_active=True,
            )
        )


def seed_warehouses(db):
    with open(SAMPLE / 'warehouses.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exists = db.execute(select(Warehouse).where(Warehouse.code == row['code'])).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Warehouse(
                    code=row['code'],
                    name=row['name'],
                    address=row['address'],
                    city=row['city'],
                    state=row['state'],
                    country=row['country'],
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    capacity_units=int(row['capacity_units']),
                )
            )


def seed_items(db):
    with open(SAMPLE / 'items.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exists = db.execute(select(Item).where(Item.sku == row['sku'])).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Item(
                    sku=row['sku'],
                    name=row['name'],
                    category=row['category'],
                    unit_cost=float(row['unit_cost']),
                    reorder_level=int(row['reorder_level']),
                )
            )


def seed_inventory(db):
    with open(SAMPLE / 'inventory.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            warehouse = db.execute(select(Warehouse).where(Warehouse.code == row['warehouse_code'])).scalar_one()
            item = db.execute(select(Item).where(Item.sku == row['sku'])).scalar_one()
            exists = db.execute(select(Inventory).where(Inventory.warehouse_id == warehouse.id, Inventory.item_id == item.id)).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Inventory(
                    warehouse_id=warehouse.id,
                    item_id=item.id,
                    quantity_on_hand=int(row['quantity_on_hand']),
                    safety_stock=int(row['safety_stock']),
                )
            )


def seed_orders(db):
    with open(SAMPLE / 'orders.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            warehouse = db.execute(select(Warehouse).where(Warehouse.code == row['warehouse_code'])).scalar_one()
            item = db.execute(select(Item).where(Item.sku == row['sku'])).scalar_one()
            db.add(
                HistoricalOrder(
                    order_date=row['order_date'],
                    warehouse_id=warehouse.id,
                    item_id=item.id,
                    quantity=int(row['quantity']),
                    unit_price=float(row['unit_price']),
                    customer_region=row['customer_region'],
                    weather_avg_temp_c=float(row['weather_avg_temp_c']),
                    weather_precip_mm=float(row['weather_precip_mm']),
                    weather_disruption_index=float(row['weather_disruption_index']),
                )
            )


def main():
    db = SessionLocal()
    try:
        seed_users(db)
        seed_warehouses(db)
        seed_items(db)
        db.commit()

        seed_inventory(db)
        seed_orders(db)
        db.commit()
        print('Sample data seeded successfully.')
        print('Default users: admin/admin12345, operator/operator12345, viewer/viewer12345')
    finally:
        db.close()


if __name__ == '__main__':
    main()
