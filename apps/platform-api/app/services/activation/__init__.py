"""Activation engine (Phase 4 blueprint).

Package contract: derived milestones 1-5 (real-row presence per category),
stored milestone 6 (first route optimization), lazy free-cap lock
(decision #5), the 60/80/100 pitch ladder (decision #6), per-workspace
sample seeding (decision #11), supersede semantics (decision #3), and the
admin-gated workspace reset (decision #10).

DAG: ``activation.* -> billing.pricing`` (leaf) and ``activation.* ->
metering`` (leaf); ``billing.locks -> activation.freecap -> pricing`` has
no back-edge into billing — ``billing`` NEVER imports ``activation`` and
``activation`` NEVER imports ``app.api`` (acyclic by construction).
"""

from app.services.activation.banner import activation_banner_payload
from app.services.activation.freecap import (
    FreeCapLockedError,
    assert_free_cap_writable,
    dismiss_pitch,
    free_cap_state,
    pitch_state,
)
from app.services.activation.reset import reset_workspace
from app.services.activation.seeding import seed_workspace, supersede_sample_rows
from app.services.activation.state import (
    ActivationStateRead,
    activation_state_read,
    record_csv_upload,
    record_route_optimization,
)

__all__ = [
    'ActivationStateRead',
    'FreeCapLockedError',
    'activation_banner_payload',
    'activation_state_read',
    'assert_free_cap_writable',
    'dismiss_pitch',
    'free_cap_state',
    'pitch_state',
    'record_csv_upload',
    'record_route_optimization',
    'reset_workspace',
    'seed_workspace',
    'supersede_sample_rows',
]
