from pathlib import Path

from backend.config import settings

_LOCAL_UPLOAD_DIR = Path(__file__).parent.parent / ".local-uploads"


def _upload_local(key: str, data: bytes) -> str:
    dest = _LOCAL_UPLOAD_DIR / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return key


def _upload_gcs(key: str, data: bytes, content_type: str) -> str:
    from google.cloud import storage  # deferred so dev mode never imports it

    client = storage.Client()
    bucket = client.bucket(settings.gcs_bucket)
    blob = bucket.blob(key)
    blob.upload_from_string(data, content_type=content_type)
    return key


def upload_bytes(key: str, data: bytes, content_type: str) -> str:
    """Upload bytes to GCS (prod) or local disk (dev_mode). Returns the key."""
    if settings.dev_mode:
        return _upload_local(key, data)
    return _upload_gcs(key, data, content_type)


def download_bytes(key: str) -> bytes:
    """Download bytes from GCS (prod) or local disk (dev_mode)."""
    if settings.dev_mode:
        return (_LOCAL_UPLOAD_DIR / key).read_bytes()
    from google.cloud import storage  # deferred so dev mode never imports it

    client = storage.Client()
    blob = client.bucket(settings.gcs_bucket).blob(key)
    return blob.download_as_bytes()
