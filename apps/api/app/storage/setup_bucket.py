import sys

import httpx

from app.core.config import Settings
from app.storage.errors import StorageError
from app.storage.service import SupabaseStorageService


def create_private_bucket(settings: Settings, client: httpx.Client) -> bool:
    service = SupabaseStorageService(settings, client)
    bucket = settings.supabase_storage_bucket
    quoted_bucket = httpx.URL(
        "/").copy_with(path=f"/{bucket}").raw_path.decode()[1:]
    response = service._request(
        "GET",
        f"bucket/{quoted_bucket}",
        "bucket inspection",
        allow_statuses=frozenset({400, 404}),
    )
    bucket_missing = response.status_code == 404
    if response.status_code == 400:
        try:
            error_payload = response.json()
        except (ValueError, TypeError):
            error_payload = None
        bucket_missing = (
            isinstance(error_payload, dict)
            and error_payload.get("code") == "NoSuchBucket"
        )
        if not bucket_missing:
            raise StorageError("Storage bucket inspection failed (HTTP 400)")

    if bucket_missing:
        service._request(
            "POST",
            "bucket",
            "bucket creation",
            json={"id": bucket, "name": bucket, "public": False},
        )
        return True

    try:
        bucket_settings = response.json()
    except (ValueError, TypeError):
        raise StorageError(
            "Storage bucket settings could not be verified") from None
    if not isinstance(bucket_settings, dict) or bucket_settings.get("public") is not False:
        raise StorageError("Configured Storage bucket must be private")
    return False


def main() -> int:
    settings = Settings()
    if settings.app_env != "development":
        print("Bucket setup is restricted to APP_ENV=development", file=sys.stderr)
        return 2
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            created = create_private_bucket(settings, client)
    except StorageError as error:
        print(str(error), file=sys.stderr)
        return 1
    status = "Created" if created else "Verified existing private"
    print(f"{status} Storage bucket: {settings.supabase_storage_bucket}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
