# src/pyaps/auth/client.py
from __future__ import annotations

import base64
import hashlib
import os
import urllib.parse
from typing import Any, Callable, Dict, Iterable, Optional

import requests

from pyaps.http.client import HTTPClient
from pyaps.auth.token_store import OAuth2Token, TokenStore

DEFAULT_AUTH_BASE = "https://developer.api.autodesk.com/authentication/v2"
DEFAULT_USERPROFILE_BASE = "https://api.userprofile.autodesk.com"


class AuthClient:
    """
    APS Authentication API 클라이언트
        - OAuth 2.0: 2-legged (Client Credentials) / 3-legged (Authorization Code + PKCE)
        - Token Management: refresh, revoke, cache
        - User Profile: OIDC UserInfo endpoint
    """

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        *,
        redirect_uri: Optional[str] = None,
        store: Optional[TokenStore] = None,
        auth_base_url: str = DEFAULT_AUTH_BASE,
        userprofile_base_url: str = DEFAULT_USERPROFILE_BASE,
        timeout: float = 15.0,
        user_agent: str = "pyaps-auth",
        cache_prefix: str = "aps",
        session: Optional[requests.Session] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.store = store
        self.cache_prefix = cache_prefix
        self.timeout = timeout

        # HTTPClient for API calls that need authentication (e.g., userinfo)
        def _token_provider() -> str:
            # This is a placeholder - userinfo endpoint needs 3-legged token from outside
            raise NotImplementedError("Token provider must be set externally for authenticated endpoints")

        self.http_auth = HTTPClient(
            _token_provider,
            base_url=auth_base_url,
            user_agent=user_agent,
            timeout=timeout,
            session=session,
        )
        self.http_userprofile = HTTPClient(
            _token_provider,
            base_url=userprofile_base_url,
            user_agent=user_agent,
            timeout=timeout,
            session=session,
        )

        # Public facades
        self.two_legged = _TwoLegged(self)
        self.three_legged = _ThreeLegged(self)
        self.tokens = _Tokens(self)
        self.user = _User(self)

    def _get_session(self) -> requests.Session:
        """Get the underlying requests session"""
        return self.http_auth.session


# ----------------------------
# 2-Legged (Client Credentials)
# ----------------------------
class _TwoLegged:
    """2-legged OAuth (Client Credentials) flow"""

    def __init__(self, client: AuthClient):
        self.client = client

    def get_token(self, scopes: Iterable[str]) -> OAuth2Token:
        """
        Get or fetch a 2-legged access token.
        Cache key: f"{prefix}:2l:{client_id}:{scope_string}"
        """
        if not self.client.client_secret:
            raise ValueError("2-legged flow requires client_secret")

        scope_str = _join_scopes(scopes)
        cache_key = f"{self.client.cache_prefix}:2l:{self.client.client_id}:{scope_str}"

        # Check cache
        token = self._read_cache(cache_key)
        if token and not token.is_expired():
            return token

        # Fetch new token
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client.client_id,
            "client_secret": self.client.client_secret,
        }
        if scope_str:
            data["scope"] = scope_str

        resp = self._post_token(data)
        token = OAuth2Token.from_token_response(resp, now=_now_utc())

        self._write_cache(cache_key, token)
        return token

    def _post_token(self, data: Dict[str, Any]) -> Dict:
        """POST to /token endpoint"""
        session = self.client._get_session()
        url = f"{self.client.http_auth.base_url}/token"
        resp = session.post(url, data=data, timeout=self.client.timeout)
        resp.raise_for_status()
        return resp.json()

    def _read_cache(self, key: str) -> Optional[OAuth2Token]:
        if not self.client.store:
            return None
        return self.client.store.read(key)

    def _write_cache(self, key: str, token: OAuth2Token) -> None:
        if self.client.store:
            self.client.store.write(key, token)


# ----------------------------
# 3-Legged (Authorization Code + PKCE)
# ----------------------------
class _ThreeLegged:
    """3-legged OAuth (Authorization Code) flow with optional PKCE"""

    def __init__(self, client: AuthClient):
        self.client = client

    def generate_pkce_pair(self, length: int = 64) -> tuple[str, str]:
        """
        Generate PKCE code_verifier and code_challenge (S256).
        RFC 7636: verifier must be 43-128 characters.
        """
        if not 43 <= length <= 128:
            raise ValueError("PKCE verifier length must be between 43 and 128")

        verifier = base64.urlsafe_b64encode(os.urandom(length)).decode("ascii").rstrip("=")
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return verifier, challenge

    def build_authorize_url(
        self,
        scopes: Iterable[str],
        *,
        state: Optional[str] = None,
        prompt: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: str = "S256",
        response_type: str = "code",
    ) -> str:
        """
        Build /authorize URL for browser redirect.
        - Use code_challenge and code_challenge_method for PKCE
        - Optional state/prompt parameters
        """
        if not self.client.redirect_uri:
            raise ValueError("redirect_uri is required to build authorize URL")

        scope_str = _join_scopes(scopes)
        params = {
            "response_type": response_type,
            "client_id": self.client.client_id,
            "redirect_uri": self.client.redirect_uri,
            "scope": scope_str,
        }
        if state:
            params["state"] = state
        if prompt:
            params["prompt"] = prompt
        if code_challenge:
            params["code_challenge"] = code_challenge
            if code_challenge_method:
                params["code_challenge_method"] = code_challenge_method

        return f"{self.client.http_auth.base_url}/authorize?{urllib.parse.urlencode(params)}"

    def exchange_code(
        self,
        code: str,
        *,
        code_verifier: Optional[str] = None,
    ) -> OAuth2Token:
        """
        Exchange authorization code for access token.
        Cache key: f"{prefix}:3l:{client_id}:{redirect_uri}:{sorted_scopes}"
        """
        if not self.client.redirect_uri:
            raise ValueError("redirect_uri is required for code exchange")

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client.client_id,
            "code": code,
            "redirect_uri": self.client.redirect_uri,
        }

        # Confidential client: include client_secret
        if self.client.client_secret:
            data["client_secret"] = self.client.client_secret

        # PKCE: include code_verifier
        if code_verifier:
            data["code_verifier"] = code_verifier

        resp = self._post_token(data)
        token = OAuth2Token.from_token_response(resp, now=_now_utc())

        # Cache the token
        cache_key = self._cache_key(token.scope or "")
        self._write_cache(cache_key, token)
        return token

    def get_token(self, scopes: Iterable[str]) -> OAuth2Token:
        """
        Get 3-legged token from cache (with auto-refresh if expired).
        Raises ValueError if no valid token found and refresh fails.
        """
        scope_str = _join_scopes(scopes)
        cache_key = self._cache_key(scope_str)

        token = self._read_cache(cache_key)
        if token:
            if not token.is_expired():
                return token
            # Try auto-refresh
            if token.refresh_token:
                try:
                    return self.client.tokens.refresh(token.refresh_token, scopes=scopes)
                except Exception:
                    pass

        raise ValueError(
            "No valid 3-legged token found. Please authorize first using build_authorize_url() and exchange_code()"
        )

    def _cache_key(self, scope_str: str) -> str:
        """Generate cache key for 3-legged token"""
        normalized = _join_scopes(scope_str.split())
        return f"{self.client.cache_prefix}:3l:{self.client.client_id}:{self.client.redirect_uri}:{normalized}"

    def _post_token(self, data: Dict[str, Any]) -> Dict:
        """POST to /token endpoint"""
        session = self.client._get_session()
        url = f"{self.client.http_auth.base_url}/token"
        resp = session.post(url, data=data, timeout=self.client.timeout)
        resp.raise_for_status()
        return resp.json()

    def _read_cache(self, key: str) -> Optional[OAuth2Token]:
        if not self.client.store:
            return None
        return self.client.store.read(key)

    def _write_cache(self, key: str, token: OAuth2Token) -> None:
        if self.client.store:
            self.client.store.write(key, token)


# ----------------------------
# Token Management (Refresh, Revoke, Logout)
# ----------------------------
class _Tokens:
    """Token lifecycle management: refresh, revoke, logout"""

    def __init__(self, client: AuthClient):
        self.client = client

    def refresh(
        self,
        refresh_token: str,
        *,
        scopes: Optional[Iterable[str]] = None,
    ) -> OAuth2Token:
        """
        Refresh an access token using refresh_token.
        - Optional scope parameter to request reduced scope
        - Updates cache
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client.client_id,
            "refresh_token": refresh_token,
        }
        if self.client.client_secret:
            data["client_secret"] = self.client.client_secret
        if scopes:
            data["scope"] = _join_scopes(scopes)

        resp = self._post_token(data)
        token = OAuth2Token.from_token_response(resp, now=_now_utc())

        # Update cache
        cache_key = self._cache_key_3l(token.scope or "")
        self._write_cache(cache_key, token)
        return token

    def revoke(
        self,
        token: str,
        *,
        token_type_hint: Optional[str] = None,
    ) -> None:
        """
        Revoke an access or refresh token.
        - token_type_hint: "access_token" or "refresh_token" (optional)
        """
        data = {
            "token": token,
            "client_id": self.client.client_id,
        }
        if token_type_hint:
            data["token_type_hint"] = token_type_hint
        if self.client.client_secret:
            data["client_secret"] = self.client.client_secret

        session = self.client._get_session()
        url = f"{self.client.http_auth.base_url}/revoke"
        resp = session.post(url, data=data, timeout=self.client.timeout)
        resp.raise_for_status()

    def revoke_all(self, token: OAuth2Token) -> None:
        """
        Convenience method to revoke both access and refresh tokens.
        Continues even if one fails.
        """
        # Revoke access token
        try:
            if token.access_token:
                self.revoke(token.access_token, token_type_hint="access_token")
        except requests.HTTPError:
            pass

        # Revoke refresh token
        try:
            if token.refresh_token:
                self.revoke(token.refresh_token, token_type_hint="refresh_token")
        except requests.HTTPError:
            pass

    def build_logout_url(
        self,
        *,
        post_logout_redirect_uri: Optional[str] = None,
    ) -> str:
        """
        Build /logout URL to terminate browser session.
        Must be opened in user's browser to take effect.
        """
        if post_logout_redirect_uri:
            params = {"post_logout_redirect_uri": post_logout_redirect_uri}
            return f"{self.client.http_auth.base_url}/logout?{urllib.parse.urlencode(params)}"
        return f"{self.client.http_auth.base_url}/logout"

    def full_signout(
        self,
        token: Optional[OAuth2Token] = None,
        *,
        post_logout_redirect_uri: Optional[str] = None,
    ) -> str:
        """
        Complete signout flow: revoke tokens + return logout URL.
        1. Revoke tokens server-side
        2. Return logout URL for browser redirect
        """
        if token is not None:
            self.revoke_all(token)
        return self.build_logout_url(post_logout_redirect_uri=post_logout_redirect_uri)

    def _cache_key_3l(self, scope_str: str) -> str:
        """Generate cache key for 3-legged token"""
        normalized = _join_scopes(scope_str.split())
        return f"{self.client.cache_prefix}:3l:{self.client.client_id}:{self.client.redirect_uri}:{normalized}"

    def _post_token(self, data: Dict[str, Any]) -> Dict:
        """POST to /token endpoint"""
        session = self.client._get_session()
        url = f"{self.client.http_auth.base_url}/token"
        resp = session.post(url, data=data, timeout=self.client.timeout)
        resp.raise_for_status()
        return resp.json()

    def _write_cache(self, key: str, token: OAuth2Token) -> None:
        if self.client.store:
            self.client.store.write(key, token)


# ----------------------------
# User Profile (OIDC UserInfo)
# ----------------------------
class _User:
    """User profile operations (OIDC UserInfo endpoint)"""

    def __init__(self, client: AuthClient):
        self.client = client

    def get_info(self, access_token: str) -> Dict:
        """
        Get current user profile from OIDC UserInfo endpoint.
        Requires 3-legged access_token with 'user-profile:read' scope.
        """
        session = self.client._get_session()
        url = f"{self.client.http_userprofile.base_url}/userinfo"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": self.client.http_userprofile.user_agent,
        }
        resp = session.get(url, headers=headers, timeout=self.client.timeout)
        resp.raise_for_status()
        return resp.json()


# ----------------------------
# Helper Functions
# ----------------------------
def _join_scopes(scopes: Iterable[str]) -> str:
    """Join scopes into sorted, unique, space-separated string"""
    return " ".join(sorted(set(s.strip() for s in scopes if s and s.strip())))


def _now_utc():
    """Get current UTC datetime"""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


# ----------------------------
# Scope Constants
# ----------------------------
class Scopes:
    """
    APS OAuth scopes
    Reference: https://aps.autodesk.com/en/docs/oauth/v2/developers_guide/scopes/
    """

    # OpenID Connect
    OPENID = "openid"
    OFFLINE_ACCESS = "offline_access"

    # User Profile
    USER_PROFILE_READ = "user-profile:read"
    USER_READ = "user:read"
    USER_WRITE = "user:write"

    # Account
    ACCOUNT_READ = "account:read"
    ACCOUNT_WRITE = "account:write"

    # Data Management
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_CREATE = "data:create"
    DATA_SEARCH = "data:search"

    # Bucket (Object Storage Service)
    BUCKET_CREATE = "bucket:create"
    BUCKET_READ = "bucket:read"
    BUCKET_UPDATE = "bucket:update"
    BUCKET_DELETE = "bucket:delete"

    # Viewables (Model Derivative)
    VIEWABLES_READ = "viewables:read"

    # Design Automation
    CODE_ALL = "code:all"

    # Autodesk Construction Cloud (ACC)
    ISSUES_READ = "issues:read"