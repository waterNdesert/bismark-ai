import logging
import re
from datetime import datetime
from typing import Annotated, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth.dependencies import current_user
from app.auth.organizations import OrganizationRole, require_organization_membership
from app.auth.verifier import Principal
from app.auth.workspaces import WorkspaceRole, require_workspace_membership
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import Document, KnowledgeSource
from app.storage.paths import build_storage_path
from app.storage.service import SupabaseStorageService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])
MIME_TYPE_PATTERN = re.compile(r"^[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+$")


class DocumentUploadResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    original_filename: str
    mime_type: str | None
    size_bytes: int | None
    status: str
    created_at: datetime


def _upload_error(status: int, code: str, message: str) -> ApiError:
    return ApiError(status, code, message)


@router.post(
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
)
async def upload_document(
    request: Request,
    response: Response,
    organization_id: UUID,
    workspace_id: UUID,
    principal: Annotated[Principal, Depends(current_user)],
    organization_role: Annotated[
        OrganizationRole, Depends(require_organization_membership)
    ],
    workspace_role: Annotated[
        WorkspaceRole, Depends(require_workspace_membership)
    ],
) -> DocumentUploadResponse:
    del organization_role, workspace_role
    response.headers["Cache-Control"] = "no-store"

    if not request.headers.get("content-type", "").lower().startswith(
        "multipart/form-data"
    ):
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "A multipart file is required.")
    try:
        async with request.form() as form:
            files = form.getlist("file")
            if (
                set(form.keys()) != {"file"}
                or len(files) != 1
                or not isinstance(files[0], UploadFile)
            ):
                raise _upload_error(
                    400, "DOCUMENT_UPLOAD_INVALID", "A file is required.")
            return await _persist_uploaded_file(
                request,
                organization_id,
                workspace_id,
                principal,
                files[0],
            )
    except StarletteHTTPException:
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "A valid multipart file is required.") from None


async def _persist_uploaded_file(
    request: Request,
    organization_id: UUID,
    workspace_id: UUID,
    principal: Principal,
    file: UploadFile,
) -> DocumentUploadResponse:
    if file is None:
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "A file is required.")
    original_filename = file.filename
    if (
        not isinstance(original_filename, str)
        or not original_filename.strip()
        or any(ord(character) < 32 for character in original_filename)
    ):
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "A valid filename is required.")

    settings = cast(Settings, request.app.state.settings)
    content_type = file.content_type
    mime_type = content_type.split(";", maxsplit=1)[
        0].strip().lower() if content_type else ""
    if (
        not MIME_TYPE_PATTERN.fullmatch(mime_type)
        or mime_type not in settings.allowed_upload_mime_type_set
    ):
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "The file type is not supported.")

    session_factory = cast(
        sessionmaker[Session] | None, request.app.state.session_factory
    )
    if session_factory is None:
        raise _upload_error(503, "DATABASE_UNAVAILABLE",
                            "Document storage is unavailable.")
    storage = cast(
        SupabaseStorageService | None,
        getattr(request.app.state, "storage_service", None),
    )
    if storage is None:
        raise _upload_error(503, "STORAGE_UNAVAILABLE",
                            "Document storage is unavailable.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        raise _upload_error(413, "DOCUMENT_TOO_LARGE",
                            "The file exceeds the upload limit.")
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise _upload_error(413, "DOCUMENT_TOO_LARGE",
                            "The file exceeds the upload limit.")

    document_id = uuid4()
    try:
        storage_path = build_storage_path(
            organization_id,
            workspace_id,
            document_id,
            original_filename,
        )
    except ValueError:
        raise _upload_error(400, "DOCUMENT_UPLOAD_INVALID",
                            "A valid filename is required.") from None

    uploaded = False
    try:
        with session_factory() as session:
            try:
                source_query = select(KnowledgeSource).where(
                        KnowledgeSource.organization_id == organization_id,
                        KnowledgeSource.workspace_id == workspace_id,
                        KnowledgeSource.source_type == "manual_upload",
                        KnowledgeSource.deleted_at.is_(None),
                    ).order_by(KnowledgeSource.created_at, KnowledgeSource.id).limit(1)
                source = session.scalar(source_query)
                if source is None:
                    source = KnowledgeSource(
                        id=uuid4(),
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        created_by=principal.id,
                        source_type="manual_upload",
                        name="Manual Upload",
                        status="active",
                    )
                    try:
                        with session.begin_nested():
                            session.add(source)
                            session.flush()
                    except IntegrityError as exc:
                        if (
                            getattr(exc.orig, "sqlstate", None) != "23505"
                            or getattr(getattr(exc.orig, "diag", None),
                                       "constraint_name", None)
                            != "uq_knowledge_sources_manual_upload_workspace"
                        ):
                            raise
                        source = session.scalar(source_query)
                if source is None or source.status != "active":
                    raise _upload_error(
                        409, "SOURCE_UNAVAILABLE",
                        "The upload source is unavailable.",
                    )
                try:
                    storage.upload(storage_path, content, mime_type)
                except Exception:
                    raise _upload_error(
                        502, "STORAGE_UPLOAD_FAILED",
                        "Document storage is unavailable.",
                    ) from None
                uploaded = True
                document = Document(
                    id=document_id,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    uploaded_by=principal.id,
                    source_id=source.id,
                    original_filename=original_filename,
                    storage_bucket=settings.supabase_storage_bucket,
                    storage_path=storage_path,
                    mime_type=mime_type,
                    size_bytes=len(content),
                    status="uploaded",
                )
                session.add(document)
                session.flush()
                result = DocumentUploadResponse(
                    id=document.id,
                    organization_id=document.organization_id,
                    workspace_id=document.workspace_id,
                    original_filename=document.original_filename,
                    mime_type=document.mime_type,
                    size_bytes=document.size_bytes,
                    status=document.status,
                    created_at=document.created_at,
                )
                session.commit()
            except Exception:
                try:
                    session.rollback()
                except Exception:
                    pass
                raise
    except ApiError:
        raise
    except Exception:
        try:
            if uploaded:
                storage.delete(storage_path)
        except Exception:
            logger.error(
                "document_storage_cleanup_failed document_id=%s", document_id)
        logger.error(
            "document_metadata_persist_failed document_id=%s", document_id)
        raise _upload_error(500, "DOCUMENT_SAVE_FAILED",
                            "The document could not be saved.") from None

    return result
