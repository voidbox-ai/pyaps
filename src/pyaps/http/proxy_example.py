"""
Proxy Configuration Examples for pyaps

This module demonstrates how to configure HTTP/HTTPS proxies for all pyaps clients.
Proxy support is available in v0.0.6+.
"""

import os
from pyaps.auth import AuthClient, Scopes
from pyaps.datamanagement import DataManagementClient
from pyaps.automation import AutomationClient, AutomationWorkflow


# ============================================
# Example 1: Explicit Proxy Configuration
# ============================================
def example_explicit_proxy():
    """Configure clients with explicit proxy settings"""

    # Define proxy settings
    proxies = {
        'http': 'http://proxy.company.com:8080',
        'https': 'https://proxy.company.com:8080',
    }

    # AuthClient with proxy
    auth_client = AuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        proxies=proxies,
        trust_env=False,  # Don't read from environment variables
    )

    token = auth_client.two_legged.get_token([Scopes.DATA_READ, Scopes.CODE_ALL])

    # DataManagementClient with proxy
    dm_client = DataManagementClient(
        token_provider=lambda: token.access_token,
        proxies=proxies,
        trust_env=False,
    )

    # AutomationClient with proxy
    auto_client = AutomationClient(
        token_provider=lambda: token.access_token,
        proxies=proxies,
        trust_env=False,
    )

    # AutomationWorkflow inherits proxy settings from clients
    workflow = AutomationWorkflow(
        automation_client=auto_client,
        data_client=dm_client,
        default_bucket="my-bucket",
    )

    print("All clients configured with explicit proxy settings")


# ============================================
# Example 2: Environment Variable Proxy
# ============================================
def example_environment_proxy():
    """Configure clients to use environment variable proxies (HTTP_PROXY, HTTPS_PROXY)"""

    # Set environment variables (in production, set these in your shell or .env file)
    # os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
    # os.environ['HTTPS_PROXY'] = 'https://proxy.company.com:8080'
    # os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

    # Clients will automatically use environment variables when trust_env=True (default)
    auth_client = AuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        trust_env=True,  # This is the default
    )

    token = auth_client.two_legged.get_token([Scopes.DATA_READ])

    dm_client = DataManagementClient(
        token_provider=lambda: token.access_token,
        trust_env=True,
    )

    print("Clients configured to use environment variable proxies")


# ============================================
# Example 3: Proxy with Authentication
# ============================================
def example_authenticated_proxy():
    """Configure proxy that requires username/password authentication"""

    proxy_user = "proxy_username"
    proxy_pass = "proxy_password"
    proxy_host = "proxy.company.com:8080"

    proxies = {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}',
        'https': f'https://{proxy_user}:{proxy_pass}@{proxy_host}',
    }

    auth_client = AuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        proxies=proxies,
        trust_env=False,
    )

    token = auth_client.two_legged.get_token([Scopes.CODE_ALL])

    auto_client = AutomationClient(
        token_provider=lambda: token.access_token,
        proxies=proxies,
        trust_env=False,
    )

    print("Clients configured with authenticated proxy")


# ============================================
# Example 4: Mixed Configuration (Environment + Explicit)
# ============================================
def example_mixed_proxy():
    """
    Use environment variables for most traffic, but override for specific clients.
    Explicit proxy settings take precedence over environment variables.
    """

    # Most clients use environment variables
    auth_client = AuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        trust_env=True,
    )

    token = auth_client.two_legged.get_token([Scopes.DATA_READ, Scopes.CODE_ALL])

    # Override for automation client (e.g., use different proxy for Design Automation)
    special_proxies = {
        'http': 'http://automation-proxy.company.com:8080',
        'https': 'https://automation-proxy.company.com:8080',
    }

    auto_client = AutomationClient(
        token_provider=lambda: token.access_token,
        proxies=special_proxies,  # Explicit setting overrides environment
        trust_env=False,
    )

    print("Mixed proxy configuration applied")


# ============================================
# Example 5: No Proxy Configuration
# ============================================
def example_no_proxy():
    """Disable proxy completely, even if environment variables are set"""

    # To disable proxy completely, set trust_env=False and don't provide proxies
    auth_client = AuthClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        proxies=None,
        trust_env=False,  # Ignore environment variables
    )

    token = auth_client.two_legged.get_token([Scopes.DATA_READ])

    dm_client = DataManagementClient(
        token_provider=lambda: token.access_token,
        proxies=None,
        trust_env=False,
    )

    print("Clients configured without any proxy")


# ============================================
# Example 6: Complete Workflow with Proxy
# ============================================
def example_complete_workflow_with_proxy():
    """Complete example: Authentication -> Data Management -> Automation with proxy"""

    # Configure proxy
    proxies = {
        'http': 'http://proxy.company.com:8080',
        'https': 'https://proxy.company.com:8080',
    }

    # Step 1: Authenticate
    auth_client = AuthClient(
        client_id=os.getenv("APS_CLIENT_ID"),
        client_secret=os.getenv("APS_CLIENT_SECRET"),
        proxies=proxies,
        trust_env=False,
    )

    token = auth_client.two_legged.get_token([
        Scopes.DATA_READ,
        Scopes.DATA_WRITE,
        Scopes.BUCKET_CREATE,
        Scopes.BUCKET_READ,
        Scopes.CODE_ALL,
    ])

    # Step 2: Setup clients
    dm_client = DataManagementClient(
        token_provider=lambda: token.access_token,
        proxies=proxies,
        trust_env=False,
    )

    auto_client = AutomationClient(
        token_provider=lambda: token.access_token,
        proxies=proxies,
        trust_env=False,
    )

    # Step 3: Run workflow
    workflow = AutomationWorkflow(
        automation_client=auto_client,
        data_client=dm_client,
        default_bucket="my-design-automation-bucket",
    )

    # Execute workitem (all HTTP requests will use proxy)
    result = workflow.run_workitem_with_files(
        activity_id="YourAlias.YourActivity+prod",
        input_files={"inputFile": "path/to/input.rvt"},
        output_files={"outputFile": "output.rvt"},
        download_outputs=True,
        output_dir="./results",
    )

    print(f"WorkItem completed: {result.status}")
    print(f"Downloaded files: {result.downloaded_files}")


# ============================================
# Proxy Configuration Best Practices
# ============================================
"""
BEST PRACTICES:

1. Security:
   - Never hardcode proxy credentials in source code
   - Use environment variables or secure configuration management
   - Be cautious with proxy logs that might contain sensitive data

2. Environment Variables:
   - Set HTTP_PROXY and HTTPS_PROXY in your shell or .env file
   - Use NO_PROXY to exclude certain hosts (e.g., localhost, internal APIs)
   - Example:
     export HTTP_PROXY=http://proxy.company.com:8080
     export HTTPS_PROXY=https://proxy.company.com:8080
     export NO_PROXY=localhost,127.0.0.1,.internal.com

3. Corporate Environments:
   - Contact your IT department for correct proxy settings
   - Some proxies may require SSL certificate configuration
   - Test proxy settings with simple requests before running workflows

4. Troubleshooting:
   - If requests hang, check proxy connectivity
   - Verify proxy authentication credentials
   - Check firewall rules and network policies
   - Use requests library's built-in debugging:
     import logging
     logging.basicConfig(level=logging.DEBUG)

5. Performance:
   - Proxy adds latency to requests
   - Consider connection pooling (handled automatically by requests.Session)
   - Monitor timeout settings if proxy is slow
"""


if __name__ == "__main__":
    print("Proxy Configuration Examples for pyaps")
    print("=" * 60)
    print()

    # Uncomment the example you want to run:
    # example_explicit_proxy()
    # example_environment_proxy()
    # example_authenticated_proxy()
    # example_mixed_proxy()
    # example_no_proxy()
    # example_complete_workflow_with_proxy()

    print("\nFor more information, see the README.md file")
