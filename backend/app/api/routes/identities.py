"""Lightweight identity listing/management (PRD section 10: Admin/Identity Detail, OPTIONAL).

No authentication is enforced yet — this is the P1 admin surface without the
RBAC wrapper. Do not expose this route publicly without adding authorization.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_identity_repository
from app.repositories.identity_repository import IdentityRepository
from app.schemas.recognition import IdentityOut

router = APIRouter(prefix="/api/v1", tags=["identities"])


@router.get("/identities", response_model=list[IdentityOut])
def list_identities(repository: IdentityRepository = Depends(get_identity_repository)) -> list[IdentityOut]:
    identities = repository.list_identities()
    return [
        IdentityOut(
            id=i.id,
            display_name=i.display_name,
            created_at=i.created_at,
            sample_count=len(i.embeddings),
        )
        for i in identities
    ]


@router.delete("/identities/{identity_id}", status_code=204, response_model=None)
def delete_identity(
    identity_id: uuid.UUID, repository: IdentityRepository = Depends(get_identity_repository)
) -> None:
    deleted = repository.delete_identity(identity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Identity not found.")
