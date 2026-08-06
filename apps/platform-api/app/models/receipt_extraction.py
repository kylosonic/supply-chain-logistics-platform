from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.custom_types import UUIDType
from app.models.common import UUIDTimestampMixin


class ReceiptExtraction(UUIDTimestampMixin, Base):
    """1:1 AI extraction result for a receipt (TECH-10).

    ``fields`` and ``confidence`` carry exactly the eight keys from
    ``services.billing.receipt_extraction.EXTRACTION_FIELDS``. A row with
    ``provider_name IS NULL`` is the zero-confidence fallback.
    """

    __tablename__ = 'receipt_extractions'
    __table_args__ = (
        UniqueConstraint('receipt_id', name='uq_receipt_extraction_receipt'),
    )

    receipt_id: Mapped[UUID] = mapped_column(
        UUIDType, ForeignKey('payment_receipts.id', ondelete='CASCADE'), nullable=False
    )
    provider_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    key_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fields: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
