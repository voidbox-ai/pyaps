# Contributing to py-aps

Thank you for your interest in py-aps! This document provides information about how the project is developed and how you can participate.

## Project Governance

**py-aps is maintained and developed by voidbox.** While this is an open source project (Apache-2.0 license), development is primarily led by the voidbox team to maintain consistent architecture and quality standards.

## How to Participate

### Reporting Issues

We welcome bug reports and feature requests! If you encounter any issues or have suggestions:

1. Check if the issue already exists in [GitHub Issues](https://github.com/voidbox-ai/pyaps/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Python version, OS, and relevant environment details
   - Code examples if applicable

### Pull Requests

**Please note:** We have limited capacity to review and merge external pull requests. If you'd like to contribute code:

1. **Open an issue first** to discuss the proposed changes with the maintainers
2. Wait for approval before starting significant work
3. Small bug fixes and documentation improvements are more likely to be accepted than large feature additions

### What We Accept

✅ **More likely to accept:**
- Bug fixes with test cases
- Documentation improvements
- Typo corrections
- Small refactoring improvements

⚠️ **Less likely to accept:**
- New features without prior discussion
- Large architectural changes
- Breaking changes
- Dependencies additions

## Development Guidelines

If you receive approval to work on a contribution, please follow these guidelines:

### Commit Convention

We follow a structured commit message format. All commits should follow this pattern:

```
<TYPE>: <subject>

[optional body]
```

#### Commit Types

- **FEAT**: A new feature
- **FIX**: A bug fix
- **DOCS**: Documentation changes
- **BUILD**: Changes to build system or dependencies
- **CHORE**: Routine tasks, maintenance, or tooling changes
- **REFACTOR**: Code changes that neither fix bugs nor add features
- **TEST**: Adding or updating tests

#### Examples

```
FEAT: Add OAuth2 authentication flow
```

```
FIX: Resolve token refresh issue in auth module

The previous implementation did not properly handle token refresh
when the access token expired during long-running operations.

Fixes #42
```

### Code Style

- Follow [PEP 8](https://pep8.org/) style guide for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

### Testing

All code contributions must include tests.

#### Setting Up Testing Environment

```bash
pip install -e ".[dev]"
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyaps --cov-report=term-missing
```

#### Writing Tests

- Place test files in the `tests/` directory
- Name test files with `test_` prefix
- Aim for high test coverage (>80%)
- All tests must pass before PR review

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following the guidelines above
4. Ensure all tests pass
5. Update documentation if needed
6. Submit PR with clear description

**Note:** PRs may take time to review. Large PRs may be closed if not previously discussed with maintainers.

## Questions and Discussions

For questions about using py-aps or general discussions:
- Open a [GitHub Discussion](https://github.com/voidbox-ai/pyaps/discussions)
- Check existing issues and documentation

For security issues, please see our security policy.

## License

By contributing to py-aps, you agree that your contributions will be licensed under the Apache-2.0 License.

## Development Roadmap

Development priorities are set by the voidbox team. You can follow our progress through:
- GitHub issues labeled with milestones
- Release notes
- Project discussions

---

Thank you for understanding our development model. We appreciate your interest in py-aps!
