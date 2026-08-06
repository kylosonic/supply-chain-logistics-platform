"""Activation payload schemas (blueprint §2.4).

Pydantic + typing only (standalone rule). Payload shapes defined in the
Phase 4 blueprint §6 — the console renders from these exact shapes.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CategoryMilestoneRead(BaseModel):
    category: str
    label: str
    status: Literal['real', 'sample', 'empty']
    real_rows: int
    sample_rows: int
    completed: bool


class ActivationStateRead(BaseModel):
    organization_id: str
    n_of_5: int
    pct_complete: int
    milestones: list[CategoryMilestoneRead]
    m6_completed: bool
    m6_completed_at: datetime | None = None
    next_step: dict | None = None
    banner: dict
    free_cap: dict
    pitch: dict
    toast_fired: bool


class ResetWorkspaceRequest(BaseModel):
    workspace_name: str = Field(min_length=1, max_length=128)

    @field_validator('workspace_name')
    @classmethod
    def _reject_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('workspace_name cannot be blank')
        return value


class ResetWorkspaceResult(BaseModel):
    rows_reseeded: dict[str, int]
    activation_reset: bool


class PitchDismissRequest(BaseModel):
    level: Literal['p60']
