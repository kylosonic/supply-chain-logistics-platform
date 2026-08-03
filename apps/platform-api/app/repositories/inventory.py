from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.item import Item
from app.models.warehouse import Warehouse
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    model = Inventory

    def __init__(self, db: Session):
        super().__init__(db)

    def list_by_org(self, organization_id: str) -> list[Inventory]:
        return list(
            self.db.execute(
                select(Inventory).where(Inventory.organization_id == organization_id)
            ).scalars().all()
        )

    def get_by_warehouse_and_item(
        self, warehouse_id: str, item_id: str, organization_id: str | None = None
    ) -> Inventory | None:
        query = select(Inventory).where(
            Inventory.warehouse_id == warehouse_id,
            Inventory.item_id == item_id,
        )
        if organization_id:
            query = query.where(Inventory.organization_id == organization_id)
        return self.db.execute(query).scalar_one_or_none()

    def upsert(
        self,
        warehouse_id: str,
        item_id: str,
        organization_id: str | None,
        quantity_on_hand: int,
        safety_stock: int,
    ) -> Inventory:
        stmt = pg_insert(Inventory).values(
            warehouse_id=warehouse_id,
            item_id=item_id,
            organization_id=organization_id,
            quantity_on_hand=quantity_on_hand,
            safety_stock=safety_stock,
        )
        stmt = stmt.on_conflict_do_update(
            constraint='uq_inventory_warehouse_item',
            set_={
                'quantity_on_hand': quantity_on_hand,
                'safety_stock': safety_stock,
                'updated_at': func.now(),
            },
        )
        self.db.execute(stmt)
        self.db.commit()

        return self.db.execute(
            select(Inventory).where(
                Inventory.warehouse_id == warehouse_id,
                Inventory.item_id == item_id,
            )
        ).scalar_one()

    def get_overview_by_org(self, organization_id: str) -> list[dict]:
        stmt = (
            select(
                Warehouse.code.label('warehouse_code'),
                Warehouse.name.label('warehouse_name'),
                func.coalesce(func.sum(Inventory.quantity_on_hand), 0).label('total_quantity_on_hand'),
                func.coalesce(func.sum(Inventory.safety_stock), 0).label('total_safety_stock'),
                func.max(Warehouse.capacity_units).label('capacity_units'),
            )
            .join(Inventory, Inventory.warehouse_id == Warehouse.id, isouter=True)
            .where(Warehouse.organization_id == organization_id)
            .group_by(Warehouse.code, Warehouse.name)
            .order_by(Warehouse.code)
        )
        rows = self.db.execute(stmt).all()
        return [
            {
                'warehouse_code': row.warehouse_code,
                'warehouse_name': row.warehouse_name,
                'total_quantity_on_hand': row.total_quantity_on_hand,
                'total_safety_stock': row.total_safety_stock,
                'capacity_units': row.capacity_units,
            }
            for row in rows
        ]
