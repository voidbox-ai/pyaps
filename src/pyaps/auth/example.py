"""
APS Authentication API 사용 예제
각 OAuth 플로우와 토큰 관리 기능을 smoke test 형태로 시연
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from pyaps.auth.client import AuthClient, Scopes
from pyaps.auth.token_store import InMemoryTokenStore

# Load .env file if exists
def load_dotenv():
    """Simple .env loader"""
    env_file = Path(__file__).parent.parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_dotenv()


def example_2legged():
    """2-legged OAuth (Client Credentials) 예제"""
    print("\n" + "="*60)
    print("1. Two-Legged OAuth (Client Credentials)")
    print("="*60)

    client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
        store=InMemoryTokenStore(),
    )

    # 1-1. 토큰 발급
    print("\n[1-1] Get 2-legged token")
    scopes = [Scopes.DATA_READ, Scopes.BUCKET_READ]
    token = client.two_legged.get_token(scopes)
    print(f"  ✓ Access Token: {token.access_token[:20]}...")
    print(f"  ✓ Token Type: {token.token_type}")
    print(f"  ✓ Expires At: {token.expires_at}")
    print(f"  ✓ Scope: {token.scope}")

    # 1-2. 캐시된 토큰 재사용
    print("\n[1-2] Reuse cached token")
    cached_token = client.two_legged.get_token(scopes)
    print(f"  ✓ Same token: {token.access_token == cached_token.access_token}")

    # 1-3. 다른 스코프로 새 토큰
    print("\n[1-3] Get token with different scopes")
    different_scopes = [Scopes.VIEWABLES_READ]
    token2 = client.two_legged.get_token(different_scopes)
    print(f"  ✓ Different token: {token.access_token != token2.access_token}")
    print(f"  ✓ Scope: {token2.scope}")


def example_3legged():
    """3-legged OAuth (Authorization Code with PKCE) 예제"""
    print("\n" + "="*60)
    print("2. Three-Legged OAuth (Authorization Code + PKCE)")
    print("="*60)

    client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
        redirect_uri="http://localhost:8080/callback",
        store=InMemoryTokenStore(),
    )

    # 2-1. PKCE pair 생성
    print("\n[2-1] Generate PKCE pair")
    verifier, challenge = client.three_legged.generate_pkce_pair()
    print(f"  ✓ Code Verifier (length: {len(verifier)}): {verifier[:20]}...")
    print(f"  ✓ Code Challenge (S256): {challenge[:20]}...")

    # 2-2. Authorization URL 생성
    print("\n[2-2] Build authorize URL")
    scopes = [Scopes.DATA_READ, Scopes.USER_PROFILE_READ, Scopes.OPENID]
    state = secrets.token_urlsafe(16)
    auth_url = client.three_legged.build_authorize_url(
        scopes=scopes,
        state=state,
        code_challenge=challenge,
        code_challenge_method="S256",
    )
    print(f"  ✓ Authorize URL (full):")
    print(f"     {auth_url}")
    print(f"  ✓ State: {state}")
    print("\n  📌 User should visit this URL in browser to authorize")

    # 2-3. Code exchange (실제 코드 없이 구조만 표시)
    print("\n[2-3] Exchange authorization code (structure only)")
    print("  After user authorizes, you'll receive 'code' in redirect_uri")
    print("  Then call:")
    print(f"    token = client.three_legged.exchange_code(")
    print(f"        code='<received_code>',")
    print(f"        code_verifier='{verifier[:20]}...'")
    print(f"    )")

    # 2-4. 캐시된 토큰 조회 (실제로는 없음)
    print("\n[2-4] Get cached 3-legged token")
    try:
        cached = client.three_legged.get_token(scopes)
        print(f"  ✓ Found cached token: {cached.access_token[:20]}...")
    except ValueError as e:
        print(f"  ℹ No cached token (expected): {e}")


def example_token_management():
    """토큰 관리 (Refresh, Revoke, Logout) 예제"""
    print("\n" + "="*60)
    print("3. Token Management (Refresh, Revoke, Logout)")
    print("="*60)

    client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
        redirect_uri="http://localhost:8080/callback",
        store=InMemoryTokenStore(),
    )

    # 3-1. Refresh token (구조만 표시)
    print("\n[3-1] Refresh access token (structure only)")
    print("  If you have a refresh_token from 3-legged flow:")
    print("    refreshed = client.tokens.refresh(")
    print("        refresh_token='<your_refresh_token>',")
    print("        scopes=[Scopes.DATA_READ]  # optional: reduce scope")
    print("    )")

    # 3-2. Revoke token (구조만 표시)
    print("\n[3-2] Revoke access token (structure only)")
    print("    client.tokens.revoke(")
    print("        token='<access_token>',")
    print("        token_type_hint='access_token'")
    print("    )")

    # 3-3. Revoke all tokens (구조만 표시)
    print("\n[3-3] Revoke all tokens from OAuth2Token (structure only)")
    print("    client.tokens.revoke_all(token_object)")
    print("  This revokes both access_token and refresh_token")

    # 3-4. Logout URL 생성
    print("\n[3-4] Build logout URL")
    logout_url = client.tokens.build_logout_url(
        post_logout_redirect_uri="http://localhost:8080/goodbye"
    )
    print(f"  ✓ Logout URL (full):")
    print(f"     {logout_url}")
    print("  📌 User should visit this URL in browser to end session")

    # 3-5. Full signout (구조만 표시)
    print("\n[3-5] Full signout flow (structure only)")
    print("    logout_url = client.tokens.full_signout(")
    print("        token=token_object,  # revokes tokens")
    print("        post_logout_redirect_uri='http://localhost:8080/goodbye'")
    print("    )")
    print("  Then redirect user to logout_url")


def example_user_profile():
    """User Profile (OIDC UserInfo) 예제"""
    print("\n" + "="*60)
    print("4. User Profile (OIDC UserInfo)")
    print("="*60)

    client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
    )

    # 4-1. Get user info (구조만 표시)
    print("\n[4-1] Get user profile (structure only)")
    print("  Requires 3-legged token with 'user-profile:read' scope:")
    print("    user_info = client.user.get_info(access_token='<3-legged_token>')")
    print("    print(user_info)")
    print("\n  Example response:")
    print("    {")
    print('      "sub": "1234567890",')
    print('      "name": "John Doe",')
    print('      "email": "john@example.com",')
    print('      "email_verified": true,')
    print('      "locale": "en-US"')
    print("    }")


def example_scopes():
    """사용 가능한 Scope 상수 목록"""
    print("\n" + "="*60)
    print("5. Available Scopes")
    print("="*60)

    scopes_by_category = {
        "OpenID Connect": [
            ("OPENID", Scopes.OPENID),
            ("OFFLINE_ACCESS", Scopes.OFFLINE_ACCESS),
        ],
        "User Profile": [
            ("USER_PROFILE_READ", Scopes.USER_PROFILE_READ),
            ("USER_READ", Scopes.USER_READ),
            ("USER_WRITE", Scopes.USER_WRITE),
        ],
        "Account": [
            ("ACCOUNT_READ", Scopes.ACCOUNT_READ),
            ("ACCOUNT_WRITE", Scopes.ACCOUNT_WRITE),
        ],
        "Data Management": [
            ("DATA_READ", Scopes.DATA_READ),
            ("DATA_WRITE", Scopes.DATA_WRITE),
            ("DATA_CREATE", Scopes.DATA_CREATE),
            ("DATA_SEARCH", Scopes.DATA_SEARCH),
        ],
        "Bucket": [
            ("BUCKET_CREATE", Scopes.BUCKET_CREATE),
            ("BUCKET_READ", Scopes.BUCKET_READ),
            ("BUCKET_UPDATE", Scopes.BUCKET_UPDATE),
            ("BUCKET_DELETE", Scopes.BUCKET_DELETE),
        ],
        "Viewables": [
            ("VIEWABLES_READ", Scopes.VIEWABLES_READ),
        ],
        "Design Automation": [
            ("CODE_ALL", Scopes.CODE_ALL),
        ],
        "ACC": [
            ("ISSUES_READ", Scopes.ISSUES_READ),
        ],
    }

    for category, scope_list in scopes_by_category.items():
        print(f"\n[{category}]")
        for name, value in scope_list:
            print(f"  Scopes.{name:20} = '{value}'")


def example_advanced_scenarios():
    """고급 시나리오"""
    print("\n" + "="*60)
    print("6. Advanced Scenarios")
    print("="*60)

    # 6-1. Custom token provider for HTTP client
    print("\n[6-1] Using tokens with HTTP client")
    print("  from pyaps.http.client import HTTPClient")
    print()
    print("  # 2-legged token provider")
    print("  def token_provider():")
    print("      token = auth_client.two_legged.get_token([Scopes.DATA_READ])")
    print("      return token.access_token")
    print()
    print("  http = HTTPClient(")
    print("      token_provider=token_provider,")
    print("      base_url='https://developer.api.autodesk.com/data/v1'")
    print("  )")
    print("  projects = http.get('/projects/:project_id/...')")

    # 6-2. Auto-refresh for 3-legged
    print("\n[6-2] Auto-refresh for 3-legged tokens")
    print("  When you call get_token(), it automatically:")
    print("  1. Checks if cached token exists")
    print("  2. If expired, tries to refresh using refresh_token")
    print("  3. Returns valid token or raises ValueError")
    print()
    print("  scopes = [Scopes.DATA_READ, Scopes.USER_PROFILE_READ]")
    print("  token = client.three_legged.get_token(scopes)  # auto-refresh!")

    # 6-3. Multiple scope combinations
    print("\n[6-3] Cache keys for different scope combinations")
    print("  Each scope combination gets its own cache entry:")
    print("    cache_key_1 = 'aps:2l:client_id:bucket:read data:read'")
    print("    cache_key_2 = 'aps:2l:client_id:data:read'")
    print("  Scopes are sorted and deduplicated automatically")

    # 6-4. Token expiration handling
    print("\n[6-4] Token expiration with skew")
    print("  token.is_expired(skew_seconds=30)")
    print("  Returns True if token expires within 30 seconds")
    print("  This prevents race conditions during API calls")


def main():
    """모든 예제 실행"""
    print("\n" + "="*60)
    print("APS Authentication API - Smoke Test Examples")
    print("="*60)
    print("\nℹ Set environment variables before running:")
    print("  export APS_CLIENT_ID='your_client_id'")
    print("  export APS_CLIENT_SECRET='your_client_secret'")

    # 환경 변수 체크
    has_credentials = bool(os.getenv("APS_CLIENT_ID") and os.getenv("APS_CLIENT_SECRET"))

    if has_credentials:
        print("\n✓ Credentials found - running live examples")
        example_2legged()
    else:
        print("\n⚠ Credentials not found - showing structure only")

    # 나머지는 항상 표시 (실제 API 호출 없음)
    example_3legged()
    example_token_management()
    example_user_profile()
    example_scopes()
    example_advanced_scenarios()

    print("\n" + "="*60)
    print("✓ All examples completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
