"""Shared activation banner payload (blueprint decision #8, NB-30.1).

Single state source for both console render densities (compact on
/dashboard, checklist on /upload). The free-cap + pitch banners render
from the same payload on every console page (NB-31.6 / NB-32).

Import map: activation.state, activation.freecap only.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.services.activation import state as activation_state


def activation_banner_payload(db: Session, org: Organization, now: datetime) -> dict:
    """The single payload both console pages render (blueprint §2.3)."""
    state = activation_state.activation_state_read(db, org, now)
    return {
        'visible': not state.m6_completed,
        'n_of_5': state.n_of_5,
        'pct': state.pct_complete,
        'next_step': state.next_step,
        'cta': state.banner['cta'],
        'demo_mode': state.banner['demo_mode'],
        'free_cap': state.free_cap,
        'pitch': state.pitch,
        'toast_fired': state.toast_fired,
    }
