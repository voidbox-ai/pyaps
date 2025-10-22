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
from pyaps import auth

# Coming soon - SDK implementation in progress
```

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/voidbox-ai/pyaps.git
   cd pyaps
   ```

2. Install in development mode with test dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage report:
```bash
pytest --cov=pyaps --cov-report=term-missing
```

### Continuous Integration

All pull requests are automatically tested via GitHub Actions on:
- Python versions: 3.9, 3.10, 3.11, 3.12
- Operating systems: Ubuntu, Windows, macOS

Tests must pass before merging.

## Project Status

This package is currently in early development (v0.0.1). The package name has been reserved on PyPI, and active development is underway.

## Contributing

py-aps is developed and maintained by **voidbox**. We welcome bug reports and feature requests through [GitHub Issues](https://github.com/voidbox-ai/pyaps/issues).

While this is an open source project, please note that we have limited capacity to review external pull requests. If you'd like to contribute code, please open an issue first to discuss your proposal with the maintainers.

For more details, see our [Contributing Guidelines](CONTRIBUTING.md).

### For Developers
- [Contributing Guidelines](CONTRIBUTING.md) - Participation guidelines and development standards
- [Commit Convention](.github/COMMIT_CONVENTION.md) - Commit message format reference

## License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/voidbox-ai/pyaps)
- [PyPI Package](https://pypi.org/project/py-aps/)
- [Autodesk Platform Services Documentation](https://aps.autodesk.com/)
