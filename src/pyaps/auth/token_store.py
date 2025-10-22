# src/pyaps/auth/token_store.py
from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

@dataclass(frozen=True)
class OAuth2Token:
    """
    표준 OAuth2 토큰 컨테이너

    - expires_at: UTC ISO 8601 (e.g., "2025-09-23T01:23:45Z")
    - scope: 공백으로 구분된 스코프 문자열 (APS 관례)
    """
    access_token: str
    token_type: str
    expires_at: str
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    def is_expired(self, skew_seconds: int = 30) -> bool:
        """토큰 만료 여부 확인. 네트워크 지연 등을 고려해 skew 여유를 둠"""
        try:
            dt = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        except Exception:
            return True
        
        now = datetime.now(timezone.utc)
        return (dt.timestamp() - now.timestamp()) <= skew_seconds
    
    @staticmethod
    def from_token_response(
        resp: Dict,
        now: Optional[datetime] = None,
        default_ttl: int = 3600,
    ) -> "OAuth2Token":
        """
        APS 토큰 응답(JSON)을 OAuth2Token으로 변환.
        응답 예시:
            {
                "token_type": "Bearer",
                "access_token": "...",
                "expires_in": 3599,
                "refresh_token": "...",
                "scope": "data:read data:write"
            }
        """
        now = now or datetime.now(timezone.utc)
        expires_in = int(resp.get("expires_in") or default_ttl)
        expires_at = datetime.fromtimestamp(now.timestamp() + expires_in, tz=timezone.utc)
        return OAuth2Token(
            access_token=resp["access_token"],
            token_type=resp.get("token_type", "Bearer"),
            refresh_token=resp.get("refresh_token"),
            scope=resp.get("scope"),
            expires_at=expires_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
    
class TokenStore(ABC):
    """토큰 저장소 인터페이스"""
    
    @abstractmethod
    def read(self, key: str) -> Optional[OAuth2Token]:
        """키로 토큰을 읽기"""
        raise NotImplementedError
    @abstractmethod
    def write(self, key: str, token: OAuth2Token) -> None:
        """키에 토큰을 저장/갱신"""
        raise NotImplementedError
    @abstractmethod
    def delete(self, key: str) -> None:
        """키의 토큰을 삭제"""
        raise NotImplementedError
    @abstractmethod
    def clear(self) -> None:
        """저장소 비우기"""
        raise NotImplementedError

class InMemoryTokenStore(TokenStore):
    """프로세스 메모리 기반 저장소(스레드 세이프)"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: Dict[str, OAuth2Token] = {}
    
    def read(self, key: str) -> Optional[OAuth2Token]:
        with self._lock:
            return self._data.get(key)
    
    def write(self, key: str, token: OAuth2Token) -> None:
        with self._lock:
            self._data[key] = token
    
    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)
    
    def clear(self) -> None:
        with self._lock:
            self._data.clear()