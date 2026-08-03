from __future__ import annotations

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.repositories.base import BaseRepository


class ShipmentRepository(BaseRepository[Shipment]):
    model = Shipment

    def __init__(self, db: Session):
        super().__init__(db)

    def list_all_sorted(self) -> list[Shipment]:
        return list(
            self.db.execute(
                select(Shipment).order_by(asc(Shipment.created_at))
            ).scalars().all()
        )

    def get_by_shipment_no(self, shipment_no: str) -> Shipment | None:
        return self.db.execute(
            select(Shipment).where(Shipment.shipment_no == shipment_no)
        ).scalar_one_or_none()
