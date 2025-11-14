# src/pyaps/automation/client.py
from __future__ import annotations
from typing import Any, Callable, Dict, Literal, Optional
from pathlib import Path
import requests

from pyaps.http.client import HTTPClient, HTTPError  # ← 공용 모듈 사용

AutomationRegion = Literal["us-east", "eu-west"]

DEFAULT_AUTOMATION_SCOPES = [
    "code:all", "data:read", "data:write", "data:create", "bucket:read", "bucket:create", "bucket:update",
]

class AutomationError(RuntimeError):
    def __init__(self, message: str, status: int, payload: Any | None = None):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.payload = payload

class AutomationClient:
    def __init__(
        self,
        token_provider: Callable[[], str],
        *,
        region: AutomationRegion = "us-east",
        user_agent: str = "pyaps-automation",
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
        proxies: Optional[Dict[str, str]] = None,
        trust_env: bool = True,
    ) -> None:
        """
        Args:
            token_provider: APS 액세스 토큰 제공 함수
            region: Design Automation 리전 (us-east, eu-west)
            user_agent: User-Agent 헤더 값
            timeout: 요청 타임아웃 (초)
            session: 커스텀 requests.Session (선택)
            proxies: 프록시 설정 (선택)
            trust_env: 환경 변수에서 프록시 읽기 (기본: True)
        """
        base_url = f"https://developer.api.autodesk.com/da/{region}/v3"
        self.http = HTTPClient(
            token_provider,
            base_url=base_url,
            user_agent=user_agent,
            timeout=timeout,
            session=session,
            proxies=proxies,
            trust_env=trust_env,
        )

    # ------- ForgeApps -------
    def get_me(self) -> Dict[str, Any]:
        return self.http.get("/forgeapps/me")

    # ------- Engines -------
    def list_engines(self, *, page: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if page is not None: params["page"] = page
        if page_size is not None: params["pageSize"] = page_size
        return self.http.get("/engines", params=params or None)

    # ------- AppBundles -------
    def create_appbundle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post("/appbundles", json=payload)

    def list_appbundles(self) -> Dict[str, Any]:
        return self.http.get("/appbundles")

    def get_appbundle(self, appbundle_id: str) -> Dict[str, Any]:
        return self.http.get(f"/appbundles/{appbundle_id}")

    def delete_appbundle(self, appbundle_id: str) -> None:
        self.http.delete(f"/appbundles/{appbundle_id}")

    def create_appbundle_alias(self, appbundle_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post(f"/appbundles/{appbundle_id}/aliases", json=payload)

    def list_appbundle_aliases(self, appbundle_id: str) -> Dict[str, Any]:
        return self.http.get(f"/appbundles/{appbundle_id}/aliases")

    def get_appbundle_alias_detail(self, appbundle_id: str, alias: str) -> Dict[str, Any]:
        return self.http.get(f"/appbundles/{appbundle_id}/aliases/{alias}")

    def set_appbundle_alias(self, appbundle_id: str, alias: str, *, version: int) -> Dict[str, Any]:
        return self.http.patch(f"/appbundles/{appbundle_id}/aliases/{alias}", json={"version": version})

    def delete_appbundle_alias(self, appbundle_id: str, alias: str):
        self.http.delete(f"/appbundles/{appbundle_id}/aliases/{alias}")

    def create_appbundle_version(self, appbundle_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post(f"/appbundles/{appbundle_id}/versions", json=payload)

    def list_appbundle_versions(self, appbundle_id: str) -> Dict[str, Any]:
        return self.http.get(f"/appbundles/{appbundle_id}/versions")

    def get_appbundle_version_detail(self, appbundle_id: str, version: str) -> Dict[str, Any]:
        return self.http.get(f"/appbundles/{appbundle_id}/versions/{version}")

    def delete_appbundle_version(self, appbundle_id: str, version: str):
        self.http.delete(f"/appbundles/{appbundle_id}/versions/{version}")

    # Presigned form upload (S3)
    def upload_form_file(self, upload_parameters: Dict[str, Any], file_path: str | Path, *, timeout: Optional[float] = None) -> None:
        endpoint = (upload_parameters or {}).get("endpointURL")
        form_data = (upload_parameters or {}).get("formData")
        if not endpoint or not form_data:
            raise AutomationError("endpointURL/formData missing in uploadParameters", 400, upload_parameters)
        try:
            self.http.post_presigned_form(endpoint, form_data, str(file_path), timeout=timeout)
        except HTTPError as e:
            raise AutomationError("Upload failed", e.status, e.body)

    def upload_appbundle_zip_from_create(self, create_response: Dict[str, Any], zip_path: str | Path, *, timeout: Optional[float] = None) -> None:
        self.upload_form_file(create_response.get("uploadParameters"), zip_path, timeout=timeout)

    def upload_appbundle_zip_from_version(self, version_response: Dict[str, Any], zip_path: str | Path, *, timeout: Optional[float] = None) -> None:
        self.upload_form_file(version_response.get("uploadParameters"), zip_path, timeout=timeout)

    # ------- Activities -------
    def create_activity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post("/activities", json=payload)

    def list_activities(self) -> Dict[str, Any]:
        return self.http.get("/activities")

    def get_activity(self, activity_id: str) -> Dict[str, Any]:
        return self.http.get(f"/activities/{activity_id}")

    def delete_activity(self, activity_id: str):
        self.http.delete(f"/activities/{activity_id}")

    def create_activity_alias(self, activity_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post(f"/activities/{activity_id}/aliases", json=payload)

    def list_activity_aliases(self, activity_id: str) -> Dict[str, Any]:
        return self.http.get(f"/activities/{activity_id}/aliases")

    def get_activity_alias_detail(self, activity_id: str, alias: str) -> Dict[str, Any]:
        return self.http.get(f"/activities/{activity_id}/aliases/{alias}")

    def set_activity_alias(self, activity_id: str, alias: str, *, version: int) -> Dict[str, Any]:
        return self.http.patch(f"/activities/{activity_id}/aliases/{alias}", json={"version": version})

    def delete_activity_alias(self, activity_id: str, alias: str):
        self.http.delete(f"/activities/{activity_id}/aliases/{alias}")

    def create_activity_version(self, activity_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.post(f"/activities/{activity_id}/versions", json=payload)

    def list_activity_versions(self, activity_id: str) -> Dict[str, Any]:
        return self.http.get(f"/activities/{activity_id}/versions")

    def get_activity_version(self, activity_id: str, version: int) -> Dict[str, Any]:
        return self.http.get(f"/activities/{activity_id}/versions/{version}")

    def delete_activity_version(self, activity_id: str, version: int):
        self.http.delete(f"/activities/{activity_id}/versions/{version}")

    # ------- WorkItems -------
    def start_workitem(self, spec: "WorkItemSpec | Dict[str, Any]") -> Dict[str, Any]:
        body = spec.to_dict() if hasattr(spec, "to_dict") else spec
        return self.http.post("/workitems", json=body)

    def get_workitem(self, workitem_id: str) -> Dict[str, Any]:
        return self.http.get(f"/workitems/{workitem_id}")

    def cancel_workitem(self, workitem_id: str) -> None:
        self.http.delete(f"/workitems/{workitem_id}")

    def create_workitems_batch(self, workitems: "list[dict] | list[WorkItemSpec]") -> dict:
        def _to_dict(wi): return wi.to_dict() if hasattr(wi, "to_dict") else wi
        payload = [_to_dict(w) for w in workitems]
        return self.http.post("/workitems/batch", json=payload)

    def get_workitems_status(self, ids: "list[str]") -> dict:
        return self.http.post("/workitems/status", json=ids)

    def combine_workitems(self, payload: dict) -> dict:
        return self.http.post("/workitems/combine", json=payload)

    # ------- ServiceLimits -------
    def get_service_limits(self, owner: str) -> Dict[str, Any]:
        return self.http.get(f"/servicelimits/{owner}")

    def put_service_limits(self, owner: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.http.request_json("PUT", f"/servicelimits/{owner}", json=payload)