# Contributing to py-aps

Thank you for your interest in contributing to py-aps! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/pyaps.git`
3. Create a new branch: `git checkout -b your-feature-branch`
4. Make your changes
5. Commit your changes following our commit convention (see below)
6. Push to your fork: `git push origin your-feature-branch`
7. Open a Pull Request

## Commit Convention

We follow a structured commit message format to maintain a clear and readable project history. All commit messages should follow this pattern:

```
<TYPE>: <subject>

[optional body]

[optional footer]
```

### Commit Types

- **FEAT**: A new feature
  ```
  FEAT: Add OAuth2 authentication flow
  ```

- **FIX**: A bug fix
  ```
  FIX: Resolve token refresh issue in auth module
  ```

- **DOCS**: Documentation changes
  ```
  DOCS: Update authentication examples in README
  ```

- **BUILD**: Changes to build system or dependencies
  ```
  BUILD: Update setuptools version requirement
  ```

- **CHORE**: Routine tasks, maintenance, or tooling changes
  ```
  CHORE: Update .gitignore for Python artifacts
  ```

- **REFACTOR**: Code changes that neither fix bugs nor add features
  ```
  REFACTOR: Simplify data management API client initialization
  ```

- **TEST**: Adding or updating tests
  ```
  TEST: Add unit tests for authentication module
  ```

### Commit Message Guidelines

1. **Subject Line**
   - Use the imperative mood ("Add feature" not "Added feature")
   - Keep it concise (50 characters or less)
   - Capitalize the first letter after the type prefix
   - Do not end with a period

2. **Body** (optional)
   - Provide additional context about the changes
   - Explain the "why" behind the change, not just the "what"
   - Wrap lines at 72 characters

3. **Footer** (optional)
   - Reference related issues: `Fixes #123` or `Closes #456`
   - Note breaking changes: `BREAKING CHANGE: Description of the breaking change`

### Examples

**Simple commit:**
```
FEAT: Add support for BIM 360 data management
```

**Commit with body:**
```
FIX: Resolve authentication token expiration handling

The previous implementation did not properly handle token refresh
when the access token expired during long-running operations.
This commit adds automatic token refresh logic.

Fixes #42
```

**Breaking change:**
```
REFACTOR: Change authentication initialization parameters

BREAKING CHANGE: The `auth.Client()` constructor now requires
`client_id` and `client_secret` as separate parameters instead
of a single `credentials` dict.

Migration guide:
- Before: `Client(credentials={'id': '...', 'secret': '...'})`
- After: `Client(client_id='...', client_secret='...')`
```

## Code Style

- Follow [PEP 8](https://pep8.org/) style guide for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

## Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a PR
- Run tests with: `pytest`

## Pull Request Process

1. **Update Documentation**: Update the README.md or relevant documentation for any user-facing changes
2. **Add Tests**: Include tests that cover your changes
3. **Follow Commit Convention**: Ensure your commits follow the convention outlined above
4. **Keep PRs Focused**: One PR should address one feature or fix
5. **Write Clear PR Description**:
   - Summarize what the PR does
   - Reference related issues
   - Highlight any breaking changes
   - Include testing instructions if applicable

## Questions?

If you have questions or need help, please:
- Open an issue on GitHub
- Check existing issues and discussions

## License

By contributing to py-aps, you agree that your contributions will be licensed under the Apache-2.0 License.
