---
title: SSH TUI Dashboard Implementation Plan
description: Comprehensive plan for implementing a terminal user interface for remote bot administration via SSH.
tags:
  - developer-guide
  - admin
  - ssh
  - tui
  - dashboard
  - remote-administration
---

# SSH TUI Dashboard Implementation Plan

## Overview

This document outlines the implementation of a **Terminal User Interface (TUI)** for remote bot administration via **SSH**. The TUI will provide a simplified, dedicated dashboard for administering backend services, monitoring bot health, and managing configuration through a secure terminal interface.

## Goals & Objectives

### Primary Goals
1. **Secure Remote Administration** - Provide secure SSH-based access to bot administration
2. **Backend Service Management** - Monitor and manage all bot services (database, HTTP, Discord connections)
3. **Real-time Monitoring** - Live dashboard for bot status, logs, and metrics
4. **Simplified Administration** - Command-line interface for common admin tasks
5. **Integration with Existing Systems** - Leverage existing permission and configuration systems

### Secondary Goals
1. **Offline Capability** - Basic admin functions available during Discord API outages
2. **Audit Trail** - Comprehensive logging of all administrative actions
3. **Multi-guild Support** - Manage multiple Discord guilds from single interface
4. **Session Management** - Persistent sessions with proper isolation

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SSH Client Terminal                       │
│  (Admin connects via ssh admin@bot-host:port)               │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 AsyncSSH Server                             │
│  - Key-based authentication                               │
│  - Session management                                      │
│  - Terminal handling                                       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 TUI Application (Textual)                    │
│  - Admin dashboard widgets                                  │
│  - Command interface                                        │
│  - Real-time updates                                       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Admin API Layer                                │
│  - Service discovery                                        │
│  - Command execution                                       │
│  - Permission validation                                   │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               Existing Bot Services                         │
│  - DatabaseService, HTTPClient                             │
│  - PermissionSystem                                        │
│  - Configuration Management                                │
│  - Module Management                                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. SSH Server (AsyncSSH)

**Location**: `src/astromorty/ssh/server.py`

**Responsibilities**:
- SSH server implementation
- Public key authentication
- Session management
- Terminal type handling
- Connection security

**Key Features**:
- Public key authentication only (no passwords)
- Rate limiting and connection throttling
- Session timeout management
- Multi-user support with isolation

### 2. TUI Application (Textual)

**Location**: `src/astromorty/ssh/tui/`

**Responsibilities**:
- Terminal-based user interface
- Interactive widgets and controls
- Real-time data display
- Command input and handling

**Key Features**:
- Dashboard with service status
- Interactive command interface
- Real-time log viewer
- Configuration management interface

### 3. Admin API Layer

**Location**: `src/astromorty/ssh/api/`

**Responsibilities**:
- Bridge between TUI and bot services
- Permission validation
- Command execution
- Data formatting

**Key Features**:
- Service discovery and introspection
- Secure command execution
- Permission-aware access control
- Structured data responses

### 4. Session Management

**Location**: `src/astromorty/ssh/session.py`

**Responsibilities**:
- User session tracking
- Permission caching
- Audit logging
- Resource cleanup

### 5. Authentication System

**Location**: `src/astromorty/ssh/auth.py`

**Responsibilities**:
- SSH key validation
- User-to-Discord account mapping
- Permission verification
- Session establishment

## Database Schema

### SSH Keys Model

```python
# src/astromorty/database/models/ssh_admin.py

class SSHAdminKey(BaseModel, table=True):
    """SSH public keys for admin access."""
    
    __tablename__ = "ssh_admin_keys"
    
    id: int = Field(primary_key=True, sa_type=Integer)
    
    # Link to Discord user
    discord_user_id: int = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        description="Discord user ID"
    )
    
    # SSH key details
    key_type: str = Field(description="SSH key type (ssh-rsa, ssh-ed25519, etc.)")
    key_data: str = Field(description="SSH public key data")
    key_comment: str | None = Field(default=None, description="Key comment/name")
    fingerprint: str = Field(description="SHA256 fingerprint")
    
    # Permissions
    permission_level: int = Field(default=10, description="Permission level (0-10)")
    allowed_guilds: list[int] = Field(
        default_factory=list,
        sa_type=JSON,
        description="Guild IDs this key can access (empty = all)"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_used: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)
    
    __table_args__ = (
        Index("idx_ssh_key_user", "discord_user_id"),
        Index("idx_ssh_key_fingerprint", "fingerprint"),
    )
```

### SSH Sessions Model

```python
# src/astromorty/database/models/ssh_admin.py (continued)

class SSHSession(BaseModel, table=True):
    """SSH session tracking for audit purposes."""
    
    __tablename__ = "ssh_sessions"
    
    id: int = Field(primary_key=True, sa_type=Integer)
    session_id: str = Field(unique=True, description="Unique session identifier")
    
    # Session details
    ssh_key_id: int = Field(foreign_key="ssh_admin_keys.id", ondelete="CASCADE")
    discord_user_id: int = Field(fore_key="users.id", ondelete="CASCADE")
    
    # Connection info
    client_ip: str = Field(description="Client IP address")
    client_version: str | None = Field(default=None, description="SSH client version")
    terminal_type: str | None = Field(default=None, description="Terminal type")
    
    # Timestamps
    connected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))
    disconnected_at: datetime | None = Field(default=None)
    
    # Session data
    commands_executed: int = Field(default=0)
    bytes_sent: int = Field(default=0)
    bytes_received: int = Field(default=0)
    
    # Status
    is_active: bool = Field(default=True)
    disconnect_reason: str | None = Field(default=None)
    
    __table_args__ = (
        Index("idx_ssh_session_user", "discord_user_id"),
        Index("idx_ssh_session_active", "is_active", "connected_at"),
    )
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals**: Basic SSH server and authentication

**Tasks**:
1. Create database models and migrations
2. Implement basic AsyncSSH server
3. Add public key authentication
4. Create session management
5. Add basic audit logging

**Deliverables**:
- SSH server that accepts connections
- Key-based authentication system
- Database models for keys and sessions
- Basic session tracking

### Phase 2: TUI Framework (Week 3-4)

**Goals**: Basic terminal interface

**Tasks**:
1. Set up Textual application framework
2. Create basic TUI layout and widgets
3. Implement command input/display
4. Add basic service status display
5. Connect TUI to SSH server

**Deliverables**:
- Functional TUI over SSH
- Basic command interface
- Service status display
- Interactive terminal controls

### Phase 3: Admin API (Week 5-6)

**Goals**: Bridge TUI to bot services

**Tasks**:
1. Create admin API layer
2. Implement service discovery
3. Add permission validation
4. Create command execution framework
5. Add configuration management

**Deliverables**:
- Admin API for service access
- Permission-aware command execution
- Service monitoring capabilities
- Configuration management interface

### Phase 4: Advanced Features (Week 7-8)

**Goals**: Real-time monitoring and management

**Tasks**:
1. Implement real-time log streaming
2. Add service health monitoring
3. Create interactive dashboards
4. Add module management (load/unload)
5. Implement user management features

**Deliverables**:
- Real-time log viewer
- Service health dashboard
- Module management interface
- User/guild administration tools

### Phase 5: Security & Polish (Week 9-10)

**Goals**: Security hardening and user experience

**Tasks**:
1. Implement comprehensive audit logging
2. Add rate limiting and security controls
3. Create permission management interface
4. Add session recording capabilities
5. Improve TUI user experience

**Deliverables**:
- Comprehensive security features
- Permission management system
- Session recording and playback
- Polished user interface

### Phase 6: Testing & Documentation (Week 11-12)

**Goals**: Testing and documentation

**Tasks**:
1. Create comprehensive test suite
2. Write user documentation
3. Create admin setup guide
4. Performance testing and optimization
5. Security audit and hardening

**Deliverables**:
- Complete test coverage
- User and admin documentation
- Performance optimization
- Security audit report

## TUI Features

### Main Dashboard

```
┌─ Astromorty Admin Dashboard ─────────────────────────────────────┐
│ Bot Status: ● ONLINE │ Guilds: 12 │ Uptime: 3d 14h 22m          │
├─────────────────────────────────────────────────────────────────┤
│ ┌─ Services ─────┐ ┌─ Recent Activity ─────┐ ┌─ Quick Actions ─┐ │
│ │ ● Database    │ │ • User banned: @user   │ │ [Reload Config] │ │
│ │ ● HTTP Client │ │ • Module loaded: mod   │ │ [View Logs]     │ │
│ │ ● Discord API │ │ • Config updated       │ │ [Manage Users]  │ │
│ │ ○ Sentry      │ │ • Service error: mail  │ │ [Service Mgmt]  │ │
│ └────────────────┘ └───────────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ ┌─ Command Input ─────────────────────────────────────────────┐ │
│ │ admin> reload_module moderation                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Service Management Interface

```
┌─ Service Management ───────────────────────────────────────────┐
│ Service Name    │ Status │ Health │ Last Check │ Actions         │
│ Database        │ ● Active│ Good   │ 2s ago     │ [Restart] [Test]│
│ HTTP Client     │ ● Active│ Good   │ 5s ago     │ [Restart] [Test]│
│ Discord API     │ ● Active│ Good   │ 1s ago     │ [Reconnect]     │
│ Sentry          │ ○ Inactive│ N/A   │ Never      │ [Enable] [Config]│
│ Mailcow API     │ ✗ Error │ Bad    │ 10s ago    │ [Restart] [Logs]│
├─────────────────────────────────────────────────────────────────┤
│ Selected Service: Database                                       │
│ ┌─ Service Details ──────────────────────────────────────────┐ │
│ │ Connection Pool: 8/10 active                                 │ │
│ │ Query Rate: 45/s                                             │ │
│ │ Last Error: None                                             │ │
│ │ Uptime: 3d 14h 22m                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Log Viewer

```
┌─ Real-time Logs ────────────────────────────────────────────────┐
│ [2024-01-15 14:32:15] INFO  Database connection established     │
│ [2024-01-15 14:32:16] INFO  Discord gateway connected           │
│ [2024-01-15 14:32:17] WARN  Rate limit approaching (95/100)     │
│ [2024-01-15 14:32:18] INFO  User command: !help                 │
│ [2024-01-15 14:32:19] ERROR HTTP request failed: timeout        │
│ [2024-01-15 14:32:20] INFO  Retrying HTTP request...             │
│ [2024-01-15 14:32:21] INFO  HTTP request succeeded               │
│─────────────────────────────────────────────────────────────────────│
│ Filter: [ERROR] │ Level: ALL │ Module: ALL │ Paused: No           │
│ Controls: [Pause] [Clear] [Save] [Filter] [Tail]                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Command Interface

### Admin Commands

```bash
# Service Management
admin> service list                    # List all services
admin> service status database         # Get service status
admin> service restart sentry          # Restart service
admin> service enable mailcow           # Enable service

# Module Management
admin> module list                     # List loaded modules
admin> module load moderation          # Load module
admin> module reload help              # Reload module
admin> module unload debug             # Unload module

# User Management
admin> user info @user#1234            # Get user info
admin> user ban @user#1234 "Reason"    # Ban user
admin> user unban @user#1234           # Unban user
admin> user permission set @user#1234 5 # Set permission level

# Guild Management
admin> guild list                      # List guilds
admin> guild info 123456789            # Get guild info
admin> guild config set 123456789      # Set guild config

# Configuration
admin> config list                     # List config options
admin> config get bot.prefix           # Get config value
admin> config set bot.prefix "!"        # Set config value
admin> config reload                   # Reload configuration

# System Management
admin> system status                   # System status
admin> system logs tail 100            # View recent logs
admin> system metrics                   # System metrics
admin> system shutdown                 # Shutdown bot
```

## Security Considerations

### Authentication & Authorization

1. **Public Key Authentication Only**
   - No password authentication
   - Ed25519 keys recommended
   - Per-user key management

2. **Permission Integration**
   - Integration with existing permission system
   - Per-guild access control
   - Command-level permissions

3. **Session Security**
   - Session timeout (default: 30 minutes idle)
   - Connection encryption
   - IP-based access control (optional)

### Audit & Logging

1. **Comprehensive Audit Trail**
   - All commands logged
   - Session start/end tracking
   - File access logging

2. **Security Monitoring**
   - Failed authentication attempts
   - Suspicious command patterns
   - Anomaly detection

3. **Data Protection**
   - No sensitive data in logs
   - Secure credential storage
   - Encrypted config values

### Access Control

1. **Multi-level Permissions**
   - Bot owner (full access)
   - Guild administrators (guild-specific)
   - Service administrators (service-specific)

2. **Command Whitelisting**
   - Only approved administrative commands
   - Context-aware command availability
   - Safe default permissions

## Integration Points

### Existing Bot Services

1. **DatabaseService**
   - Connection monitoring
   - Query performance metrics
   - Migration management

2. **HTTPClient**
   - Request monitoring
   - Rate limiting status
   - External API health

3. **PermissionSystem**
   - User permission verification
   - Role management
   - Guild-specific permissions

4. **Configuration System**
   - Runtime configuration updates
   - Validation and rollback
   - Environment-specific configs

5. **Module System**
   - Dynamic module loading
   - Hot reloading
   - Dependency management

### Database Models to Extend

1. **Users Table**
   - SSH key associations
   - Admin permissions
   - Session tracking

2. **Guilds Table**
   - SSH access permissions
   - Admin assignments
   - Configuration overrides

## Performance Considerations

### Resource Management

1. **Connection Limits**
   - Maximum concurrent SSH sessions (default: 5)
   - Memory usage per session
   - CPU usage monitoring

2. **Caching Strategy**
   - Permission caching
   - Service status caching
   - Configuration caching

3. **Async Operations**
   - Non-blocking I/O throughout
   - Proper coroutine management
   - Timeout handling

### Scalability

1. **Session Isolation**
   - Per-session resource limits
   - Memory cleanup on disconnect
   - Graceful session termination

2. **Background Tasks**
   - Health monitoring
   - Log streaming
   - Metrics collection

## Deployment & Configuration

### Environment Variables

```bash
# SSH Server Configuration
SSH_ADMIN_ENABLED=true
SSH_ADMIN_PORT=8022
SSH_ADMIN_HOST_KEYS="/path/to/ssh_host_keys"
SSH_ADMIN_MAX_SESSIONS=5
SSH_ADMIN_SESSION_TIMEOUT=1800  # 30 minutes

# Security Configuration
SSH_ADMIN_REQUIRE_2FA=false
SSH_ADMIN_ALLOWED_NETWORKS="10.0.0.0/8,192.168.0.0/16"
SSH_ADMIN_RATE_LIMIT=10  # requests per minute

# Logging Configuration
SSH_ADMIN_LOG_LEVEL=INFO
SSH_ADMIN_AUDIT_LOGS=true
SSH_ADMIN_SESSION_RECORDING=false
```

### Docker Integration

```dockerfile
# Add to existing Dockerfile
RUN apt-get update && apt-get install -y \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# SSH configuration directory
VOLUME ["/etc/astromorty/ssh"]
```

### Database Migration

```python
# Migration file for SSH admin tables
"""Add SSH admin tables

Revision ID: ssh_admin_001
Revises: previous_revision
Create Date: 2024-01-15 14:32:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Migration code here
```

## Testing Strategy

### Unit Tests

1. **SSH Server Tests**
   - Connection handling
   - Authentication validation
   - Session management

2. **TUI Tests**
   - Widget rendering
   - User interaction
   - Data display

3. **API Layer Tests**
   - Service integration
   - Permission validation
   - Error handling

### Integration Tests

1. **End-to-End SSH Tests**
   - Full SSH connection flow
   - Command execution
   - Session management

2. **Service Integration Tests**
   - Real service connections
   - Permission enforcement
   - Configuration updates

### Security Tests

1. **Authentication Tests**
   - Invalid key rejection
   - Permission boundary testing
   - Session hijacking attempts

2. **Input Validation Tests**
   - Command injection prevention
   - Parameter validation
   - Error handling

## Troubleshooting

### Common Issues

1. **SSH Connection Issues**
   - Key format problems
   - Permission denied
   - Network connectivity

2. **TUI Rendering Issues**
   - Terminal compatibility
   - Screen size problems
   - Character encoding

3. **Service Integration Issues**
   - Permission failures
   - Service unavailability
   - Configuration errors

### Debug Commands

```bash
# Test SSH connection
ssh -v -p 8022 admin@bot-host

# Check SSH server status
admin> system status
admin> service status ssh-server

# View session logs
admin> logs filter ssh-server
admin> logs session <session_id>
```

## Future Enhancements

### Phase 7+ Features

1. **Web Terminal Alternative**
   - Browser-based terminal interface
   - WebSocket communication
   - Same backend API

2. **Multi-user Collaboration**
   - Shared sessions
   - Screen sharing
   - Collaborative editing

3. **Advanced Monitoring**
   - Performance metrics dashboard
   - Alert configuration
   - Automated responses

4. **Service Templates**
   - Pre-configured service setups
   - Quick deployment templates
   - Configuration presets

5. **API Extensions**
   - RESTful admin API
   - Third-party integrations
   - Custom command plugins

## Getting Started

### Initial Setup

1. **Database Migration**
   ```bash
   uv run db new "Add SSH admin tables"
   uv run db dev
   ```

2. **SSH Key Generation**
   ```bash
   # Generate host keys
   ssh-keygen -t ed25519 -f /etc/astromorty/ssh/host_key
   
   # Generate admin keys
   ssh-keygen -t ed25519 -f ~/.ssh/astromorty_admin
   ```

3. **Admin Setup**
   ```bash
   # Add SSH key to database
   admin> ssh key add ~/.ssh/astromorty_admin.pub --user @user#1234 --level 10
   ```

### Connection

```bash
# Connect to admin SSH
ssh -p 8022 -i ~/.ssh/astromorty_admin admin@bot-host

# First time connection
admin> help
admin> service list
admin> system status
```

## Success Criteria

1. ✅ Secure SSH access with public key authentication
2. ✅ Full bot service management capabilities
3. ✅ Real-time monitoring and log viewing
4. ✅ Integration with existing permission system
5. ✅ Comprehensive audit logging
6. ✅ Session management and security controls
7. ✅ User-friendly terminal interface
8. ✅ Complete documentation and testing

## Dependencies

### New Dependencies

```toml
# Add to pyproject.toml
asyncssh = "^2.14.0"        # SSH server implementation
textual = "^0.44.0"         # TUI framework
rich = "^13.7.0"            # Terminal formatting (already dependency)
```

### Optional Dependencies

```toml
paramiko = "^3.3.0"         # Alternative SSH implementation
cryptography = "^41.0.0"     # Enhanced cryptographic operations
```

## Timeline Summary

- **Phase 1-2**: Foundation and TUI framework (4 weeks)
- **Phase 3**: Admin API layer (2 weeks)
- **Phase 4**: Advanced features (2 weeks)
- **Phase 5**: Security and polish (2 weeks)
- **Phase 6**: Testing and documentation (2 weeks)

**Total**: ~12 weeks for complete implementation

## Questions & Considerations

### Open Questions

1. Should SSH sessions be able to survive bot restarts?
2. How to handle service-specific authentication (API keys, tokens)?
3. Should we implement a configuration rollback system?
4. How to handle concurrent modifications to the same data?
5. Should there be different permission levels for SSH vs Discord?

### Design Decisions Needed

1. **SSH Key Management**: Centralized vs per-user key storage
2. **Session Persistence**: How to handle bot restarts
3. **Real-time Updates**: Push vs pull for data updates
4. **Command Permissions**: Separate from Discord permissions or integrated
5. **Logging Granularity**: What level of detail to log for audit purposes

## References

- [AsyncSSH Documentation](https://asyncssh.readthedocs.io/)
- [Textual TUI Framework](https://textual.textual.io/)
- [SSH Security Best Practices](https://www.ssh.com/academy/security)
- [Service Dashboard Plan](./service-dashboard-plan.md)
- [Database Models Documentation](../concepts/database/models.md)
- [Permission System](../concepts/core/permission-system.md)