# Migration Plan: discord.py PyPI → Local Custom Version

## Overview

This document outlines the migration plan from using `discord-py>=2.6.0` from PyPI to the custom version located in `external/discord.py/` (version `2.7.0a`).

## Current State

### Current Configuration

- **Source**: PyPI package `discord-py>=2.6.0`
- **Location in pyproject.toml**: Line 18
- **Package Manager**: `uv`
- **Lock File**: `uv.lock`

### Target State

- **Source**: Local path `external/discord.py/`
- **Version**: `2.7.0a` (alpha)
- **Package Name**: `discord.py` (same as PyPI package name)
- **Build System**: setuptools (via pyproject.toml)

## Pre-Migration Checklist

- [ ] Verify `external/discord.py/` is up to date
- [ ] Check if `external/discord.py/` is a git submodule (currently it's not in `.gitmodules`)
- [ ] Review any custom modifications in the local version
- [ ] Ensure all team members have the external directory available
- [ ] Backup current `uv.lock` file
- [ ] Create a feature branch for the migration

## Migration Steps

### Step 1: Update pyproject.toml

Replace the PyPI dependency with a local path dependency:

**Before:**
```toml
dependencies = [
    # ... other dependencies ...
    "discord-py>=2.6.0",
    # ... other dependencies ...
]
```

**After:**
```toml
dependencies = [
    # ... other dependencies ...
    "discord.py @ ./external/discord.py",
    # ... other dependencies ...
]
```

**Note**: `uv` supports PEP 508 path dependencies. The relative path `./external/discord.py` is relative to the `pyproject.toml` file location.

**Alternative (using absolute path):**
```toml
dependencies = [
    # ... other dependencies ...
    "discord.py @ file:///absolute/path/to/external/discord.py",
    # ... other dependencies ...
]
```

**Editable mode (for development):**
If you want changes to the local package to be immediately available without reinstalling:
```toml
dependencies = [
    # ... other dependencies ...
    "discord.py @ ./external/discord.py",
    # ... other dependencies ...
]
```

Then install with:
```bash
uv sync --extra editable
```

Or use the `--editable` flag when adding:
```bash
uv add --editable ./external/discord.py
```

### Step 2: Update Lock File

Run the following command to update the lock file:

```bash
uv lock --upgrade-package discord.py
```

Or simply:
```bash
uv sync
```

This will:
- Resolve the local path dependency
- Update `uv.lock` with the local package information
- Install the local version in editable mode (if using editable)

### Step 3: Verify Installation

Check that the local version is installed:

```bash
uv pip list | grep discord
```

Or check the installed version:
```python
import discord
print(discord.__version__)  # Should show '2.7.0a'
```

### Step 4: Test Imports

Verify all imports still work:

```bash
python -c "import discord; from discord.ext import commands; print('Imports OK')"
```

### Step 5: Run Test Suite

Execute the full test suite to ensure compatibility:

```bash
uv run test all
```

Pay special attention to:
- Discord API interactions
- Bot initialization
- Command execution
- Event handlers
- UI components (Components V2)

### Step 6: Run Quality Checks

Ensure code quality checks pass:

```bash
uv run dev all
```

This includes:
- Linting (`ruff`)
- Type checking (`basedpyright`)
- Docstring validation (`pydoclint`)

## Potential Issues & Solutions

### Issue 1: Package Name Mismatch

**Problem**: PyPI package is `discord-py` but local package is `discord.py`

**Solution**: The import name is the same (`discord`), so this shouldn't affect imports. However, ensure the package name in `external/discord.py/pyproject.toml` matches what we're referencing.

### Issue 2: Missing Dependencies

**Problem**: Local version might have different or additional dependencies

**Solution**: Check `external/discord.py/requirements.txt` and ensure all dependencies are available. The local version should list its dependencies in its `pyproject.toml`.

### Issue 3: Version Compatibility

**Problem**: `2.7.0a` is an alpha version and might have breaking changes

**Solution**: 
- Review changelog or commit history in `external/discord.py/`
- Test thoroughly before deploying
- Consider pinning to a specific commit if using git submodule

### Issue 4: CI/CD Pipeline

**Problem**: CI/CD might not have access to the external directory

**Solution**:
- If using git submodule, ensure CI clones submodules
- If not using submodule, ensure the external directory is included in the repository
- Update CI configuration to handle local path dependencies

### Issue 5: Development Environment

**Problem**: Other developers might not have the external directory

**Solution**:
- Document the requirement in `README.md`
- Add setup instructions for cloning/updating external dependencies
- Consider using git submodules for better management

## Rollback Plan

If issues arise, rollback using these steps:

1. **Revert pyproject.toml**:
   ```toml
   dependencies = [
       # ... other dependencies ...
       "discord-py>=2.6.0",
       # ... other dependencies ...
   ]
   ```

2. **Restore lock file**:
   ```bash
   git checkout uv.lock
   ```

3. **Reinstall dependencies**:
   ```bash
   uv sync
   ```

4. **Verify rollback**:
   ```bash
   python -c "import discord; print(discord.__version__)"  # Should show 2.6.x
   ```

## Post-Migration Tasks

- [ ] Update documentation to reflect local dependency
- [ ] Update `.cursor/rules/core/tech-stack.mdc` if needed
- [ ] Add note in `README.md` about external dependencies
- [ ] Update CI/CD configuration if needed
- [ ] Document any custom modifications in the local version
- [ ] Create or update `.gitmodules` if converting to submodule

## Long-term Considerations

### Option 1: Git Submodule

Convert `external/discord.py/` to a git submodule for better version control:

```bash
git submodule add <repository-url> external/discord.py
```

**Pros**:
- Better version tracking
- Easier updates
- Clear separation of concerns

**Cons**:
- Requires submodule initialization
- Additional git commands for updates

### Option 2: Fork and Maintain

If significant customizations are needed:
- Fork the discord.py repository
- Maintain custom changes in the fork
- Reference the fork via git URL in pyproject.toml

### Option 3: Contribute Upstream

If custom changes are beneficial:
- Contribute changes back to upstream discord.py
- Use upstream version once merged
- Keep local version only for development/testing

## Testing Checklist

Before considering migration complete:

- [ ] All imports work correctly
- [ ] Bot starts without errors
- [ ] Commands execute successfully
- [ ] Events fire correctly
- [ ] UI components (buttons, modals, views) work
- [ ] Slash commands work
- [ ] Voice features work (if used)
- [ ] All tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Documentation builds successfully

## Version Comparison

| Aspect | PyPI (2.6.0) | Local (2.7.0a) |
|--------|--------------|---------------|
| Version | 2.6.0 (stable) | 2.7.0a (alpha) |
| Source | PyPI registry | Local path |
| Updates | `uv sync --upgrade` | Manual update |
| Stability | Production-ready | Development/alpha |
| Breaking Changes | Unlikely | Possible |

## Related Files

- `pyproject.toml` - Main dependency configuration
- `uv.lock` - Locked dependency versions
- `external/discord.py/` - Local discord.py source
- `external/discord.py/pyproject.toml` - Local package config
- `.gitmodules` - Git submodule configuration (if used)
- `.cursor/rules/core/tech-stack.mdc` - Tech stack documentation

## References

- [UV Documentation - Path Dependencies](https://docs.astral.sh/uv/guides/dependency-management/#path-dependencies)
- [PEP 508 - Dependency Specification](https://peps.python.org/pep-0508/)
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- Project's existing pattern: `docs/content/developer/investigations/spotify-music-system.md` (local package integration)

## Notes

- The local version (`2.7.0a`) is an alpha release and may contain breaking changes or bugs
- Ensure all team members are aware of the migration
- Consider creating a migration branch and testing thoroughly before merging
- Keep the PyPI version as a fallback option during initial migration period

