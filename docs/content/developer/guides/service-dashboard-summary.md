---
title: Service Dashboard - Quick Reference
description: Quick reference guide for the service dashboard implementation plan.
tags:
  - developer-guide
  - services
  - dashboard
  - quick-reference
---

# Service Dashboard - Quick Reference

## Overview

A comprehensive dashboard system to manage all bot services (internal and external) with extensibility for future additions.

## Key Components

### 1. Database Models
- `ServiceRegistry` - Main service catalog
- `ServiceConfiguration` - Service-specific config storage
- Located in: `src/tux/database/models/service_registry.py`

### 2. Service Registry System
- `ServiceRegistryManager` - Core management class
- `ServiceInterface` - Protocol for manageable services
- `ServiceMetadata` - Service information structure
- Located in: `src/tux/services/registry/`

### 3. Dashboard Interface
- Discord commands for service management
- Located in: `src/tux/modules/admin/dashboard.py`

## Quick Start

### Adding a New Service

1. Implement `ServiceInterface`:
```python
class MyService(ServiceInterface):
    async def health_check(self) -> ServiceStatus:
        return ServiceStatus.ACTIVE
    
    async def get_metadata(self) -> ServiceMetadata:
        return ServiceMetadata(
            id="my_service",
            name="My Service",
            description="Service description",
            service_type=ServiceType.INTERNAL,
        )
    # ... other methods
```

2. Register during bot startup:
```python
await bot.service_registry.register_service(
    service=my_service,
    metadata=service_metadata,
)
```

## Implementation Phases

1. **Phase 1-2** (4 weeks): Foundation & Core
   - Database models
   - Service registry
   - Discovery system

2. **Phase 3** (2 weeks): Dashboard Interface
   - Discord commands
   - UI components

3. **Phase 4** (2 weeks): External Services
   - Integration with external APIs
   - Configuration management

4. **Phase 5** (2 weeks): Advanced Features
   - Dependencies
   - Automated monitoring

5. **Phase 6** (2 weeks): Documentation & Testing
   - Complete docs
   - Test suite

**Total**: ~12 weeks

## Service Types

- `INTERNAL` - Built-in bot services
- `EXTERNAL` - Third-party integrations
- `WRAPPER` - API wrapper services

## Service Status

- `ACTIVE` - Service is operational
- `INACTIVE` - Service is disabled
- `ERROR` - Service has errors
- `UNKNOWN` - Status not determined

## Commands (Planned)

- `/services list` - List all services
- `/services status <id>` - Get service status
- `/services enable <id>` - Enable a service
- `/services disable <id>` - Disable a service
- `/services health [id]` - Check health
- `/services config <id>` - View configuration

## Files to Create

```
src/tux/
├── services/registry/
│   ├── __init__.py
│   ├── base.py
│   ├── metadata.py
│   ├── discovery.py
│   ├── manager.py
│   ├── health.py
│   └── config.py
├── database/models/service_registry.py
├── database/controllers/service_registry.py
└── modules/admin/dashboard.py
```

## See Also

- [Full Implementation Plan](./service-dashboard-plan.md) - Detailed plan and architecture
- [Service Concepts](../concepts/services/index.md) - Service patterns
- [Database Models](../concepts/database/models.md) - Database patterns





