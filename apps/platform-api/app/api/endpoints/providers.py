from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import get_current_membership, get_current_user, require_org_roles
from app.db.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.provider_key import ProviderApiKey
from app.models.user import User
from app.schemas.auth import OrganizationRole
from app.schemas.provider import (
    ProviderKeyCreateRequest,
    ProviderPreferenceRead,
    ProviderPreferenceRequest,
    ProviderKeyRead,
    ProviderKeyRevokeRequest,
    ProviderKeyTestResponse,
)
from app.services.security import decrypt_provider_key, encrypt_provider_key, mask_provider_key

router = APIRouter()


@router.get('/keys', response_model=list[ProviderKeyRead])
def list_provider_keys(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    rows = db.execute(
        select(ProviderApiKey)
        .where(ProviderApiKey.organization_id == membership.organization_id)
        .order_by(ProviderApiKey.created_at.desc())
    ).scalars().all()
    return rows


@router.post('/keys', response_model=ProviderKeyRead, status_code=201)
def create_provider_key(
    payload: ProviderKeyCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership: OrganizationMembership = Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)),
):
    duplicate = db.execute(
        select(ProviderApiKey).where(
            ProviderApiKey.organization_id == membership.organization_id,
            ProviderApiKey.provider_name == payload.provider_name,
            ProviderApiKey.key_name == payload.key_name,
            ProviderApiKey.status == 'active',
        )
    ).scalar_one_or_none()
    if duplicate:
        raise HTTPException(status_code=409, detail='An active key with this name already exists for the provider')

    api_key = payload.api_key.strip()
    key = ProviderApiKey(
        organization_id=membership.organization_id,
        created_by_user_id=user.id,
        provider_name=payload.provider_name.strip().lower(),
        key_name=payload.key_name.strip(),
        masked_key=mask_provider_key(api_key),
        encrypted_key=encrypt_provider_key(api_key),
        status='active',
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


@router.post('/keys/{key_id}/revoke', response_model=ProviderKeyRead)
def revoke_provider_key(
    key_id: str,
    _: ProviderKeyRevokeRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)),
):
    key = db.get(ProviderApiKey, key_id)
    if not key or key.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Provider key not found')

    key.status = 'revoked'
    key.revoked_at = datetime.now(UTC)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


@router.post('/keys/{key_id}/test', response_model=ProviderKeyTestResponse)
def test_provider_key(
    key_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    key = db.get(ProviderApiKey, key_id)
    if not key or key.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Provider key not found')

    if key.status != 'active':
        return ProviderKeyTestResponse(
            key_id=key.id,
            provider_name=key.provider_name,
            ok=False,
            message='Key is not active',
        )

    decrypted = decrypt_provider_key(key.encrypted_key)
    is_valid_shape = len(decrypted.strip()) >= 12
    return ProviderKeyTestResponse(
        key_id=key.id,
        provider_name=key.provider_name,
        ok=is_valid_shape,
        message='Key format looks valid' if is_valid_shape else 'Key appears invalid',
    )


@router.get('/preference', response_model=ProviderPreferenceRead)
def get_provider_preference(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    return ProviderPreferenceRead(
        organization_id=organization.id,
        provider_name=organization.preferred_ai_provider,
        key_id=organization.preferred_ai_key_id,
    )


@router.post('/preference', response_model=ProviderPreferenceRead)
def set_provider_preference(
    payload: ProviderPreferenceRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN)),
):
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail='Organization not found')

    key = db.get(ProviderApiKey, payload.key_id)
    if not key or key.organization_id != membership.organization_id:
        raise HTTPException(status_code=404, detail='Provider key not found')
    if key.status != 'active':
        raise HTTPException(status_code=400, detail='Only active keys can be selected')

    organization.preferred_ai_provider = key.provider_name
    organization.preferred_ai_key_id = key.id
    db.add(organization)
    db.commit()
    db.refresh(organization)

    return ProviderPreferenceRead(
        organization_id=organization.id,
        provider_name=organization.preferred_ai_provider,
        key_id=organization.preferred_ai_key_id,
    )
