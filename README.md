# py-aps

Python SDK for Autodesk Platform Service APIs

## Installation

```bash
pip install py-aps
```

## Overview

py-aps is a Python SDK that provides a simple and intuitive interface for interacting with Autodesk Platform Services (formerly known as Forge) APIs. This SDK simplifies authentication, data management, and automation workflows for APS-powered applications.

## Features

- **Authentication**: Easy OAuth2 authentication flow
- **Data Management**: Access and manage files in BIM 360, ACC, and other Autodesk cloud storage
- **Automation**: Automate design and engineering workflows

## Quick Start

```python
from pyaps.auth import AuthClient, Scopes

# 2-legged OAuth
client = AuthClient(client_id="...", client_secret="...")
token = client.two_legged.get_token([Scopes.DATA_READ])

# 3-legged OAuth with PKCE
verifier, challenge = client.three_legged.generate_pkce_pair()
auth_url = client.three_legged.build_authorize_url(
    scopes=[Scopes.DATA_READ, Scopes.USER_PROFILE_READ],
    code_challenge=challenge
)
# After user authorizes: token = client.three_legged.exchange_code(code, code_verifier=verifier)
```

For more examples, see `src/pyaps/auth/example.py`.

## Project Status

**Current version: v0.0.2** - Authentication API support added

This package is currently in early development. Active development is underway by **voidbox**.

### Version History
- **v0.0.2** - Added OAuth 2.0 authentication client with 2-legged/3-legged flows, PKCE support, and token management
- **v0.0.1** - Initial package release (placeholder)

## Contributing

We welcome bug reports and feature requests through [GitHub Issues](https://github.com/voidbox-ai/pyaps/issues).

This project is primarily developed by voidbox. External pull requests have limited review capacity.

## License

Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/voidbox-ai/pyaps)
- [PyPI Package](https://pypi.org/project/py-aps/)
- [Autodesk Platform Services Documentation](https://aps.autodesk.com/)
