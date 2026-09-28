from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.storage.errors import StorageError
from app.storage.paths import validate_storage_path


class SupabaseStorageService:
    def __init__(self, settings: Settings, client: httpx.Client) -> None:
        self._settings = settings
        self._client = client

    def _credentials(self) -> tuple[str, str]:
        if not self._settings.supabase_url:
            raise StorageError("Supabase Storage URL is not configured")
        if not self._settings.supabase_service_role_key:
            raise StorageError(
                "Supabase Storage backend credentials are not configured")
        return (
            self._settings.supabase_url,
            self._settings.supabase_service_role_key.get_secret_value(),
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        operation: str,
        *,
        allow_statuses: frozenset[int] = frozenset(),
        **kwargs: object,
    ) -> httpx.Response:
        base_url, service_key = self._credentials()
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            **kwargs.pop("headers", {}),  # type: ignore[arg-type]
        }
        try:
            response = self._client.request(
                method,
                f"{base_url}/storage/v1/{endpoint}",
                headers=headers,
                **kwargs,
            )
        except httpx.RequestError:
            raise StorageError(f"Storage {operation} request failed") from None
        if not response.is_success and response.status_code not in allow_statuses:
            raise StorageError(
                f"Storage {operation} failed (HTTP {response.status_code})"
            )
        return response

    def _object_endpoint(self, object_path: str) -> str:
        validate_storage_path(object_path)
        bucket = quote(self._settings.supabase_storage_bucket, safe="")
        path = quote(object_path, safe="/")
        return f"object/{bucket}/{path}"

    def upload(
        self, object_path: str, content: bytes, content_type: str
    ) -> None:
        endpoint = self._object_endpoint(object_path)
        self._request(
            "POST",
            endpoint,
            "upload",
            content=content,
            headers={"Content-Type": content_type, "x-upsert": "false"},
        )

    def download(self, object_path: str) -> bytes:
        endpoint = self._object_endpoint(object_path)
        bucket, path = endpoint.split("/", maxsplit=2)[1:]
        response = self._request(
            "GET",
            f"object/authenticated/{bucket}/{path}",
            "download",
        )
        return response.content

    def delete(self, object_path: str) -> None:
        validate_storage_path(object_path)
        bucket = quote(self._settings.supabase_storage_bucket, safe="")
        self._request(
            "DELETE",
            f"object/{bucket}",
            "delete",
            json={"prefixes": [object_path]},
        )
