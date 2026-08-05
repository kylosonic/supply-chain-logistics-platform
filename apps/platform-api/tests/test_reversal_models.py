"""Model-level reversal tests (TECH-18..21 / NB-18..21).

Phase 3 schema: the four reversal columns on ``payment_receipts``
(check-constrained to undo|reversed|NULL), the widened wallet status
(available|applied|voided) with ``voided_at``, and the new
``sender_fraud_flags`` table keyed (organization_id, sender_name).
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.payment_receipt import PaymentReceipt
from app.models.sender_fraud_flag import SenderFraudFlag
from app.models.wallet_credit import WalletCredit


def _org(db: Session, name: str = 'Reversal Org') -> Organization:
    org = Organization(
        name=name,
        slug=f'rev-{uuid4().hex[:10]}',
        subscription_tier='starter',
        subscription_status='trialing',
        billing_phase='free',
    )
    db.add(org)
    db.flush()
    return org


def _receipt(db: Session, org: Organization, *, status: str = 'verified') -> PaymentReceipt:
    receipt = PaymentReceipt(
        organization_id=org.id,
        file_name='receipt.png',
        content_type='image/png',
        file_size_bytes=64,
        file_data=b'\x89PNG\r\n\x1a\n' + b'0' * 64,
        file_sha256='a' * 64,
        amount_etb=Decimal('4520.00'),
        sender_name='Mulugeta Tesfaye',
        status=status,
    )
    db.add(receipt)
    db.flush()
    return receipt


def test_reversal_status_check_constraint(
    db_session: Session,
):
    """reversal_status only accepts 'undo' | 'reversed' | NULL (decision #2)."""
    org = _org(db_session)
    receipt = _receipt(db_session, org)
    receipt.reversal_status = 'bogus'
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_wallet_voided_status_allowed_and_voided_at(
    db_session: Session,
):
    """WalletCredit accepts the new 'voided' status + voided_at (decision #5)."""
    org = _org(db_session)
    receipt = _receipt(db_session, org)
    credit = WalletCredit(
        organization_id=org.id,
        receipt_id=receipt.id,
        amount_etb=Decimal('480.00'),
        status='voided',
        voided_at=datetime.now(UTC),
    )
    db_session.add(credit)
    db_session.commit()
    db_session.refresh(credit)
    assert credit.status == 'voided'
    assert credit.voided_at is not None


def test_sender_fraud_flag_org_sender_unique(
    db_session: Session,
):
    """(organization_id, sender_name) is UNIQUE; same sender in another org is fine.

    Normalization (casefold/collapse) is applied by the service layer
    before insert — the constraint guards the stored pair.
    """
    org_a = _org(db_session, 'Org A')
    org_b = _org(db_session, 'Org B')
    now = datetime.now(UTC)
    db_session.add(
        SenderFraudFlag(
            organization_id=org_a.id, sender_name='mulugeta tesfaye', fraud_risk_since=now
        )
    )
    db_session.flush()
    # Same org + identical stored sender -> unique violation
    db_session.add(
        SenderFraudFlag(
            organization_id=org_a.id, sender_name='mulugeta tesfaye', fraud_risk_since=now
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
    # Different org, same sender -> allowed
    db_session.add(
        SenderFraudFlag(
            organization_id=org_b.id, sender_name='mulugeta tesfaye', fraud_risk_since=now
        )
    )
    db_session.flush()


def test_reversal_columns_nullable_by_default(
    db_session: Session,
):
    """A fresh receipt has all four reversal columns NULL (no behavior change)."""
    org = _org(db_session)
    receipt = _receipt(db_session, org, status='pending')
    db_session.commit()
    db_session.refresh(receipt)
    assert receipt.reversal_status is None
    assert receipt.reversal_note is None
    assert receipt.reversed_by_user_id is None
    assert receipt.reversed_at is None
