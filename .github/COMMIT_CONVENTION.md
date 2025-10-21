# Commit Convention Quick Reference

## Format
```
<TYPE>: <subject>
```

## Types

| Type | Description | Example |
|------|-------------|---------|
| **FEAT** | New feature | `FEAT: Add OAuth2 authentication` |
| **FIX** | Bug fix | `FIX: Resolve token refresh issue` |
| **DOCS** | Documentation only | `DOCS: Update README examples` |
| **BUILD** | Build system or dependencies | `BUILD: Update setuptools to v68` |
| **CHORE** | Maintenance tasks | `CHORE: Update .gitignore` |
| **REFACTOR** | Code refactoring | `REFACTOR: Simplify auth client` |
| **TEST** | Tests only | `TEST: Add auth module tests` |

## Rules

✅ **DO:**
- Use imperative mood: "Add" not "Added"
- Capitalize after prefix: `FEAT: Add feature`
- Keep subject under 50 characters
- Reference issues in body: `Fixes #123`

❌ **DON'T:**
- End subject with period
- Use past tense: "Added feature"
- Mix multiple types in one commit

## Examples

**Good:**
```
FEAT: Add support for BIM 360 data management
```

**Good with body:**
```
FIX: Resolve authentication token expiration

The previous implementation did not handle token refresh properly.
This adds automatic refresh logic for long-running operations.

Fixes #42
```

**Bad:**
```
added new feature.
Fixed bug
Update readme
```

For full guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md)
