# Roadmap

This roadmap is a living document that will be updated as the project evolves. It is not a commitment to deliver any specific features or changes, but rather a guide for the project's direction. For more detailed information and updates, please refer to the [CHANGELOG](CHANGELOG.md).

## v0.1.0 - First Major Release

**Status**: Feature complete, final testing phase

- [x] Asynchronous architecture with hybrid commands (slash + prefix)
- [x] Cog loading with hot reload, branded embeds, comprehensive error handling
- [x] Activity rotation, custom help command, dynamic permission system
- [x] Multi-format configuration (TOML/YAML/JSON), emoji management
- [x] Complete moderation suite (ban, kick, warn, timeout, tempban, jail, purge, slowmode)
- [x] Case management with viewing, searching, modification, and thread-safe numbering
- [x] XP/leveling, AFK, reminders, snippets, starboard, status roles
- [x] Bookmarks, temp voice channels, GIF limiting, InfluxDB logging
- [x] Documentation (MkDocs), Docker, CLI (Typer), testing (pytest + Codecov)
- [x] Pre-commit hooks, CI/CD, multi-platform Docker builds
- [x] Database migration (Prisma → SQLModel), package manager (Poetry → uv)
- [x] CLI framework (Click → Typer), type checker (pyright → basedpyright)
- [x] Project layout (flat → src), Alembic migrations
- [x] Plugin system: Deepfry, Flag Remover, Support Notifier, Harmful Commands, Fact, Role Count, TTY Roles, Git, Mail, Mock
- [ ] Final bug fixes, performance optimization, documentation review, release notes

---

## v0.2.0 - Next Release

**Status**: In development

### High Priority Bug Fixes & Improvements

- [ ] Fix `db version` command not working
- [ ] Fix jail setup not being in the config wizard
- [ ] Fix log channel UI not updating when channel is selected
- [ ] Fix `/config ranks create` command not working
- [ ] Standardize `--debug` / `DEBUG=` usage across codebase
- [ ] Update docs on how to setup native Discord roles in relation to config approach
- [ ] Make config reset button in wizard be smaller or move to a new command

### Ticket System

**Status**: In progress

- [x] Database models (Ticket model with status tracking)
- [x] Database controller (TicketController with CRUD operations)
- [x] Discord commands (`/ticket`, `/ticket-close`, `/ticket-assign`)
- [x] Thread-safe ticket numbering
- [ ] Database migrations
- [ ] Testing and validation
- [ ] Documentation
- [ ] Ticket transcripts
- [ ] Ticket statistics and analytics
- [ ] FAQ system integration
- [ ] Auto-responses
- [ ] Priority levels

### Spotify Music System

**Status**: Planned (waiting for ticket system completion)

**Related Documents**: 
- [Spotify Music System Investigation](docs/content/developer/investigations/spotify-music-system.md)
- [Spotify Music System Todos](docs/content/developer/investigations/spotify-music-system-todos.md)

**Implementation Phases**:

#### Phase 1: Foundation (MVP)
- Package updates (`spotify-api.py` async conversion)
- Type definitions (Python types from `spotify-types`)
- Configuration integration
- Core services (Spotify, Audio, Queue)
- Basic commands (`/play`, `/queue`, `/skip`, `/stop`)
- Essential error handling
- Unit tests and quality checks

#### Phase 2: Enhanced Features
- Database models (MusicQueue, MusicPlaylist, MusicPlaylistTrack, MusicGuildSettings)
- Database controllers
- Persistent queue storage
- Advanced commands (`/pause`, `/resume`, `/volume`, `/nowplaying`)
- Permissions system
- Integration tests
- Manual testing

#### Phase 3: Advanced Features
- Playlist management
- Search functionality
- Recommendations
- OAuth integration

#### Phase 4: Polish
- Interactive UI
- Auto-disconnect
- DJ roles
- Statistics

**Total Tasks**: 102 tasks across 12 categories

### Service Dashboard System

**Status**: Planned

**Related Documents**:
- [Service Dashboard Plan](docs/content/developer/guides/service-dashboard-plan.md)
- [Service Dashboard Summary](docs/content/developer/guides/service-dashboard-summary.md)
- [SSH TUI Dashboard Plan](docs/content/developer/guides/ssh-tui-dashboard-plan.md) (Related: Terminal-based admin interface)

**Implementation Timeline**: ~12 weeks

#### Phase 1-2: Foundation & Core (4 weeks)
- Database models (ServiceRegistry, ServiceConfiguration)
- Service registry system
- Service discovery mechanism
- Health monitoring system
- Configuration management

#### Phase 3: Dashboard Interface (2 weeks)
- Discord commands (`/services list`, `/services status`, `/services enable`, etc.)
- Rich UI components
- Status reporting

#### Phase 4: External Services (2 weeks)
- Integration with external APIs (Sentry, GitHub, etc.)
- Configuration schema support
- Dynamic configuration updates

#### Phase 5: Advanced Features (2 weeks)
- Service dependencies tracking
- Automated health monitoring
- Metrics and logging

#### Phase 6: Documentation & Testing (2 weeks)
- Complete documentation
- Comprehensive test suite
- Migration guide

**Features**:
- Service discovery and cataloging
- Health monitoring and status tracking
- Dynamic configuration management
- Enable/disable services at runtime
- Extensible architecture for future services

### Plugin System Stability

- [ ] Document Plugin APIs - Clear guide showing which parts of Tux plugins can safely use
- [ ] Add Deprecation Warnings - Warnings when old plugin code will be removed
- [ ] Check Plugin Imports - Review what plugins import and ensure safe, stable code usage
- [ ] Validate Plugins on Load - Check plugins at startup to catch problems early
- [ ] Version Compatibility - Document which Tux versions work with plugins
- [ ] Plugin Error Handling - Document how plugins should handle errors
- [ ] Plugin Examples - Create simple step-by-step guides for building plugins
- [ ] Test Plugin Compatibility - Add tests to ensure plugins work correctly
- [ ] Detect Breaking Changes - Automatic checks for code changes that might break plugins
- [ ] Code Quality Checks - Rules to prevent plugins from using unsafe internal code

### Error Handling System Improvements

#### Documentation & Developer Experience
- [ ] Error Documentation Suite - Architecture overview, configuration guide, API reference
- [ ] Error Simulation Framework - Developer tools for testing error scenarios
- [ ] Error Context Enrichment - Structured error context collection

#### User Experience Enhancements
- [ ] Smart Command Suggestions - Intelligent suggestions when CommandNotFound errors occur
- [ ] Error Message Personalization - Personalization based on user history
- [ ] Error Message Localization - i18n support for multiple languages
- [ ] Dynamic Error Templates - Templates with variable substitution

#### Performance & Scalability
- [ ] Error Processing Caching - LRU caching for repeated error configurations
- [ ] Error Rate Limiting - Prevent spam and abuse of error responses
- [ ] Error Recovery Mechanisms - Automatic retry logic for transient failures

#### Monitoring & Analytics
- [ ] Error Analytics Dashboard - Error frequency, trends, and common issues
- [ ] Error Metrics & KPIs - Error resolution time, user satisfaction, system reliability
- [ ] Error Correlation System - Group related errors and identify root causes
- [ ] Error Escalation System - Alert administrators for critical errors

#### Configuration & Customization
- [ ] Per-Guild Customization - Per-guild error message customization
- [ ] Error Plugins System - Third-party extensions for custom error types
- [ ] Error Message A/B Testing - Optimize user experience and error resolution rates

#### Security & Reliability
- [ ] Security Filtering - Prevent sensitive information leakage in error messages
- [ ] Error Stress Testing - Validate system reliability under high error volume
- [ ] Enhanced Sentry Integration - Custom tags, user context, error grouping

### Documentation & Code Quality

- [ ] Complete Documentation - Ensure all features are properly explained
- [ ] Check Type Hints - Verify all code has clear type information
- [ ] Documentation Inventory - Ensure all important functions appear in documentation search
- [ ] Clean Up Internal Code - Organize internal utilities and separate from public APIs
- [ ] Command-Line Tools - Make CLI commands more reliable and programmable

### Infrastructure Improvements

- [ ] Setup Sentry SDK for metrics
- [ ] Set permission errors to not be sent to Sentry
- [ ] Enhanced monitoring and observability

### HTTP Endpoint Migration

**Status**: Planned

**Related Documents**:
- [HTTP Endpoint Migration Plan](docs/http-endpoint-migration-plan.md)

**Overview**: Migrate from WebSocket Gateway to HTTP-based endpoints for receiving Discord events and interactions, enabling serverless deployment and better scalability.

**Implementation Timeline**: 5-10 weeks (phased approach)

#### Phase 1: Interactions Endpoint (2-3 weeks)
- Create interactions endpoint handler with signature verification
- Update FastAPI app with interactions route
- Create interaction router to route HTTP interactions to command handlers
- Update bot configuration to support HTTP interactions
- Testing and validation

#### Phase 2: Webhook Events URL (3-4 weeks)
- Create webhook events handler
- Event subscription configuration
- Event router for HTTP events
- Update event handlers for HTTP compatibility
- Event deduplication (if receiving from both sources)

#### Phase 3: Full HTTP Migration (Optional, 2-3 weeks)
- Migrate remaining features (voice, presence)
- Remove WebSocket dependency
- Update dependencies and imports
- Full system testing

**Key Benefits**:
- Serverless-friendly deployment
- Better scalability
- Reduced infrastructure costs
- No persistent connection management
- Easier horizontal scaling

**Limitations**:
- Higher latency for some operations
- Cannot use all Discord features (voice, presence updates)
- Requires public HTTPS endpoint

### Components V2 Migration

**Status**: Planned

**Related Documents**:
- [Components V2 Migration Plan](docs/components-v2-migration-plan.md)

**Overview**: Migrate from Discord's legacy component system (View-based) to Components V2 (LayoutView-based) for enhanced UI capabilities and modern Discord features.

**Implementation Timeline**: 5 weeks

#### Phase 1: Foundation & Utilities (Week 1)
- Create embed-to-container conversion utilities
- Create TextDisplay formatters
- Update Cursor rules for Components V2
- Create migration helper functions

#### Phase 2: Simple Components (Week 1-2)
- Migrate `XkcdButtons` to LayoutView
- Migrate `GithubButton` to LayoutView
- Migrate close button views
- Update all usages

#### Phase 3: Medium Complexity (Week 2-3)
- Migrate `BaseConfirmationView` and subclasses
- Migrate `TldrPaginatorView`
- Handle pagination with Components V2
- Update embed-based messages to use Container

#### Phase 4: Complex Components (Week 3-4)
- Migrate `BaseHelpView` and all subclasses
- Migrate help command select menus and buttons
- Handle complex navigation state
- Update help command embed usage

#### Phase 5: Modals (Week 4)
- Migrate modals to use Label components
- Update TextInput usage
- Test modal interactions

#### Phase 6: Integration & Testing (Week 5)
- Update all command modules
- Comprehensive testing
- Performance validation
- Documentation updates

**Key Benefits**:
- Enhanced layout capabilities (Containers, Sections, TextDisplay)
- Up to 40 components per message (vs 25 in legacy)
- Better visual organization
- Modern component system with improved flexibility
- Access to new component types (MediaGallery, File, Separator)

**Critical Constraints**:
- Cannot send `content`, `embeds`, `stickers`, or `polls` with Components V2
- Must use `TextDisplay` and `Container` instead
- Max 4000 characters across all TextDisplay items
- Max 40 components total (including nested)
- Once a message uses Components V2, it cannot be converted back

### Discord Role Connections

**Status**: Planned

**Related Documents**:
- [Role Connections Implementation Plan](docs/role-connections-implementation-plan.md)

**Overview**: Implement Discord Role Connections to allow users to link external accounts (GitHub, Twitter, Steam, etc.) and receive automatic role assignments based on verification metadata.

**Implementation Timeline**: ~5 weeks

#### Phase 1: Foundation Setup (Week 1)
- Discord application configuration for Role Connections
- Web server foundation (FastAPI)
- Database models (RoleConnection, ConnectionPlatform)
- Database migrations

#### Phase 2: OAuth2 Implementation (Week 2)
- OAuth flow endpoints
- Token management (secure storage, refresh mechanisms)
- State management (CSRF protection)

#### Phase 3: External API Integration (Week 3)
- GitHub API integration
- Twitter API integration
- Steam API integration
- Profile verification logic
- Metadata mapping

#### Phase 4: Discord Integration (Week 4)
- Discord metadata API integration
- Role assignment logic
- Event handlers (on_member_update, on_ready)
- User commands (`/link`, `/unlink`, `/connections`)

#### Phase 5: User Interface & Admin Controls (Week 5)
- User dashboard (optional web interface)
- Admin commands for managing connections
- Configuration management
- Audit & monitoring

**Key Features**:
- OAuth2 flow for external account linking
- Automatic role assignment based on verified connections
- Support for multiple platforms (GitHub, Twitter, Steam)
- Admin controls for connection management
- Comprehensive audit logging

### SSH TUI Dashboard

**Status**: Planned

**Related Documents**:
- [SSH TUI Dashboard Plan](docs/content/developer/guides/ssh-tui-dashboard-plan.md)

**Overview**: Implement a Terminal User Interface (TUI) for remote bot administration via SSH, providing secure terminal-based access to bot services, monitoring, and configuration management.

**Implementation Timeline**: ~12 weeks

#### Phase 1: Foundation (Week 1-2)
- Database models (SSHAdminKey, SSHSession)
- Basic AsyncSSH server implementation
- Public key authentication
- Session management
- Basic audit logging

#### Phase 2: TUI Framework (Week 3-4)
- Set up Textual application framework
- Create basic TUI layout and widgets
- Implement command input/display
- Add basic service status display
- Connect TUI to SSH server

#### Phase 3: Admin API (Week 5-6)
- Create admin API layer
- Implement service discovery
- Add permission validation
- Create command execution framework
- Add configuration management

#### Phase 4: Advanced Features (Week 7-8)
- Real-time log streaming
- Service health monitoring
- Interactive dashboards
- Module management (load/unload)
- User management features

#### Phase 5: Security & Polish (Week 9-10)
- Comprehensive audit logging
- Rate limiting and security controls
- Permission management interface
- Session recording capabilities
- Improved TUI user experience

#### Phase 6: Testing & Documentation (Week 11-12)
- Comprehensive test suite
- User and admin documentation
- Performance testing and optimization
- Security audit and hardening

**Key Features**:
- Secure SSH access with public key authentication
- Full bot service management capabilities
- Real-time monitoring and log viewing
- Integration with existing permission system
- Comprehensive audit logging
- Session management and security controls
- User-friendly terminal interface

### Performance Optimizations

**Status**: Analysis Complete, Implementation Planned

**Related Documents**:
- [Multi-Language Optimization Analysis](docs/multi-language-optimization-analysis.md)
- [Caching Strategy](docs/caching-strategy.md)

**Overview**: Performance optimization opportunities identified through analysis. Redis caching strategy already implemented.

#### Caching Strategy (Implemented)
- ✅ Redis integration for distributed caching
- ✅ Cache-aside pattern for read-heavy data
- ✅ Write-through pattern for frequently updated data
- ✅ TTL-based eviction strategies
- ✅ Cache invalidation on updates
- ✅ Graceful degradation if Redis unavailable

**Performance Improvements**:
- Prefix lookup: 5-10x faster (Redis cache hit ~1ms vs DB query ~5-10ms)
- Guild config access: 5-10x faster
- Levels lookup: 5-10x faster

#### Multi-Language Optimization Opportunities

**High Priority (Quick Wins)**:
- [ ] Image Processing with Rust (5-10x speedup)
  - Create Rust crate for deepfry algorithm
  - Expose via PyO3 bindings
  - Estimated Impact: High
  - Risk: Low (isolated module)

- [ ] Regex Optimization (2-5x speedup)
  - Use Python `regex` package (Rust-based) instead of `re`
  - Or create minimal Rust bindings for hot regex paths
  - Estimated Impact: Medium
  - Risk: Very Low (drop-in replacement)

**Medium Priority (Strategic Improvements)**:
- [ ] XP Calculation in Rust (1.5-2x speedup)
  - Extract pure computation functions
  - Keep business logic in Python
  - Estimated Impact: Medium
  - Risk: Low-Medium

- [ ] String Processing Optimization
  - Identify hot paths through profiling
  - Extract to Rust if beneficial
  - Estimated Impact: Variable
  - Risk: Low

**Low Priority (Defer)**:
- [ ] HTTP Client (Rust) - Network I/O is bottleneck, not HTTP parsing
- [ ] PostgreSQL Functions - Database already well-optimized

**Recommendation**: Start with image processing optimization using Rust, as it provides the best ROI with manageable complexity. Use Python `regex` package as a quick win for regex performance.

---

## Backlog

> **Note**: The following items are under consideration for future releases. The roadmap will be redesigned after v0.1.0 release.

### Configuration & Multi-Guild

- Interactive configuration wizard, guild-specific feature toggles
- Configuration import/export, validation, migration tools
- Enhanced multi-guild optimization, per-guild feature flags and prefixes
- Cross-guild statistics and analytics

### Moderation Enhancements

- Multi-user moderation commands, bulk operations, templates
- Enhanced case search and filtering
- Improved error messages, command analytics

### Performance & Caching

- [x] Redis integration for distributed caching (✅ Implemented - see [Caching Strategy](docs/caching-strategy.md))
- [x] Permission, guild config, and user data caching with TTL (✅ Implemented)
- [ ] Command cooldowns with Redis backend
- [ ] Database query optimization, connection pooling improvements
- [ ] Async operation optimization, memory profiling
- [ ] Automated slowmode based on activity
- [ ] Auto-moderation triggers, scheduled tasks system
- [ ] Multi-language optimizations (see [Multi-Language Optimization Analysis](docs/multi-language-optimization-analysis.md))

### Statistics & Tracking

- User activity and command usage statistics
- Server growth metrics, feature usage tracking
- Invite tracking with credit system
- Nickname and role change history
- Message edit/delete logging
- Statistical reports, visualizations, export functionality

### Auto-Moderation

- Regex-based content filtering, spam detection
- Heat system (escalating warnings), rate limiting
- Link filtering with whitelist, mention spam protection
- Raid protection, alt account detection
- Suspicious activity monitoring, automated restrictions

### External Integrations

- RSS subscription service with filtering and formatting
- Repology API integration for package search and updates
- GitHub webhooks, custom webhook support
- API endpoints for external services

### Economy & Engagement

- Virtual currency, wallets, transactions
- Shop system with purchasable items
- Daily rewards, streaks, achievements, badges
- Leaderboards, contests, giveaways, custom rewards

### Support & Ticketing

**Status**: In progress (see v0.2.0 section above)

- [x] Ticket creation, management
- [x] Staff assignment
- [ ] Ticket transcripts
- [ ] Category-based routing
- [ ] Ticket statistics and analytics
- [ ] FAQ system, auto-responses
- [ ] Priority levels

### Web Dashboard

- Authentication, guild management, real-time statistics
- Configuration management UI, moderation case viewer
- User management, log viewer, analytics
- Plugin management, RESTful API, WebSocket support

### Stable Release (v1.0.0)

- Comprehensive code review, security audit
- Performance benchmarking, load testing
- Documentation completeness, migration guides
- Discord verification, bot list submissions
- Public announcement, community server

### Future Considerations

- Voice features (partially planned in Spotify Music System)
- AI/ML moderation
- Mobile app
- Multi-language support
- Advanced analytics
- Custom command builder
- Integration marketplace
