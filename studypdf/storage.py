import mimetypes
from pathlib import Path

import requests

from studypdf.config import STUDYPDF_STORAGE_BUCKET, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL


APPLICATION_JSON = "application/json"


class StorageError(RuntimeError):
    pass


def ensure_storage_configured():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not STUDYPDF_STORAGE_BUCKET:
        raise StorageError("Defina SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e STUDYPDF_STORAGE_BUCKET.")


def storage_headers(content_type=None):
    ensure_storage_configured()
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def storage_url(path=""):
    ensure_storage_configured()
    path = path.strip("/")
    base = f"{SUPABASE_URL}/storage/v1"
    return f"{base}/{path}" if path else base


def ensure_bucket():
    response = requests.get(
        storage_url(f"bucket/{STUDYPDF_STORAGE_BUCKET}"),
        headers=storage_headers(),
        timeout=30,
    )
    if response.status_code == 200:
        return
    if response.status_code != 404:
        raise_storage_error(response, "Nao foi possivel verificar o bucket do Supabase Storage.")

    response = requests.post(
        storage_url("bucket"),
        headers=storage_headers(APPLICATION_JSON),
        json={"id": STUDYPDF_STORAGE_BUCKET, "name": STUDYPDF_STORAGE_BUCKET, "public": False},
        timeout=30,
    )
    if response.status_code not in {200, 201}:
        raise_storage_error(response, "Nao foi possivel criar o bucket do Supabase Storage.")


def upload_bytes(key, content, content_type="application/octet-stream"):
    ensure_bucket()
    response = requests.post(
        storage_url(f"object/{STUDYPDF_STORAGE_BUCKET}/{key}"),
        headers={**storage_headers(content_type), "x-upsert": "true"},
        data=content,
        timeout=120,
    )
    if response.status_code not in {200, 201}:
        raise_storage_error(response, f"Nao foi possivel enviar arquivo para Storage: {key}")
    return key


def upload_file(key, path, content_type=None):
    path = Path(path)
    guessed_type = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return upload_bytes(key, path.read_bytes(), guessed_type)


def download_bytes(key):
    response = requests.get(
        storage_url(f"object/{STUDYPDF_STORAGE_BUCKET}/{key}"),
        headers=storage_headers(),
        timeout=120,
    )
    if response.status_code != 200:
        raise_storage_error(response, f"Nao foi possivel baixar arquivo do Storage: {key}")
    return response.content


def download_file(key, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(download_bytes(key))
    return path


def delete_keys(keys):
    keys = [key for key in keys if key]
    if not keys:
        return
    response = requests.delete(
        storage_url(f"object/{STUDYPDF_STORAGE_BUCKET}"),
        headers=storage_headers(APPLICATION_JSON),
        json={"prefixes": keys},
        timeout=60,
    )
    if response.status_code not in {200, 204}:
        raise_storage_error(response, "Nao foi possivel remover arquivos do Supabase Storage.")


def list_keys(prefix):
    response = requests.post(
        storage_url(f"object/list/{STUDYPDF_STORAGE_BUCKET}"),
        headers=storage_headers(APPLICATION_JSON),
        json={"prefix": prefix.strip("/"), "limit": 1000, "offset": 0, "sortBy": {"column": "name", "order": "asc"}},
        timeout=60,
    )
    if response.status_code != 200:
        raise_storage_error(response, f"Nao foi possivel listar arquivos do Storage: {prefix}")
    return [f"{prefix.rstrip('/')}/{item['name']}" for item in response.json() if item.get("name")]


def delete_prefix(prefix):
    delete_keys(list_keys(prefix))


def raise_storage_error(response, message):
    detail = response.text[:500] if response.text else response.reason
    raise StorageError(f"{message} Status {response.status_code}: {detail}")
