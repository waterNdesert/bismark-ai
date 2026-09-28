import re
import unicodedata
from uuid import UUID


def _canonical_uuid(value: UUID | str, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{name} must be a valid UUID") from None


def sanitize_filename(original_filename: str) -> str:
    if not isinstance(original_filename, str):
        raise ValueError("filename must be a string")

    normalized = unicodedata.normalize("NFKC", original_filename)
    if not normalized.strip() or normalized.endswith(("/", "\\")):
        raise ValueError("filename must not be empty")

    flattened = re.sub(r"[\\/]+", "_", normalized)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", flattened)
    safe_name = re.sub(r"\.{2,}", "_", safe_name).strip("._-")
    if not safe_name:
        raise ValueError("filename must not be empty")
    return safe_name[:255]


def build_storage_path(
    organization_id: UUID | str,
    workspace_id: UUID | str,
    document_id: UUID | str,
    original_filename: str,
) -> str:
    organization = _canonical_uuid(organization_id, "organization_id")
    workspace = _canonical_uuid(workspace_id, "workspace_id")
    document = _canonical_uuid(document_id, "document_id")
    filename = sanitize_filename(original_filename)
    return (
        f"organizations/{organization}/workspaces/{workspace}"
        f"/documents/{document}/{filename}"
    )


def validate_storage_path(path: str) -> str:
    parts = path.split("/") if isinstance(path, str) else []
    if (
        len(parts) != 7
        or parts[0] != "organizations"
        or parts[2] != "workspaces"
        or parts[4] != "documents"
    ):
        raise ValueError("storage path must use the tenant document namespace")

    expected_ids = (
        (parts[1], "organization_id"),
        (parts[3], "workspace_id"),
        (parts[5], "document_id"),
    )
    for value, name in expected_ids:
        if _canonical_uuid(value, name) != value:
            raise ValueError(f"{name} must use canonical UUID format")
    if sanitize_filename(parts[6]) != parts[6]:
        raise ValueError("storage filename must be sanitized")
    return path
