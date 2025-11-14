# src/pyaps/datamanagement/client.py
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional
import requests

from pyaps.http.client import HTTPClient, HTTPError

DEFAULT_PROJECT_BASE    = "https://developer.api.autodesk.com/project/v1"
DEFAULT_DATA_BASE       = "https://developer.api.autodesk.com/data/v1"
DEFAULT_OSS_BASE        = "https://developer.api.autodesk.com/oss/v2"

class DataManagementClient:
    """
    APS Data Management
        - project/v1    : Hubs, Projects, TopFolders
        - data/v1       : Folders, Items, Versions, Storage, Commands
        - oss/v2        : Buckets, Objects (signed upload/download)
    """
    def __init__(
        self,
        token_provider: Callable[[], str],
        *,
        project_base_url: str = DEFAULT_PROJECT_BASE,
        data_base_url: str = DEFAULT_DATA_BASE,
        oss_base_url: str = DEFAULT_OSS_BASE,
        timeout: float = 30.0,
        user_agent: str = "pyaps-dm",
        session: Optional[requests.Session] = None,
        proxies: Optional[Dict[str, str]] = None,
        trust_env: bool = True,
    ) -> None:
        """
        Args:
            token_provider: APS 액세스 토큰 제공 함수
            project_base_url: Project API base URL
            data_base_url: Data API base URL
            oss_base_url: OSS API base URL
            timeout: 요청 타임아웃 (초)
            user_agent: User-Agent 헤더 값
            session: 커스텀 requests.Session (선택)
            proxies: 프록시 설정 (선택)
            trust_env: 환경 변수에서 프록시 읽기 (기본: True)
        """
        self.http_project = HTTPClient(
            token_provider, base_url=project_base_url,
            user_agent=user_agent, timeout=timeout, session=session,
            proxies=proxies, trust_env=trust_env
        )
        self.http_data = HTTPClient(
            token_provider, base_url=data_base_url,
            user_agent=user_agent, timeout=timeout, session=session,
            proxies=proxies, trust_env=trust_env
        )
        self.http_oss = HTTPClient(
            token_provider, base_url=oss_base_url,
            user_agent=user_agent, timeout=timeout, session=session,
            proxies=proxies, trust_env=trust_env
        )

        # public facades
        self.hubs       = _Hubs(self)
        self.projects   = _Projects(self)
        self.folders    = _Folders(self)
        self.items      = _Items(self)
        self.versions   = _Versions(self)
        self.buckets    = _Buckets(self)
        self.objects    = _Objects(self)
        self.commands   = _Commands(self)

# ----------------------------
# Project v1 — Hubs / Projects / TopFolders
# ----------------------------
class _Hubs:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def list(self, *, limit: int | None = None) -> Iterable[Dict]:
        """GET /project/v1/hubs — list accessible hubs."""
        params = {"page[limit]": limit} if limit else None
        page = self.cli.http_project.get("/hubs", params=params)
        yield from self.cli.http_project.paginate(page)

    def get(self, hub_id: str) -> Dict:
        """GET /project/v1/hubs/:hub_id"""
        return self.cli.http_project.get(f"/hubs/{hub_id}")

    def list_projects(self, hub_id: str, *, limit: int | None = None) -> Iterable[Dict]:
        """GET /project/v1/hubs/:hub_id/projects — projects in a hub."""
        params = {"page[limit]": limit} if limit else None
        page = self.cli.http_project.get(f"/hubs/{hub_id}/projects", params=params)
        yield from self.cli.http_project.paginate(page)

class _Projects:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def get(self, hub_id: str, project_id: str) -> Dict:
        """GET /project/v1/hubs/:hub_id/projects/:project_id"""
        return self.cli.http_project.get(f"/hubs/{hub_id}/projects/{project_id}")

    def top_folders(self, hub_id: str, project_id: str) -> Dict:
        """GET /project/v1/hubs/:hub_id/projects/:project_id/topFolders"""
        return self.cli.http_project.get(f"/hubs/{hub_id}/projects/{project_id}/topFolders")

# ----------------------------
# Data v1 — Folders / Items / Versions / Storage / Commands
# ----------------------------
class _Folders:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def get(self, project_id: str, folder_id: str) -> Dict:
        """GET /data/v1/projects/:project_id/folders/:folder_id"""
        return self.cli.http_data.get(f"/projects/{project_id}/folders/{folder_id}")

    def contents(self, project_id: str, folder_id: str, *, limit: int | None = None, include: str | None = None) -> Iterable[Dict]:
        """GET /data/v1/projects/:project_id/folders/:folder_id/contents"""
        params: Dict[str, Any] = {}
        if limit: params["page[limit]"] = limit
        if include: params["include"] = include
        page = self.cli.http_data.get(f"/projects/{project_id}/folders/{folder_id}/contents", params=params)
        yield from self.cli.http_data.paginate(page)

    def search(self, project_id: str, folder_id: str, q: str, *, limit: int | None = None) -> Iterable[Dict]:
        """GET /data/v1/projects/:project_id/folders/:folder_id/search?q=..."""
        params: Dict[str, Any] = {"q": q}
        if limit: params["page[limit]"] = limit
        page = self.cli.http_data.get(f"/projects/{project_id}/folders/{folder_id}/search", params=params)
        yield from self.cli.http_data.paginate(page)

    def create(self, project_id: str, parent_folder_id: str, name: str, *, hidden:bool = False) -> Dict:
        """POST /data/v1/projects/:project_id/folders"""
        body = {
            "data": {
                "type": "folders",
                "attributes": {"name": name, "hidden": hidden},
                "relationships": {"parent": {"data": {"type": "folders", "id": parent_folder_id}}},
            }
        }
        resp = self.cli.http_data.post(f"/projects/{project_id}/folders", json=body)
        return (resp or {}).get("data", {})

    def patch(self, project_id: str, folder_id: str, attributes: Dict) -> Dict:
        """PATCH /data/v1/projects/:project_id/folders/:folder_id"""
        body = {"data": {"type": "folders", "id": folder_id, "attributes": attributes}}
        return self.cli.http_data.patch(f"/projects/{project_id}/folders/{folder_id}", json=body)

class _Items:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def get(self, project_id: str, item_id: str) -> Dict:
        """GET /data/v1/projects/:project_id/items/:item_id"""
        return self.cli.http_data.get(f"/projects/{project_id}/items/{item_id}")

    def list_versions(self, project_id: str, item_id: str, *, limit: int | None = None) -> Iterable[Dict]:
        """GET /data/v1/projects/:project_id/items/:item_id/versions"""
        params = {"page[limit]": limit} if limit else None
        page = self.cli.http_data.get(f"/projects/{project_id}/items/{item_id}/versions", params=params)
        yield from self.cli.http_data.paginate(page)

    def create_with_first_version(self, project_id: str, parent_folder_id: str, file_name: str, storage_urn: str) -> Dict:
        """POST /data/v1/projects/:project_id/items — create item + first version"""
        body = {
            "data": {
                "type": "items",
                "attributes": {"displayName": file_name},
                "relationships": {
                    "tip": {"data": {"type": "versions", "id": "1"}},
                    "parent": {"data": {"type": "folders", "id": parent_folder_id}},
                },
            },
            "included": [
                {"type": "versions", "id": "1", "attributes": {"name": file_name, "storageUrn": storage_urn}}
            ],
        }
        resp = self.cli.http_data.post(f"/projects/{project_id}/items", json=body)
        return (resp or {}).get("data", {})

class _Versions:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def get(self, project_id: str, version_id: str) -> Dict:
        """GET /data/v1/projects/:project_id/versions/:version_id"""
        return self.cli.http_data.get(f"/projects/{project_id}/versions/{version_id}")

    def create(self, project_id: str, item_id: str, file_name: str, storage_urn: str) -> Dict:
        """POST /data/v1/projects/:project_id/versions — create a new version for an item."""
        body = {
            "data": {
                "type": "versions",
                "attributes": {"name": file_name, "storageUrn": storage_urn},
                "relationships": {"item": {"data": {"type": "items", "id": item_id}}},
            }
        }
        resp = self.cli.http_data.post(f"/projects/{project_id}/versions", json=body)
        return (resp or {}).get("data", {})

class _Commands:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def post(self, project_id: str, payload: Dict) -> Dict:
        """POST /data/v1/projects/:project_id/commands"""
        return self.cli.http_data.post(f"/projects/{project_id}/commands", json=payload)

# ----------------------------
# OSS v2 — Objects
# ----------------------------

class _Objects:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    # ----- Storage (Data v1 → direct S3 PUT) -----
    def create_storage(self, project_id: str, target_folder_id: str, file_name: str) -> Dict:
        """POST /data/v1/projects/:project_id/storage — reserve upload target and get signed URL metadata."""
        body = {
            "data": {
                "type": "objects",
                "attributes": {"name": file_name},
                "relationships": {"target": {"data": {"type": "folders", "id": target_folder_id}}},
            }
        }
        return self.cli.http_data.post(f"/projects/{project_id}/storage", json=body)

    def upload_via_storage(self, storage_resp: Dict, payload: bytes | str | Any, *, timeout: float | None = None) -> None:
        """
        Use storage response's signed URL to upload in a single PUT.
        """
        data = (storage_resp or {}).get("data", {}) or {}
        attrs = data.get("attributes", {}) or {}
        up = attrs.get("uploadParameters", {}) or {}
        url = up.get("url") or ((data.get("links") or {}).get("signedUrl") or {}).get("href")
        print("[datamanagement/client.py] url: ", url)
        headers = up.get("headers") or {}
        if not url:
            raise HTTPError(500, "PUT", "signed-url", "No signed URL in storage response")
        self.cli.http_data.put_signed_url(url, payload, headers=headers, timeout=timeout)

    # ----- OSS v2: object metadata/details -----
    def get_details(self, bucket_key: str, object_key: str) -> Dict:
        """GET /oss/v2/buckets/:bucketKey/objects/:objectKey/details"""
        return self.cli.http_oss.get(f"/buckets/{bucket_key}/objects/{object_key}/details")

    # ----- OSS v2: delete object -----
    def delete(self, bucket_key: str, object_key: str) -> None:
        """DELETE /oss/v2/buckets/:bucketKey/objects/:objectKey"""
        self.cli.http_oss.delete(f"/buckets/{bucket_key}/objects/{object_key}")

    # ----- OSS v2: copy object (within same bucket) -----
    def copy_to(self, bucket_key: str, object_key: str, new_object_key: str) -> Dict:
        """PUT /oss/v2/buckets/:bucketKey/objects/:objectKey/copyto/:newObjectKey"""
        return self.cli.http_oss.request_json(
            "PUT",
            f"/buckets/{bucket_key}/objects/{object_key}/copyto/{new_object_key}"
        )

    # ----- OSS v2: signed S3 upload/download -----
    def get_signed_upload(self, bucket_key: str, object_key: str, *, parts: int | None = None, useAcceleration: bool | None = None) -> Dict:
        """GET /oss/v2/buckets/:bucketKey/objects/:objectKey/signeds3upload"""
        params: Dict[str, Any] = {}
        if parts is not None: params["parts"] = parts
        if useAcceleration: params["useAcceleration"] = "true"
        return self.cli.http_oss.get(f"/buckets/{bucket_key}/objects/{object_key}/signeds3upload", params=params)

    def complete_signed_upload(self, bucket_key: str, object_key: str, upload_key: str, *, size: int | None = None, etags: list[str] | None = None) -> Dict:
        """POST /oss/v2/buckets/:bucketKey/objects/:objectKey/signeds3upload"""
        body: Dict[str, Any] = {"uploadKey": upload_key}
        if size is not None: body["size"] = size
        if etags: body["eTags"] = etags
        return self.cli.http_oss.post(f"/buckets/{bucket_key}/objects/{object_key}/signeds3upload", json=body)

    def get_signed_download(self, bucket_key: str, object_key: str, *, minutes_valid: int | None = None) -> Dict:
        """GET /oss/v2/buckets/:bucketKey/objects/:objectKey/signeds3download"""
        params = {"minutesExpiration": minutes_valid} if minutes_valid else None
        return self.cli.http_oss.get(f"/buckets/{bucket_key}/objects/{object_key}/signeds3download", params=params)
    
    # ----- OSS v2: signed (proxy) upload/download ticket -----
    def post_signed(self, bucket_key: str, object_key: str, *, access: str = "readwrite", use_cookies: bool | None = None) -> Dict:
        """
        POST /oss/v2/buckets/:bucketKey/objects/:objectKey/signed
        - access: 'read', 'write', 'readwrite'
        - 반환 값은 signedUrl(단건) 혹은 signedUrls(다건) 등을 포함 (문서에 따라)
        """
        params: Dict[str, Any] = {"access": access}
        if use_cookies is True:
            params["useCookies"] = "true"
        return self.cli.http_oss.post(f"/buckets/{bucket_key}/objects/{object_key}/signed", params=params, json={})
    
    def upload_via_signed(self, signed_resp: Dict, file_path: str | bytes, *, timeout: float | None = None) -> None:
        """
        POST /signed 응답의 signedUrl(또는 signedUrls[0]) 로 실제 바이트 업로드 (HTTP PUT)
        """
        data = signed_resp or {}
        url = (data.get("signedUrl")
            or (isinstance(data.get("signedUrls"), list) and data["signedUrls"][0])
            or None)
        if not url:
            raise HTTPError(500, "PUT", "signed-url", "No signedUrl in POST /signed response")
        self.cli.http_oss.put_signed_url(url, file_path, headers={}, timeout=timeout)

# ----------------------------
# OSS v2 — Buckets
# ----------------------------
class _Buckets:
    def __init__(self, cli: DataManagementClient): self.cli = cli

    def list(self, *, region: str | None = None, limit: int | None = None) -> Iterable[Dict]:
        """GET /oss/v2/buckets — list buckets owned by the app."""
        params: Dict[str, Any] = {}
        if region: params["region"] = region
        if limit: params["page[limit]"] = limit
        page = self.cli.http_oss.get("/buckets", params=params)
        data = (page or {}).get("items") or (page or {}).get("data") or []
        for it in data:
            yield it

    def create(self, bucket_key: str, *, region: str | None = None, policy_key: str | None = None) -> Dict:
        """POST /oss/v2/buckets — create a bucket."""
        body: Dict[str, Any] = {"bucketKey": bucket_key}
        if region: body["region"] = region
        if policy_key: body["policyKey"] = policy_key
        return self.cli.http_oss.post("/buckets", json=body)

    def get(self, bucket_key: str) -> Dict:
        """GET /oss/v2/buckets/:bucketKey/details"""
        return self.cli.http_oss.get(f"/buckets/{bucket_key}/details")

    def list_objects(self, bucket_key: str, *, limit: int | None = None) -> Iterable[Dict]:
        """GET /oss/v2/buckets/:bucketKey/objects — list objects in a bucket."""
        params = {"page[limit]": limit} if limit else None
        page = self.cli.http_oss.get(f"/buckets/{bucket_key}/objects", params=params)
        data = (page or {}).get("items") or (page or {}).get("data") or []
        for it in data:
            yield it