"""Temporary local-development tenant boundary.

Replace with verified session/org membership before any external access.
All repository-content queries must receive an organization id from this module.
"""
import uuid

LOCAL_DEVELOPMENT_ORGANIZATION_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def current_organization_id() -> uuid.UUID:
    return LOCAL_DEVELOPMENT_ORGANIZATION_ID
