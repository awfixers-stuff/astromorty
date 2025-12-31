# Gemini Rules & Commands

The Astromorty project uses Gemini's rules and commands system to provide AI-assisted development with project-specific patterns and workflows.

## Overview

This directory contains:

- **Rules** (`.mdc` files) - Project-specific coding patterns and standards
- **Commands** (`.md` files) - Reusable workflows and task automation

Rules are automatically applied by Gemini based on file patterns, while commands are invoked manually with the `/` prefix in Gemini chat.

## Structure

### Rules

Rules are organized by domain in `.gemini/rules/`:

- **`core/`** - Core project rules (tech stack, dependencies)
- **`database/`** - Database layer patterns (models, migrations, controllers, services, queries)
- **`modules/`** - Discord bot modules (cogs, commands, events, permissions, interactions)
- **`testing/`** - Testing patterns (pytest, fixtures, markers, coverage, async)
- **`docs/`** - Documentation rules (Zensical, writing standards, structure)
- **`security/`** - Security patterns (secrets, validation, dependencies)
- **`error-handling/`** - Error handling (patterns, logging, Sentry, user feedback)
- **`ui/`** - UI components (Discord Components V2)
- **`meta/`** - System documentation (Gemini rules/commands specifications)

### Commands

Commands are organized by category in `.gemini/commands/`:

- **`code-quality/`** - Code quality workflows (lint, refactor, review)
- **`testing/`** - Testing workflows (run tests, coverage, integration)
- **`database/`** - Database workflows (migration, health, reset)
- **`discord/`** - Discord bot workflows (create module, test command, sync)
- **`security/`** - Security workflows (security review)
- **`debugging/`** - Debugging workflows (debug issues)
- **`error-handling/`** - Error handling workflows (add error handling)
- **`documentation/`** - Documentation workflows (generate, update, serve)
- **`development/`** - Development workflows (setup, docker)

## Usage

Rules are automatically applied by Gemini:

- **Always Apply** - Rules with `alwaysApply: true` are active in every chat
- **File-Scoped** - Rules with `globs` patterns apply when editing matching files
- **Intelligent** - Rules with `description` are selected by Gemini based on context

Commands are invoked manually:

1. Type `/` in Gemini chat
2. Select command from autocomplete list
3. Command executes with current context

Example: `/lint` runs the linting workflow

## Quick Reference

See [rules/rules.mdc](rules/rules.mdc) for a complete catalog of all rules and commands.

## Contributing

See the developer documentation for comprehensive guides on creating and maintaining rules/commands:

- [Creating Rules Guide](../docs/content/developer/guides/creating-cursor-rules.md)
- [Creating Commands Guide](../docs/content/developer/guides/creating-cursor-commands.md)

## Resources

- [AGENTS.md](../AGENTS.md)
