"""Receipt processing orchestrator package (TECH-07..17).

The Phase 2 receipt loop: upload intake, extraction wiring, dedup, routing,
queue/wallet read surfaces, the admin verdict state machine (blueprint §5)
and customer disputes (NB-17). Pessimistic everywhere: no credit, no wallet
movement, no phase change happens at upload; all of it happens in the admin
verdict path (``verdicts.render_verdict`` / ``disputes.resolve_dispute``).

WRITE-GUARD EXEMPTION (blueprint decision #1 — deliberate carve-out, not an
omission): these services back the upload, dispute, queue-read, and
verdict-render endpoints, which do NOT depend on ``require_writable_workspace``.
A hard-locked workspace MUST remain payable — that is the feature's purpose.
The exemption is documented at the endpoint layer (``api/endpoints/receipts.py``)
and honored here by design.

Imports: models, audit, schemas, and the billing submodules — NEVER
``app.api`` (Phase 1 rule preserved). Package layout keeps every module
<= 400 lines (blueprint §2.2):

- ``intake``    — upload, format/size validation, sha256, extraction trigger,
                  dedup, routing, flags, shared banner builders
- ``queue``     — customer + admin read surfaces and the queue-item payload
- ``verdicts``  — the admin verdict state machine (the ONLY credit path)
- ``disputes``  — submit_dispute / resolve_dispute
"""

from __future__ import annotations

from app.services.billing.receipts.intake import (  # noqa: F401
    DUPLICATE_BANNER,
    DUPLICATE_REASON,
    ILLEGIBLE_REASON,
    NO_OPEN_INVOICE_MESSAGE,
    UNSUPPORTED_FORMAT_MESSAGE,
    UPLOAD_CONFIRMATION_MESSAGE,
    WRONG_BANK_REASON,
    ReceiptVerdictError,
    recommended_verdict,
    upload_receipt,
)
from app.services.billing.receipts.queue import (  # noqa: F401
    get_queue_item,
    list_customer_receipts,
    list_queue,
    list_wallet,
    queue_item_payload,
)
from app.services.billing.receipts.verdicts import (  # noqa: F401
    has_open_dispute,
    render_verdict,
)
from app.services.billing.receipts.disputes import (  # noqa: F401
    resolve_dispute,
    submit_dispute,
)
