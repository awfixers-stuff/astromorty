---
title: Service Dashboard Implementation Plan
description: Comprehensive plan for implementing a dashboard system to manage all available services with extensibility for future additions.
tags:
  - developer-guide
  - services
  - dashboard
  - architecture
---

# Service Dashboard Implementation Plan

## Overview

This document outlines a comprehensive plan for implementing a service management dashboard that can:

1. **Discover and catalog** all available services (internal and external)
2. **Monitor service health** and status
3. **Manage service configuration** dynamically
4. **Enable/disable services** at runtime
5. **Extend easily** to add new services in the future

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Interface                       │
│  (Web UI / Discord Commands / API)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Registry & Manager                       │
│  - Service Discovery                                         │
│  - Service Metadata                                          │
│  - Health Monitoring                                         │
│  - Configuration Management                                 │
└──────────────┬───────────────────────────────┬───────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│   Internal Services      │    │   External Service           │
│   Registry               │    │   Integrations                │
│                          │    │                              │
│  - Moderation            │    │  - Sentry                    │
│  - Hot Reload            │    │  - GitHub                    │
│  - HTTP Client           │    │  - Mailcow                   │
│  - Emoji Manager         │    │  - Wolfram Alpha             │
│  - Service Wrappers      │    │  - InfluxDB                  │
│    (Godbolt, TLDR, etc.) │    │  - Supabase                  │
│                          │    │  - Redis                     │
└──────────────────────────┘    └──────────────────────────────┘
```

### Core Components

1. **Service Registry** - Central catalog of all services
2. **Service Metadata** - Structured information about each service
3. **Health Monitor** - Status checking and health reporting
4. **Configuration Manager** - Dynamic configuration updates
5. **Dashboard Interface** - User-facing management interface

## Database Schema

### Service Registry Model

```python
# src/tux/database/models/service_registry.py

class ServiceType(str, Enum):
    """Service type classification."""
    
    INTERNAL = "internal"  # Built-in bot services
    EXTERNAL = "external"  # Third-party integrations
    WRAPPER = "wrapper"  # API wrapper services


class ServiceStatus(str, Enum):
    """Service operational status."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"


class ServiceRegistry(BaseModel, table=True):
    """Registry of all available services in the bot.
    
    This model tracks metadata, configuration, and status for all services,
    enabling dynamic management and monitoring.
    
    Attributes
    ----------
    id : str
        Unique service identifier (e.g., "moderation", "sentry", "github").
    name : str
        Human-readable service name.
    description : str
        Service description and purpose.
    service_type : ServiceType
        Classification of the service.
    status : ServiceStatus
        Current operational status.
    enabled : bool
        Whether the service is currently enabled.
    version : str, optional
        Service version identifier.
    metadata : dict
        Additional service metadata (JSON).
    config_schema : dict, optional
        JSON schema for service configuration.
    health_check_endpoint : str, optional
        Endpoint or method name for health checks.
    created_at : datetime
        When the service was registered.
    updated_at : datetime
        Last update timestamp.
    last_health_check : datetime, optional
        Last health check timestamp.
    """
    
    id: str = Field(
        primary_key=True,
        description="Unique service identifier",
        examples=["moderation", "sentry", "github"],
    )
    
    name: str = Field(
        description="Human-readable service name",
        examples=["Moderation Service", "Sentry Integration"],
    )
    
    description: str = Field(
        default="",
        description="Service description and purpose",
    )
    
    service_type: ServiceType = Field(
        description="Service classification",
    )
    
    status: ServiceStatus = Field(
        default=ServiceStatus.UNKNOWN,
        description="Current operational status",
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether the service is currently enabled",
    )
    
    version: str | None = Field(
        default=None,
        description="Service version identifier",
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_type=JSON,
        description="Additional service metadata",
    )
    
    config_schema: dict[str, Any] | None = Field(
        default=None,
        sa_type=JSON,
        description="JSON schema for service configuration",
    )
    
    health_check_endpoint: str | None = Field(
        default=None,
        description="Method name or endpoint for health checks",
    )
    
    last_health_check: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Last health check timestamp",
    )
    
    # Inherited from BaseModel: created_at, updated_at
```

### Service Configuration Model

```python
# src/tux/database/models/service_registry.py (continued)

class ServiceConfiguration(BaseModel, table=True):
    """Service-specific configuration storage.
    
    Stores configuration values for services, separate from the main
    config system to allow dynamic updates without restart.
    
    Attributes
    ----------
    service_id : str
        Foreign key to ServiceRegistry.
    config_key : str
        Configuration key name.
    config_value : str
        Configuration value (JSON-encoded if complex).
    encrypted : bool
        Whether the value is encrypted.
    """
    
    __tablename__ = "service_configuration"
    
    id: int = Field(
        primary_key=True,
        sa_type=Integer,
        description="Primary key",
    )
    
    service_id: str = Field(
        foreign_key="service_registry.id",
        ondelete="CASCADE",
        description="Service identifier",
    )
    
    config_key: str = Field(
        description="Configuration key name",
    )
    
    config_value: str = Field(
        description="Configuration value (JSON-encoded if complex)",
    )
    
    encrypted: bool = Field(
        default=False,
        description="Whether the value is encrypted",
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
    
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
    )
    
    __table_args__ = (
        UniqueConstraint("service_id", "config_key", name="uq_service_config"),
        Index("idx_service_config_service", "service_id"),
    )
```

## Service Registry System

### Service Discovery

Services will be discovered through multiple mechanisms:

1. **Auto-discovery** - Scan service directories and detect services
2. **Manual registration** - Explicit service registration
3. **Plugin system** - Services registered by plugins

### Service Metadata Structure

```python
# src/tux/services/registry/metadata.py

@dataclass
class ServiceMetadata:
    """Service metadata structure."""
    
    id: str
    name: str
    description: str
    service_type: ServiceType
    version: str | None = None
    dependencies: list[str] = field(default_factory=list)
    health_check: str | None = None  # Method name or endpoint
    config_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Service Interface

```python
# src/tux/services/registry/base.py

class ServiceInterface(Protocol):
    """Protocol for services that can be managed by the dashboard."""
    
    async def health_check(self) -> ServiceStatus:
        """Check service health.
        
        Returns
        -------
        ServiceStatus
            Current service health status.
        """
        ...
    
    async def get_metadata(self) -> ServiceMetadata:
        """Get service metadata.
        
        Returns
        -------
        ServiceMetadata
            Service metadata information.
        """
        ...
    
    async def enable(self) -> None:
        """Enable the service."""
        ...
    
    async def disable(self) -> None:
        """Disable the service."""
        ...
    
    async def get_config(self) -> dict[str, Any]:
        """Get current service configuration.
        
        Returns
        -------
        dict[str, Any]
            Current configuration values.
        """
        ...
    
    async def update_config(self, config: dict[str, Any]) -> None:
        """Update service configuration.
        
        Parameters
        ----------
        config : dict[str, Any]
            Configuration updates to apply.
        """
        ...
```

## Implementation Structure

### Directory Structure

```
src/tux/
├── services/
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── base.py              # ServiceInterface protocol
│   │   ├── metadata.py          # ServiceMetadata dataclass
│   │   ├── discovery.py         # Service discovery logic
│   │   ├── manager.py           # ServiceRegistryManager
│   │   ├── health.py            # Health check system
│   │   └── config.py            # Configuration management
│   └── [existing services]
│
├── database/
│   ├── models/
│   │   └── service_registry.py   # Database models
│   └── controllers/
│       └── service_registry.py  # Database controller
│
├── modules/
│   └── admin/
│       └── dashboard.py         # Dashboard Discord commands
│
└── ui/
    └── dashboard/
        ├── views.py             # Discord UI components
        └── embeds.py            # Dashboard embeds
```

### Core Classes

#### ServiceRegistryManager

```python
# src/tux/services/registry/manager.py

class ServiceRegistryManager:
    """Manages service registration, discovery, and lifecycle.
    
    This class coordinates service discovery, registration, health monitoring,
    and configuration management for all services in the bot.
    """
    
    def __init__(self, bot: Tux) -> None:
        """Initialize the service registry manager.
        
        Parameters
        ----------
        bot : Tux
            The bot instance.
        """
        self.bot = bot
        self.db = bot.db
        self._services: dict[str, ServiceInterface] = {}
        self._metadata: dict[str, ServiceMetadata] = {}
    
    async def discover_services(self) -> list[ServiceMetadata]:
        """Discover all available services.
        
        Scans service directories and configuration to find all
        available services (internal and external).
        
        Returns
        -------
        list[ServiceMetadata]
            List of discovered service metadata.
        """
        ...
    
    async def register_service(
        self,
        service: ServiceInterface,
        metadata: ServiceMetadata,
    ) -> None:
        """Register a service with the registry.
        
        Parameters
        ----------
        service : ServiceInterface
            The service instance to register.
        metadata : ServiceMetadata
            Service metadata.
        """
        ...
    
    async def get_service(self, service_id: str) -> ServiceInterface | None:
        """Get a registered service by ID.
        
        Parameters
        ----------
        service_id : str
            Service identifier.
        
        Returns
        -------
        ServiceInterface | None
            Service instance if found, None otherwise.
        """
        ...
    
    async def list_services(
        self,
        service_type: ServiceType | None = None,
        enabled_only: bool = False,
    ) -> list[ServiceMetadata]:
        """List all registered services.
        
        Parameters
        ----------
        service_type : ServiceType | None
            Filter by service type.
        enabled_only : bool
            Only return enabled services.
        
        Returns
        -------
        list[ServiceMetadata]
            List of service metadata.
        """
        ...
    
    async def check_health(self, service_id: str) -> ServiceStatus:
        """Check health of a specific service.
        
        Parameters
        ----------
        service_id : str
            Service identifier.
        
        Returns
        -------
        ServiceStatus
            Current service health status.
        """
        ...
    
    async def check_all_health(self) -> dict[str, ServiceStatus]:
        """Check health of all services.
        
        Returns
        -------
        dict[str, ServiceStatus]
            Mapping of service IDs to their health status.
        """
        ...
```

## Dashboard Interface

### Discord Commands

```python
# src/tux/modules/admin/dashboard.py

class ServiceDashboard(BaseCog):
    """Discord commands for service management dashboard."""
    
    @commands.hybrid_group(name="services")
    async def services_group(self, ctx: commands.Context[Tux]) -> None:
        """Service management commands."""
        ...
    
    @services_group.command(name="list")
    async def list_services(
        self,
        ctx: commands.Context[Tux],
        service_type: str | None = None,
    ) -> None:
        """List all available services."""
        ...
    
    @services_group.command(name="status")
    async def service_status(
        self,
        ctx: commands.Context[Tux],
        service_id: str,
    ) -> None:
        """Get status of a specific service."""
        ...
    
    @services_group.command(name="enable")
    async def enable_service(
        self,
        ctx: commands.Context[Tux],
        service_id: str,
    ) -> None:
        """Enable a service."""
        ...
    
    @services_group.command(name="disable")
    async def disable_service(
        self,
        ctx: commands.Context[Tux],
        service_id: str,
    ) -> None:
        """Disable a service."""
        ...
    
    @services_group.command(name="health")
    async def check_health(
        self,
        ctx: commands.Context[Tux],
        service_id: str | None = None,
    ) -> None:
        """Check service health."""
        ...
    
    @services_group.command(name="config")
    async def service_config(
        self,
        ctx: commands.Context[Tux],
        service_id: str,
    ) -> None:
        """View service configuration."""
        ...
```

### Web Dashboard (Future)

For future web-based dashboard:

- **Framework**: FastAPI or similar async web framework
- **Frontend**: React/Vue with real-time updates
- **Authentication**: Discord OAuth2
- **Real-time**: WebSocket for live status updates

## Service Implementation Examples

### Internal Service Example

```python
# src/tux/services/moderation/__init__.py (modified)

class ModerationService(ServiceInterface):
    """Moderation service with dashboard integration."""
    
    async def health_check(self) -> ServiceStatus:
        """Check moderation service health."""
        try:
            # Verify database connection
            await self.bot.db.health_check()
            # Verify coordinator is initialized
            if self.coordinator is None:
                return ServiceStatus.ERROR
            return ServiceStatus.ACTIVE
        except Exception:
            return ServiceStatus.ERROR
    
    async def get_metadata(self) -> ServiceMetadata:
        """Get moderation service metadata."""
        return ServiceMetadata(
            id="moderation",
            name="Moderation Service",
            description="Handles moderation actions, cases, and communication",
            service_type=ServiceType.INTERNAL,
            version="1.0.0",
            dependencies=["database"],
            health_check="health_check",
        )
    
    async def enable(self) -> None:
        """Enable moderation service."""
        # Service is always enabled if loaded
        pass
    
    async def disable(self) -> None:
        """Disable moderation service."""
        # Would need to unload cogs/commands
        raise NotImplementedError("Service disabling not yet implemented")
    
    async def get_config(self) -> dict[str, Any]:
        """Get moderation service configuration."""
        return {
            "case_retention_days": 90,
            "auto_appeal_enabled": True,
        }
    
    async def update_config(self, config: dict[str, Any]) -> None:
        """Update moderation service configuration."""
        # Update configuration in database
        ...
```

### External Service Example

```python
# src/tux/services/sentry/__init__.py (modified)

class SentryService(ServiceInterface):
    """Sentry integration with dashboard support."""
    
    async def health_check(self) -> ServiceStatus:
        """Check Sentry integration health."""
        if not self.bot.sentry_manager.is_initialized:
            return ServiceStatus.INACTIVE
        try:
            # Check if Sentry client is responding
            # (Sentry doesn't have a direct health endpoint)
            return ServiceStatus.ACTIVE
        except Exception:
            return ServiceStatus.ERROR
    
    async def get_metadata(self) -> ServiceMetadata:
        """Get Sentry service metadata."""
        return ServiceMetadata(
            id="sentry",
            name="Sentry Integration",
            description="Error tracking and performance monitoring",
            service_type=ServiceType.EXTERNAL,
            version=sentry_sdk.__version__,
            dependencies=[],
            health_check="health_check",
            config_schema={
                "type": "object",
                "properties": {
                    "dsn": {"type": "string", "description": "Sentry DSN"},
                    "environment": {"type": "string", "description": "Environment name"},
                    "traces_sample_rate": {"type": "number", "description": "Trace sample rate"},
                },
                "required": ["dsn"],
            },
        )
    
    async def get_config(self) -> dict[str, Any]:
        """Get Sentry configuration."""
        return {
            "dsn": self.bot.sentry_manager.dsn or "",
            "environment": self.bot.sentry_manager.environment,
            "traces_sample_rate": self.bot.sentry_manager.traces_sample_rate,
        }
    
    async def update_config(self, config: dict[str, Any]) -> None:
        """Update Sentry configuration."""
        # Update environment variables and reinitialize
        # Note: Some services may require restart
        ...
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals:**
- Database models and migrations
- Basic service registry structure
- Service discovery mechanism

**Tasks:**
1. Create `ServiceRegistry` and `ServiceConfiguration` models
2. Create database migration
3. Implement `ServiceInterface` protocol
4. Create `ServiceMetadata` dataclass
5. Implement basic `ServiceRegistryManager`
6. Add service discovery for internal services

**Deliverables:**
- Database models
- Migration files
- Basic registry system
- Unit tests for models

### Phase 2: Core Functionality (Week 3-4)

**Goals:**
- Health checking system
- Configuration management
- Service enable/disable

**Tasks:**
1. Implement health check system
2. Create configuration management
3. Add service enable/disable functionality
4. Integrate with existing services
5. Add service registration on bot startup

**Deliverables:**
- Health monitoring system
- Configuration management
- Service lifecycle management
- Integration tests

### Phase 3: Dashboard Interface (Week 5-6)

**Goals:**
- Discord command interface
- Rich UI components
- Status reporting

**Tasks:**
1. Create Discord command module
2. Design and implement dashboard embeds
3. Add interactive views for service management
4. Implement status reporting
5. Add permission checks

**Deliverables:**
- Discord dashboard commands
- UI components
- User documentation

### Phase 4: External Services (Week 7-8)

**Goals:**
- External service integration
- Configuration schema support
- Dynamic configuration updates

**Tasks:**
1. Integrate external services (Sentry, GitHub, etc.)
2. Add configuration schema support
3. Implement dynamic configuration updates
4. Add validation for configuration changes
5. Handle service restart requirements

**Deliverables:**
- External service integrations
- Configuration management UI
- Validation system

### Phase 5: Advanced Features (Week 9-10)

**Goals:**
- Service dependencies
- Health monitoring automation
- Metrics and logging

**Tasks:**
1. Implement service dependency tracking
2. Add automated health monitoring
3. Create metrics collection
4. Add comprehensive logging
5. Performance optimization

**Deliverables:**
- Dependency system
- Automated monitoring
- Metrics dashboard
- Performance improvements

### Phase 6: Documentation & Testing (Week 11-12)

**Goals:**
- Complete documentation
- Comprehensive testing
- Migration guide

**Tasks:**
1. Write user documentation
2. Write developer documentation
3. Add integration tests
4. Create migration guide for existing services
5. Performance testing

**Deliverables:**
- Complete documentation
- Test suite
- Migration guide

## Extension Points

### Adding a New Service

To add a new service to the dashboard:

1. **Implement ServiceInterface**

```python
class MyNewService(ServiceInterface):
    async def health_check(self) -> ServiceStatus:
        # Implement health checking
        ...
    
    async def get_metadata(self) -> ServiceMetadata:
        # Return service metadata
        ...
    
    # Implement other required methods
    ...
```

2. **Register Service**

```python
# In service initialization
registry_manager = bot.service_registry
await registry_manager.register_service(
    service=my_service_instance,
    metadata=ServiceMetadata(
        id="my_service",
        name="My Service",
        description="Service description",
        service_type=ServiceType.INTERNAL,
    ),
)
```

3. **Auto-Discovery** (Optional)

Add service metadata to a discovery file:

```python
# src/tux/services/my_service/__init__.py
SERVICE_METADATA = ServiceMetadata(
    id="my_service",
    name="My Service",
    ...
)
```

### Service Discovery Mechanisms

1. **Directory Scanning** - Scan `src/tux/services/` for service modules
2. **Metadata Files** - Look for `SERVICE_METADATA` constants
3. **Decorator Registration** - Use decorators to mark services
4. **Plugin System** - Services registered by plugins

## Testing Strategy

### Unit Tests

- Service registry operations
- Health check logic
- Configuration management
- Service metadata handling

### Integration Tests

- Service discovery
- Database operations
- Service enable/disable
- Configuration updates

### E2E Tests

- Discord command execution
- Dashboard UI interactions
- Service lifecycle management

### Test Structure

```
tests/
├── services/
│   └── registry/
│       ├── test_manager.py
│       ├── test_discovery.py
│       ├── test_health.py
│       └── test_config.py
├── database/
│   └── test_service_registry.py
└── modules/
    └── admin/
        └── test_dashboard.py
```

## Security Considerations

1. **Permission Checks** - Only authorized users can manage services
2. **Configuration Encryption** - Sensitive config values encrypted
3. **Input Validation** - Validate all configuration inputs
4. **Audit Logging** - Log all service management actions
5. **Rate Limiting** - Prevent abuse of dashboard commands

## Performance Considerations

1. **Lazy Loading** - Load services on demand
2. **Caching** - Cache service metadata and status
3. **Async Operations** - All I/O operations async
4. **Batch Operations** - Batch health checks where possible
5. **Database Indexing** - Index service registry queries

## Migration Guide

### Migrating Existing Services

1. **Implement ServiceInterface** on existing services
2. **Add metadata** for each service
3. **Register services** during bot startup
4. **Update configuration** to use service registry
5. **Test thoroughly** before deployment

### Backward Compatibility

- Existing services continue to work without changes
- Dashboard is opt-in for services
- Configuration can be migrated gradually

## Future Enhancements

1. **Web Dashboard** - Browser-based management interface
2. **Service Metrics** - Detailed performance metrics
3. **Service Dependencies** - Visual dependency graphs
4. **Service Templates** - Pre-configured service setups
5. **Automated Testing** - Service health test automation
6. **Alerting System** - Notifications for service issues
7. **Service Marketplace** - Community-contributed services

## Success Criteria

1. ✅ All existing services discoverable and manageable
2. ✅ Health monitoring for all services
3. ✅ Dynamic configuration updates
4. ✅ Easy addition of new services
5. ✅ Comprehensive documentation
6. ✅ Full test coverage
7. ✅ Performance meets requirements
8. ✅ Security best practices followed

## Dependencies

### New Dependencies

- None required (uses existing stack)

### Optional Dependencies

- `jsonschema` - For configuration schema validation
- `cryptography` - For configuration encryption

## Timeline Summary

- **Phase 1-2**: Foundation and core (4 weeks)
- **Phase 3**: Dashboard interface (2 weeks)
- **Phase 4**: External services (2 weeks)
- **Phase 5**: Advanced features (2 weeks)
- **Phase 6**: Documentation and testing (2 weeks)

**Total**: ~12 weeks for complete implementation

## Getting Started

When ready to implement:

1. Review this plan with the team
2. Set up development branch
3. Start with Phase 1 (Foundation)
4. Follow implementation phases sequentially
5. Update this document as implementation progresses

## Questions & Considerations

### Open Questions

1. Should services be enabled/disabled at runtime or require restart?
2. How to handle service dependencies when disabling?
3. Should configuration changes require validation before applying?
4. How to handle services that require external API keys?
5. Should there be a service marketplace for community services?

### Design Decisions Needed

1. **Service Lifecycle**: Runtime enable/disable vs restart required
2. **Configuration Storage**: Database vs environment variables
3. **Health Check Frequency**: On-demand vs scheduled
4. **Dashboard Access**: Discord-only vs web interface
5. **Service Versioning**: How to handle service updates

## References

- [Service Pattern Documentation](../concepts/services/index.md)
- [Database Models Documentation](../concepts/database/models.md)
- [Module Development Guide](./creating-modules.md)
- [Configuration Management](../concepts/core/config.md)






