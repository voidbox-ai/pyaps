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

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.

### Quick Links for Contributors
- [Contributing Guidelines](CONTRIBUTING.md) - Full contribution guide
- [Commit Convention](.github/COMMIT_CONVENTION.md) - Quick reference for commit messages

## License

This project is licensed under the Apache-2.0 License - see the [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/voidbox-ai/pyaps)
- [PyPI Package](https://pypi.org/project/py-aps/)
- [Autodesk Platform Services Documentation](https://aps.autodesk.com/)
