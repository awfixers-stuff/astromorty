# TODO.md

- [ ] Fix db version command not working
- [ ] Update docs on how to setup native discord roles in relation to our config approach.
- [ ] Fix jail setup not being in the config wizard.
- [ ] Make config reset button in wizard be smaller or move to a new command.
- [ ] Fix --debug / DEBUG= / etc standardization and usage in the codebase.

## Plugin System Stability

- [ ] **Document Plugin APIs** - Create a clear guide showing which parts of Tux plugins can safely use
- [ ] **Add Deprecation Warnings** - Set up warnings when old plugin code will be removed in future versions
- [ ] **Check Plugin Imports** - Review what plugins import and ensure they're using safe, stable code
- [ ] **Validate Plugins on Load** - Check plugins when they start up to catch problems early
- [ ] **Version Compatibility** - Document which Tux versions work with plugins and how to upgrade between versions
- [ ] **Plugin Error Handling** - Document how plugins should handle errors and exceptions
- [ ] **Plugin Examples** - Create simple step-by-step guides for building plugins
- [ ] **Test Plugin Compatibility** - Add tests to ensure plugins work correctly with the bot
- [ ] **Detect Breaking Changes** - Set up automatic checks to find code changes that might break plugins
- [ ] **Code Quality Checks** - Add rules to prevent plugins from using unsafe internal code

## Documentation & Types

- [ ] **Complete Documentation** - Make sure all features are properly explained in docs
- [ ] **Check Type Hints** - Verify all code has clear type information for better reliability
- [ ] **Documentation Inventory** - Ensure all important functions appear in documentation search

## Code Organization

- [ ] **Clean Up Internal Code** - Organize internal utilities and separate them from public APIs
- [ ] **Command-Line Tools** - Make CLI commands more reliable and programmable

Fix log channel ui not updating when channel is selected

FIx /config ranks create command not working

## Database Issues

### Session Access Patterns
- [ ] **Inconsistent Session Access** - Services use `self.db.db.session()` (DatabaseCoordinator → DatabaseService) while controllers use `self.db.session()` (DatabaseService directly). Need to standardize the pattern across all services and controllers.
- [ ] **Antinuke Service Session Access** - Currently uses `self.db.db.session()` which is correct but inconsistent with controller patterns. Consider refactoring to match controller pattern or document the difference.
- [ ] **Session Context Manager Usage** - Verify all database operations properly use async context managers for session management to prevent resource leaks.

### Model Issues
- [ ] **Reserved Field Names** - Fixed `metadata` → `event_metadata` in AntinukeEvent model. Need to audit all models for other reserved SQLAlchemy field names (e.g., `metadata`, `registry`, `mapper`, etc.).
- [ ] **Field Name Conflicts** - Check for any other SQLModel/SQLAlchemy reserved attribute names that might cause conflicts.

### Migration Issues
- [ ] **Antinuke Migration** - Create database migration for antinuke system tables (antinuke_config, antinuke_events) with proper enum types, constraints, and indexes.
- [ ] **Enum Type Migrations** - Ensure AntinukeActionType and AntinukeResponseType enums are properly created in PostgreSQL with correct naming.
- [ ] **Migration Testing** - Test antinuke migration upgrade and downgrade paths to ensure rollback works correctly.

### Database Access Patterns
- [ ] **Service vs Controller Pattern** - Services (like AntinukeService) receive DatabaseCoordinator but need DatabaseService for sessions. Controllers receive DatabaseService directly. Consider standardizing on one pattern.
- [ ] **Session Lifecycle Management** - Document and verify proper session lifecycle (create, use, commit/rollback, cleanup) across all database operations.
- [ ] **Transaction Boundaries** - Ensure transaction boundaries are properly defined and all related operations are within the same transaction when needed.

### Performance & Optimization
- [ ] **Session Pooling** - Verify session pooling is working correctly and not creating too many connections.
- [ ] **Query Optimization** - Review antinuke service queries for potential N+1 query problems or missing indexes.
- [ ] **Connection Leaks** - Add monitoring/alerting for potential database connection leaks.

### Error Handling
- [ ] **Database Error Recovery** - Ensure antinuke service properly handles database connection failures, timeouts, and retries.
- [ ] **Transaction Rollback** - Verify all database operations properly rollback on errors, especially in antinuke event recording.
- [ ] **Error Logging** - Ensure database errors in antinuke system are properly logged with context for debugging.

### Data Integrity
- [ ] **Foreign Key Constraints** - Verify antinuke_config foreign key to guild table is properly set up with CASCADE delete.
- [ ] **Constraint Validation** - Test all check constraints in antinuke models (thresholds, IDs, etc.) work correctly.
- [ ] **Index Optimization** - Review and optimize indexes on antinuke_events table for query performance (guild_id, user_id, timestamp, etc.).

### Testing
- [ ] **Database Tests** - Add unit tests for antinuke database operations (config creation, event recording, queries).
- [ ] **Migration Tests** - Add tests to verify antinuke migrations work correctly.
- [ ] **Integration Tests** - Test antinuke system end-to-end with database operations.

Setup sentry sdk for metrics

Set permission errors to not be sent to sentry

## Error Handling System Improvements

### 📚 Documentation & Developer Experience

- [ ] **Error Documentation Suite** - Add comprehensive error handling documentation with architecture overview, configuration guide, and developer API reference
- [ ] **Error Simulation Framework** - Create developer tools for testing error scenarios in staging environments
- [ ] **Error Context Enrichment** - Add structured error context collection including user permissions, command arguments, and system state for better debugging

### 🎨 User Experience Enhancements

- [ ] **Smart Command Suggestions** - Implement intelligent command suggestions when CommandNotFound errors occur, using fuzzy matching on available commands
- [ ] **Error Message Personalization** - Add error message personalization based on user history, preferences, and interaction patterns
- [ ] **Error Message Localization** - Implement error message localization/i18n support for multiple languages beyond English
- [ ] **Dynamic Error Templates** - Create error message templates with variable substitution for dynamic content (user mentions, timestamps, etc.)

### ⚡ Performance & Scalability

- [ ] **Error Processing Caching** - Optimize error processing performance with LRU caching for repeated error configurations and message formatting
- [ ] **Error Rate Limiting** - Implement error rate limiting to prevent spam and abuse of error responses in high-traffic scenarios
- [ ] **Error Recovery Mechanisms** - Add error recovery with automatic retry logic for transient failures (rate limits, network issues)

### 📊 Monitoring & Analytics

- [ ] **Error Analytics Dashboard** - Create error analytics dashboard showing error frequency, trends, and most common issues across guilds
- [ ] **Error Metrics & KPIs** - Implement error handling metrics and KPIs tracking error resolution time, user satisfaction, and system reliability
- [ ] **Error Correlation System** - Add error correlation system to group related errors and identify root causes across multiple failures
- [ ] **Error Escalation System** - Implement error escalation that can alert administrators for critical errors or error spikes

### 🔧 Configuration & Customization

- [ ] **Per-Guild Customization** - Implement per-guild error message customization allowing servers to modify error responses and add custom messages
- [ ] **Error Plugins System** - Create error handling plugins system allowing third-party extensions to add custom error types and handlers
- [ ] **Error Message A/B Testing** - Add error message A/B testing to optimize user experience and error resolution rates

### 🔒 Security & Reliability

- [ ] **Security Filtering** - Implement comprehensive security filtering to prevent sensitive information leakage in error messages
- [ ] **Error Stress Testing** - Create error handling stress testing suite to validate system reliability under high error volume conditions
- [ ] **Enhanced Sentry Integration** - Enhance Sentry integration with custom tags, user context, and error grouping for better issue tracking

### 🎯 High Priority Items

- [ ] **Smart Command Suggestions** - High-impact user experience improvement
- [ ] **Error Analytics Dashboard** - Critical for monitoring system health
- [ ] **Per-Guild Customization** - Allows servers to brand error messages
- [ ] **Error Recovery Mechanisms** - Improves user experience with transient failures
- [ ] **Comprehensive Documentation** - Essential for maintainability
