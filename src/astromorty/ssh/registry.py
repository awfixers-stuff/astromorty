"""
Service Registry and Monitoring System for SSH Administration.

This module provides a unified interface for discovering,
monitoring, and managing all bot services for the SSH admin interface.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Any

from loguru import logger

from astromorty.database.service import DatabaseService


class ServiceRegistryManager:
    """Manages service registration, discovery, and monitoring.

    This class coordinates service discovery, registration, health monitoring,
    and configuration management for all services in the bot, providing
    a unified interface for SSH administration.
    """

    def __init__(self, db_service: DatabaseService) -> None:
        """Initialize service registry manager.

        Parameters
        ----------
        db_service : DatabaseService
            Database service for data operations.
        """
        self.db_service = db_service
        self._services: dict[str, Any] = {}
        self._health_cache: dict[str, dict[str, Any]] = {}
        self._health_check_interval = 60  # seconds

    async def discover_services(self) -> dict[str, Any]:
        """Discover all available bot services.

        Returns
        -------
        dict[str, Any]
            Dictionary of discovered services with their metadata.
        """
        services = {}

        # Core bot services
        services.update(await self._discover_core_services())

        # Database service
        services.update(await self._discover_database_service())

        # External services
        services.update(await self._discover_external_services())

        # Cache discovered services
        self._services = services

        logger.info(f"Discovered {len(services)} services for registry")
        return services

    async def _discover_core_services(self) -> dict[str, Any]:
        """Discover core bot services."""
        return {
            "bot": {
                "name": "Bot Core",
                "description": "Main Discord bot functionality",
                "type": "internal",
                "status": "active",
                "health_endpoint": "bot_status",
                "config_schema": None,
                "dependencies": ["database", "discord_api"],
            },
            "database": {
                "name": "Database Service",
                "description": "PostgreSQL database with connection pooling",
                "type": "internal",
                "status": "active",
                "health_endpoint": "database_health",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "max_connections": {"type": "integer"},
                        "connection_timeout": {"type": "number"},
                    },
                },
                "dependencies": [],
            },
            "http_client": {
                "name": "HTTP Client Service",
                "description": "HTTP client for external API calls",
                "type": "internal",
                "status": "active",
                "health_endpoint": "http_health",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "number"},
                        "max_concurrent": {"type": "integer"},
                    },
                },
                "dependencies": [],
            },
        }

    async def _discover_database_service(self) -> dict[str, Any]:
        """Discover database service information."""
        # In a real implementation, this would check database connection
        # and get actual configuration. For now, return mock data.
        return {
            "name": "Database Service",
            "description": "PostgreSQL database management",
            "type": "internal",
            "status": "active",
            "health_endpoint": "database_health",
            "config_schema": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                    "database": {"type": "string"},
                    "pool_size": {"type": "integer"},
                },
            },
            "dependencies": [],
        }

    async def _discover_external_services(self) -> dict[str, Any]:
        """Discover external service integrations."""
        from astromorty.shared.config import CONFIG

        services = {}

        # Sentry integration
        if CONFIG.external_services.SENTRY_DSN:
            services["sentry"] = {
                "name": "Sentry Integration",
                "description": "Error tracking and performance monitoring",
                "type": "external",
                "status": "active" if CONFIG.sentry else "inactive",
                "health_endpoint": "sentry_health",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "dsn": {"type": "string"},
                        "environment": {"type": "string"},
                        "traces_sample_rate": {"type": "number"},
                    },
                },
                "dependencies": [],
            }

        # GitHub integration
        if CONFIG.external_services.GITHUB_PRIVATE_KEY:
            services["github"] = {
                "name": "GitHub Integration",
                "description": "GitHub API integration for development",
                "type": "external",
                "status": "active",
                "health_endpoint": "github_health",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "app_id": {"type": "string"},
                        "installation_id": {"type": "string"},
                        "private_key": {"type": "string"},
                    },
                },
                "dependencies": [],
            }

        # Mailcow integration
        if CONFIG.external_services.MAILCOW_TOKEN:
            services["mailcow"] = {
                "name": "Mailcow Integration",
                "description": "Email service integration",
                "type": "external",
                "status": "active",
                "health_endpoint": "mailcow_health",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"},
                        "api_url": {"type": "string"},
                    },
                },
                "dependencies": [],
            }

        return services

    async def get_service(self, service_id: str) -> dict[str, Any] | None:
        """Get a specific service by ID.

        Parameters
        ----------
        service_id : str
            Service identifier to retrieve.

        Returns
        -------
        dict[str, Any] | None
            Service metadata if found, None otherwise.
        """
        # Ensure services are discovered
        if not self._services:
            await self.discover_services()

        return self._services.get(service_id)

    async def get_all_services(self) -> dict[str, Any]:
        """Get all discovered services.

        Returns
        -------
        dict[str, Any]
            Dictionary of all services.
        """
        if not self._services:
            await self.discover_services()

        return self._services.copy()

    async def check_service_health(self, service_id: str) -> dict[str, Any]:
        """Check health of a specific service.

        Parameters
        ----------
        service_id : str
            Service identifier to check.

        Returns
        -------
        dict[str, Any]
            Health check result with status and details.
        """
        try:
            # Get service metadata
            service = await self.get_service(service_id)
            if not service:
                return {
                    "service_id": service_id,
                    "status": "not_found",
                    "health": "unknown",
                    "message": f"Service '{service_id}' not found",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            # Perform health check based on service type
            if service.get("type") == "internal":
                return await self._check_internal_service_health(service_id, service)
            elif service.get("type") == "external":
                return await self._check_external_service_health(service_id, service)
            else:
                return {
                    "service_id": service_id,
                    "status": "error",
                    "health": "unknown",
                    "message": f"Unknown service type: {service.get('type')}",
                    "timestamp": datetime.now(UTC).isoformat(),
                }

        except Exception as e:
            logger.error(f"Health check failed for service {service_id}: {e}")
            return {
                "service_id": service_id,
                "status": "error",
                "health": "unknown",
                "message": f"Health check error: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_internal_service_health(
        self, service_id: str, service: dict[str, Any]
    ) -> dict[str, Any]:
        """Check health of internal services."""
        health_endpoint = service.get("health_endpoint")

        if health_endpoint == "bot_status":
            return await self._check_bot_health()
        elif health_endpoint == "database_health":
            return await self._check_database_health()
        elif health_endpoint == "http_health":
            return await self._check_http_client_health()
        else:
            return {
                "service_id": service_id,
                "status": "unknown",
                "health": "unknown",
                "message": f"No health check implemented for endpoint: {health_endpoint}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_external_service_health(
        self, service_id: str, service: dict[str, Any]
    ) -> dict[str, Any]:
        """Check health of external services."""
        health_endpoint = service.get("health_endpoint")

        if health_endpoint == "sentry_health":
            return await self._check_sentry_health()
        elif health_endpoint == "github_health":
            return await self._check_github_health()
        elif health_endpoint == "mailcow_health":
            return await self._check_mailcow_health()
        else:
            return {
                "service_id": service_id,
                "status": "unknown",
                "health": "unknown",
                "message": f"No health check implemented for endpoint: {health_endpoint}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_bot_health(self) -> dict[str, Any]:
        """Check overall bot health."""
        try:
            # In a real implementation, this would check:
            # - Discord connection status
            # - Guild connectivity
            # - Module loading status
            # - Memory usage
            # - Error rates

            # For now, return mock data
            return {
                "service_id": "bot",
                "status": "active",
                "health": "good",
                "details": {
                    "discord_connected": True,
                    "guilds_connected": 12,
                    "modules_loaded": 45,
                    "memory_usage_mb": 256,
                    "uptime_hours": 48,
                    "error_rate_1h": 0.02,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "bot",
                "status": "error",
                "health": "bad",
                "message": f"Bot health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_database_health(self) -> dict[str, Any]:
        """Check database service health."""
        try:
            # In a real implementation, this would:
            # - Test database connection
            # - Check connection pool status
            # - Validate query performance
            # - Check for errors

            return {
                "service_id": "database",
                "status": "active",
                "health": "good",
                "details": {
                    "connected": True,
                    "active_connections": 8,
                    "max_connections": 10,
                    "queries_per_second": 45,
                    "avg_response_time_ms": 12,
                    "last_error": None,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "database",
                "status": "error",
                "health": "bad",
                "message": f"Database health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_http_client_health(self) -> dict[str, Any]:
        """Check HTTP client service health."""
        try:
            # In a real implementation, this would:
            # - Test HTTP client connectivity
            # - Check connection pool status
            # - Measure response times
            # - Check for errors

            return {
                "service_id": "http_client",
                "status": "active",
                "health": "good",
                "details": {
                    "connection_pool_status": "healthy",
                    "active_requests": 12,
                    "queued_requests": 3,
                    "avg_response_time_ms": 150,
                    "error_rate_5m": 0.1,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "http_client",
                "status": "error",
                "health": "bad",
                "message": f"HTTP client health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_sentry_health(self) -> dict[str, Any]:
        """Check Sentry integration health."""
        try:
            # In a real implementation, this would:
            # - Test Sentry client initialization
            # - Send test event
            # - Check for errors

            return {
                "service_id": "sentry",
                "status": "inactive",
                "health": "n/a",
                "details": {
                    "initialized": False,
                    "reason": "Sentry not configured or disabled",
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "sentry",
                "status": "error",
                "health": "bad",
                "message": f"Sentry health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_github_health(self) -> dict[str, Any]:
        """Check GitHub integration health."""
        try:
            # In a real implementation, this would:
            # - Test GitHub API authentication
            # - Check rate limits
            # - Test repository access

            return {
                "service_id": "github",
                "status": "active",
                "health": "good",
                "details": {
                    "api_accessible": True,
                    "rate_limit_remaining": 4980,
                    "last_successful_check": "2024-01-15T10:30:00Z",
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "github",
                "status": "error",
                "health": "bad",
                "message": f"GitHub health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _check_mailcow_health(self) -> dict[str, Any]:
        """Check Mailcow integration health."""
        try:
            # In a real implementation, this would:
            # - Test Mailcow API authentication
            # - Check email sending capabilities
            # - Test domain validation

            return {
                "service_id": "mailcow",
                "status": "error",
                "health": "bad",
                "details": {
                    "api_accessible": False,
                    "last_successful_check": "2024-01-14T15:30:00Z",
                    "error": "Connection timeout",
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "service_id": "mailcow",
                "status": "error",
                "health": "bad",
                "message": f"Mailcow health check failed: {e}",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def check_all_services_health(self) -> dict[str, dict[str, Any]]:
        """Check health of all services.

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary mapping service IDs to their health status.
        """
        services = await self.get_all_services()
        health_results = {}

        # Check each service health
        tasks = []
        for service_id in services.keys():
            task = asyncio.create_task(self.check_service_health(service_id))
            tasks.append(task)

        # Wait for all health checks to complete
        health_results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (service_id, result) in enumerate(
            zip(services.keys(), health_results_list)
        ):
            if isinstance(result, Exception):
                health_results[service_id] = {
                    "status": "error",
                    "health": "bad",
                    "message": f"Health check failed: {result}",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            else:
                health_results[service_id] = result

        return health_results

    def get_service_summary(self) -> dict[str, Any]:
        """Get summary of all services for dashboard display."""
        if not self._services:
            return {
                "total_services": 0,
                "active_services": 0,
                "inactive_services": 0,
                "services_with_errors": 0,
                "last_updated": datetime.now(UTC).isoformat(),
            }

        total = len(self._services)
        active = sum(
            1
            for service in self._services.values()
            if service.get("status") == "active"
        )
        inactive = sum(
            1
            for service in self._services.values()
            if service.get("status") == "inactive"
        )
        with_errors = sum(
            1 for service in self._services.values() if service.get("status") == "error"
        )

        return {
            "total_services": total,
            "active_services": active,
            "inactive_services": inactive,
            "services_with_errors": with_errors,
            "last_updated": datetime.now(UTC).isoformat(),
        }

    def __repr__(self) -> str:
        """Return string representation of service registry."""
        return f"ServiceRegistryManager(services={len(self._services)})"
