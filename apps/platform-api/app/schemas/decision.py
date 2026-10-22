from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class DecisionEvidence(BaseModel):
    record_type: str
    record_id: str | None = None
    label: str
    value: str | int | float | None = None


class DecisionRisk(BaseModel):
    kind: str
    severity: str
    message: str
    evidence: list[DecisionEvidence] = Field(default_factory=list)


class DecisionAction(BaseModel):
    priority: int
    action: str
    reason: str
    href: str | None = None
    evidence: list[DecisionEvidence] = Field(default_factory=list)


class CashRiskRow(BaseModel):
    driver_id: str | None
    driver_name: str
    outstanding_count: int
    expected_etb: Decimal
    collected_etb: Decimal
    shortfall_etb: Decimal
    risk_score: int
    factors: list[str]


class ExceptionTriageRow(BaseModel):
    alert_id: str
    title: str
    severity: str
    age_hours: float
    priority: int
    suggested_action: str
    evidence: list[DecisionEvidence] = Field(default_factory=list)


class DecisionBrief(BaseModel):
    generated_at: datetime
    generated_by: str
    headline: str
    what_changed: list[str]
    risks: list[DecisionRisk]
    actions: list[DecisionAction]
    cash_risk: list[CashRiskRow]
    triage: list[ExceptionTriageRow]
