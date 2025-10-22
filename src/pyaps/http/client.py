# src/pyaps/http/client.py
from __future__ import annotations

import io
import os
import json as _json
import time
from typing import Any, Callable, Dict, Iterable, Optional
import requests

class HTTPError(RuntimeError):
    def __init__(self, status: int, method: str, url: str, body: str | None = None):
        super().__init__(f"[{status}] {method} {url} :: {(body or '')[:1000]}")
        self.status = status
        self.method = method
        self.url = url
        self.body = body or ""

class HTTPClient:
    """
    공통 HTTP 클라이언트
    - token_provider(): APS 액세스 토큰(2/3-legged) 반환
    - base_url: 선택 (상대 경로 요청 지원)
    - 기본 JSON Accept/Content-Type 처리
    - stream/raw/text/json 응답 모드 지원
    - 간단한 재시도(backoff) 옵션
    """

    def __init__(
        self,
        token_provider: Callable[[], str],
        *,
        base_url: str | None = None,
        user_agent: str = "pyaps-http",
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._tp = token_provider
        self.base_url = base_url.rstrip("/") if base_url else None
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = session or requests.Session()
        self.default_headers = default_headers or {}

    # ------------ low-level ------------
    def _auth_headers(self, json_ct: bool = True) -> Dict[str, str]:
        h = {
            "Authorization": f"Bearer {self._tp()}",
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if json_ct:
            h["Content-Type"] = "application/json"
        if self.default_headers:
            h.update(self.default_headers)
        return h

    def _make_url(self, path_or_url: str) -> str:
        if self.base_url and not path_or_url.startswith("http"):
            return f"{self.base_url}{path_or_url}"
        return path_or_url

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        stream: bool = False,
        retries: int = 0,
        retry_wait: float = 1.5,
        retry_on: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> requests.Response:
        """
        공통 request. 재시도는 idempotent한 GET/HEAD 정도에서만 보수적으로 사용 권장.
        """
        url = self._make_url(path_or_url)
        # data = _json.dumps(json) if json is not None else None
        hdrs = self._auth_headers(json_ct=(json is not None))
        if headers:
            hdrs.update(headers)

        attempt = 0
        while True:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                headers=hdrs,
                params=params,
                # data=data,
                json=json,
                timeout=timeout or self.timeout,
                stream=stream,
            )
            if resp.status_code < 400 or attempt >= retries or resp.status_code not in retry_on:
                return resp
            attempt += 1
            time.sleep(retry_wait)

    # ------------ response helpers ------------
    def request_json(self, *args, **kwargs) -> Dict[str, Any] | list | None:
        resp = self.request(*args, **kwargs)
        if resp.status_code >= 400:
            self._raise(resp, *args, **kwargs)
        if not resp.content:
            return None
        try:
            return resp.json()
        except Exception:
            return None

    def request_text(self, *args, **kwargs) -> str:
        resp = self.request(*args, **kwargs)
        if resp.status_code >= 400:
            self._raise(resp, *args, **kwargs)
        return resp.text

    def request_raw(self, *args, **kwargs) -> bytes:
        resp = self.request(*args, **kwargs)
        if resp.status_code >= 400:
            self._raise(resp, *args, **kwargs)
        return resp.content

    def request_stream(self, *args, **kwargs) -> requests.Response:
        kwargs["stream"] = True
        resp = self.request(*args, **kwargs)
        if resp.status_code >= 400:
            self._raise(resp, *args, **kwargs)
        return resp

    def _raise(self, resp: requests.Response, method: str, path_or_url: str, **_):
        body = None
        try:
            body = resp.text
        except Exception:
            body = None
        raise HTTPError(resp.status_code, method, self._make_url(path_or_url), body)

    # ------------ verbs ------------
    def get(self, path_or_url: str, **kw):    return self.request_json("GET", path_or_url, **kw)
    def post(self, path_or_url: str, **kw):   return self.request_json("POST", path_or_url, **kw)
    def patch(self, path_or_url: str, **kw):  return self.request_json("PATCH", path_or_url, **kw)
    def delete(self, path_or_url: str, **kw): return self.request_json("DELETE", path_or_url, **kw)

    # ------------ extras ------------
    def paginate(self, first_page: dict) -> Iterable[dict]:
        """Data v2의 links.next.href 페이지네이션 헬퍼"""
        for it in first_page.get("data", []) or []:
            yield it
        next_href = ((first_page.get("links") or {}).get("next") or {}).get("href")
        while next_href:
            page = self.get(next_href)  # absolute URL 허용
            for it in page.get("data", []) or []:
                yield it
            next_href = ((page.get("links") or {}).get("next") or {}).get("href")

    def post_presigned_form(self, endpoint_url: str, form_data: Dict[str, Any], file_path: str, *, timeout: Optional[float] = None) -> None:
        """S3 presigned 'form' 업로드 (Automation AppBundle 등)"""
        p = os.fspath(file_path)
        if not os.path.exists(p):
            raise HTTPError(400, "POST", endpoint_url, f"File not found: {p}")
        with open(p, "rb") as fp:
            files = {"file": (os.path.basename(p), fp)}
            # presigned 폼은 토큰/JSON 헤더 금지
            resp = self.session.post(endpoint_url, data=form_data, files=files, headers=None, timeout=timeout or self.timeout, allow_redirects=True)
        if resp.status_code >= 400:
            raise HTTPError(resp.status_code, "POST", endpoint_url, resp.text)

    def put_signed_url(self, url: str, payload: bytes | str | Any, *, headers: Optional[dict] = None, timeout: Optional[float] = None) -> None:
        """Data v2 storage/OSS signeds3upload URL에 대한 단일 PUT 업로드"""
        stream = _to_stream(payload)
        try:
            resp = self.session.put(url, data=stream, headers=headers or {}, timeout=timeout or self.timeout)
        finally:
            if hasattr(stream, "close"):
                try: stream.close()
                except Exception: pass
        if resp.status_code >= 400:
            raise HTTPError(resp.status_code, "PUT", url, resp.text)


def _to_stream(payload):
    if hasattr(payload, "read"):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        return io.BytesIO(payload)
    if isinstance(payload, str) and os.path.exists(payload):
        return open(payload, "rb")
    raise TypeError("payload must be file path, bytes/bytearray, or BinaryIO")
