# HTTP Endpoint Migration Implementation Plan

## Executive Summary

This document outlines the implementation plan for migrating Astromorty from a pure WebSocket Gateway connection to HTTP-based endpoints for receiving Discord events and interactions. This migration enables serverless deployment, better scalability, and reduced infrastructure overhead.

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Discord HTTP Alternatives](#discord-http-alternatives)
3. [Migration Strategy](#migration-strategy)
4. [Implementation Phases](#implementation-phases)
5. [Technical Implementation](#technical-implementation)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Considerations](#deployment-considerations)
8. [Rollback Plan](#rollback-plan)
9. [Limitations & Trade-offs](#limitations--trade-offs)
10. [Timeline & Resources](#timeline--resources)

---

## Current Architecture Analysis

### Current State

**Connection Method:**

- Uses `discord.py` library with WebSocket Gateway connection
- Bot connects via `wss://gateway.discord.gg/` (Gateway v10)
- Maintains persistent WebSocket connection for real-time events
- Entry point: `src/astromorty/core/app.py` → `AstromortyApp.start()`
- Bot class: `src/astromorty/core/bot.py` → `Astromorty(commands.Bot)`

**Key Components:**

- **Gateway Connection**: `bot.login()` → `bot.connect(reconnect=True)`
- **Event Handling**: Discord Gateway events (MESSAGE_CREATE, INTERACTION_CREATE, etc.)
- **Command Processing**: Hybrid commands (slash + traditional prefix commands)
- **Existing HTTP Server**: FastAPI app at `src/astromorty/web/app.py` (currently for role connections)

**Dependencies:**

- `discord.py` (local fork in `external/discord.py/`)
- `fastapi` + `uvicorn` (already in use)
- `httpx` (already in use)
- `pynacl` (for signature verification)

### Current Flow

```text
1. Bot starts → AstromortyApp.run()
2. Bot initializes → Astromorty.__init__()
3. Bot logs in → bot.login(BOT_TOKEN)
4. Bot connects → bot.connect() [WebSocket]
5. Gateway sends events → Event handlers process
6. Commands execute → Cog command handlers
7. Bot responds → Via discord.py HTTP API
```

---

## Discord HTTP Alternatives

Discord provides two HTTP-based alternatives to the WebSocket Gateway:

### 1. Interactions Endpoint URL

**Purpose:** Receive interactions (slash commands, buttons, modals, select menus) via HTTP POST requests instead of Gateway events.

**Requirements:**

- Public HTTPS endpoint
- Signature verification (`X-Signature-Ed25519`, `X-Signature-Timestamp`)
- PING/PONG handling for endpoint validation
- 3-second response time for initial interaction response

**Events Received:**

- `INTERACTION_CREATE` (slash commands, buttons, modals, select menus)
- **NOT** traditional message events (MESSAGE_CREATE, etc.)

**Limitations:**

- Only interactions, not all Gateway events
- Cannot receive message-based prefix commands via HTTP
- Requires separate mechanism for message events

### 2. Webhook Events URL

**Purpose:** Receive Gateway events via HTTP POST requests instead of WebSocket.

**Requirements:**

- Public HTTPS endpoint
- Signature verification (`X-Signature-Ed25519`, `X-Signature-Timestamp`)
- PING event handling (type: 0, respond with 204)
- Event filtering via subscription configuration

**Events Received:**

- All Gateway events (MESSAGE_CREATE, GUILD_MEMBER_ADD, etc.)
- Configurable event subscriptions
- Full Gateway event payloads

**Limitations:**

- Requires event subscription configuration
- Higher latency than WebSocket (HTTP request overhead
- No bidirectional communication (cannot send events via HTTP)

### 3. Hybrid Approach (Recommended)

**Strategy:** Use both HTTP endpoints while maintaining WebSocket for specific features.

**Interactions Endpoint:**

- Handle all interactions (slash commands, buttons, modals)
- Reduces Gateway load
- Better for serverless deployments

**WebSocket Gateway:**

- Maintain for message events (prefix commands)
- Maintain for real-time features (presence, voice, etc.)
- Use for features requiring bidirectional communication

---

## Migration Strategy

### Recommended Approach: Phased Hybrid Migration

**Phase 1:** Add Interactions Endpoint (HTTP) alongside WebSocket

- Migrate slash commands to HTTP
- Keep prefix commands on WebSocket
- Zero downtime migration

**Phase 2:** Add Webhook Events URL (HTTP) for non-critical events

- Migrate read-only events (GUILD_MEMBER_ADD, MESSAGE_CREATE for logging)
- Keep real-time features on WebSocket

**Phase 3:** Full HTTP Migration (Optional)

- Migrate all events to HTTP
- Remove WebSocket dependency
- Requires rearchitecting real-time features

### Alternative: Full HTTP Migration

**Strategy:** Complete migration to HTTP endpoints only.

**Pros:**

- Serverless-friendly
- No persistent connections
- Better scalability
- Reduced infrastructure costs

**Cons:**

- Lose real-time bidirectional features
- Higher latency for some operations
- More complex event handling
- Cannot use features requiring Gateway (voice, presence updates)

---

## Implementation Phases

### Phase 1: Interactions Endpoint (HTTP)

**Goal:** Migrate slash commands and interactions to HTTP endpoint.

**Steps:**

1. **Create Interactions Endpoint Handler**
   - File: `src/astromorty/web/interactions.py`
   - Handle POST requests to `/interactions`
   - Verify signatures using `pynacl`
   - Handle PING requests (type: 1)
   - Route interactions to command handlers

2. **Update FastAPI App**
   - Add interactions route to `src/astromorty/web/app.py`
   - Configure middleware for signature verification
   - Add request/response models

3. **Create Interaction Router**
   - File: `src/astromorty/core/interaction_router.py`
   - Route interactions to appropriate command handlers
   - Convert HTTP interaction format to discord.py format
   - Handle interaction responses

4. **Update Bot Configuration**
   - Disable Gateway interactions (keep WebSocket for other events)
   - Configure Interactions Endpoint URL in Discord Developer Portal
   - Update command registration

5. **Testing**
   - Unit tests for signature verification
   - Integration tests for interaction handling
   - End-to-end tests with Discord

**Estimated Time:** 2-3 weeks

---

### Phase 2: Webhook Events URL (HTTP)

**Goal:** Migrate Gateway events to HTTP webhook endpoint.

**Steps:**

1. **Create Webhook Events Handler**
   - File: `src/astromorty/web/webhook_events.py`
   - Handle POST requests to `/webhook-events`
   - Verify signatures
   - Handle PING events (type: 0)
   - Route events to appropriate handlers

2. **Event Subscription Configuration**
   - Configure which events to receive via HTTP
   - Update Discord Developer Portal settings
   - Create event routing system

3. **Event Router**
   - File: `src/astromorty/core/event_router.py`
   - Route HTTP events to existing event handlers
   - Convert HTTP event format to discord.py format
   - Handle event processing asynchronously

4. **Update Event Handlers**
   - Modify event handlers to work with HTTP events
   - Ensure compatibility with both WebSocket and HTTP
   - Add event deduplication (if receiving from both sources)

5. **Testing**
   - Test event reception and processing
   - Test event deduplication
   - Performance testing

**Estimated Time:** 3-4 weeks

---

### Phase 3: Full HTTP Migration (Optional)

**Goal:** Remove WebSocket dependency entirely.

**Steps:**

1. **Migrate Remaining Features**
   - Voice connections (if used)
   - Presence updates
   - Real-time features

2. **Remove WebSocket Code**
   - Remove `bot.connect()` calls
   - Remove Gateway event handlers
   - Update bot initialization

3. **Update Dependencies**
   - Remove discord.py Gateway dependencies (if possible)
   - Keep discord.py HTTP API client
   - Update imports and references

4. **Testing**
   - Full system testing
   - Performance validation
   - Load testing

**Estimated Time:** 2-3 weeks

---

## Technical Implementation

### 1. Signature Verification

**File:** `src/astromorty/web/security.py`

```python
"""Discord signature verification for HTTP endpoints."""

import nacl.signing
from fastapi import Header, HTTPException, Request

from astromorty.shared.config import CONFIG


def verify_signature(
    request_body: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    """
    Verify Discord request signature.

    Parameters
    ----------
    request_body : bytes
        Raw request body
    signature : str
        X-Signature-Ed25519 header value
    timestamp : str
        X-Signature-Timestamp header value

    Returns
    -------
    bool
        True if signature is valid
    """
    public_key = nacl.signing.VerifyKey(
        bytes.fromhex(CONFIG.DISCORD_PUBLIC_KEY)
    )
    try:
        message = f"{timestamp}{request_body.decode()}".encode()
        public_key.verify(message, bytes.fromhex(signature))
        return True
    except Exception:
        return False


async def verify_discord_request(request: Request) -> None:
    """
    Middleware to verify Discord request signatures.

    Raises
    ------
    HTTPException
        If signature verification fails
    """
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature headers")

    body = await request.body()
    if not verify_signature(body, signature, timestamp):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

### 2. Interactions Endpoint

**File:** `src/astromorty/web/interactions.py`

```python
"""Discord Interactions HTTP endpoint handler."""

from fastapi import APIRouter, HTTPException, Request, Response
from loguru import logger

from astromorty.core.interaction_router import InteractionRouter
from astromorty.web.security import verify_discord_request

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("")
async def handle_interaction(request: Request) -> Response:
    """
    Handle Discord interaction HTTP requests.

    Parameters
    ----------
    request : Request
        FastAPI request object

    Returns
    -------
    Response
        Interaction response
    """
    # Verify signature
    await verify_discord_request(request)

    # Parse interaction payload
    payload = await request.json()

    # Handle PING
    if payload.get("type") == 1:
        return Response(
            content='{"type": 1}',
            media_type="application/json",
            status_code=200,
        )

    # Route interaction to handler
    try:
        router = InteractionRouter()
        response = await router.handle_interaction(payload)
        return Response(
            content=response.model_dump_json(),
            media_type="application/json",
            status_code=200,
        )
    except Exception as e:
        logger.exception("Error handling interaction")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Interaction Router

**File:** `src/astromorty/core/interaction_router.py`

```python
"""Route Discord interactions to command handlers."""

from typing import Any

from loguru import logger

from astromorty.core.bot import Astromorty


class InteractionRouter:
    """Route HTTP interactions to discord.py command handlers."""

    def __init__(self, bot: Astromorty | None = None) -> None:
        """
        Initialize interaction router.

        Parameters
        ----------
        bot : Astromorty | None
            Bot instance (injected via dependency)
        """
        self.bot = bot

    async def handle_interaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Handle interaction payload and route to handler.

        Parameters
        ----------
        payload : dict[str, Any]
            Interaction payload from Discord

        Returns
        -------
        dict[str, Any]
            Interaction response
        """
        interaction_type = payload.get("type")

        if interaction_type == 2:  # APPLICATION_COMMAND
            return await self._handle_slash_command(payload)
        elif interaction_type == 3:  # MESSAGE_COMPONENT
            return await self._handle_component(payload)
        elif interaction_type == 5:  # MODAL_SUBMIT
            return await self._handle_modal(payload)
        else:
            logger.warning(f"Unknown interaction type: {interaction_type}")
            return {"type": 4, "data": {"content": "Unknown interaction type"}}

    async def _handle_slash_command(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle slash command interaction."""
        # Convert HTTP payload to discord.py Interaction format
        # Route to appropriate command handler
        # Return response
        pass

    async def _handle_component(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle button/select menu interaction."""
        pass

    async def _handle_modal(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle modal submission."""
        pass
```

### 4. Update FastAPI App

**File:** `src/astromorty/web/app.py`

```python
# Add interactions router
from astromorty.web.interactions import router as interactions_router

app.include_router(interactions_router)
```

### 5. Configuration Updates

**File:** `src/astromorty/shared/config.py`

```python
# Add Discord public key for signature verification
DISCORD_PUBLIC_KEY: str = Field(
    ...,
    description="Discord application public key for signature verification",
)

# Add interactions endpoint URL
INTERACTIONS_ENDPOINT_URL: str | None = Field(
    None,
    description="Public URL for Discord interactions endpoint",
)
```

### 6. Update Bot Initialization

**File:** `src/astromorty/core/app.py`

```python
async def start(self) -> int:
    """Start bot with optional HTTP endpoints."""
    # ... existing setup ...

    # Start HTTP server if configured
    if CONFIG.INTERACTIONS_ENDPOINT_URL:
        # Start FastAPI server in background
        import uvicorn
        server_task = asyncio.create_task(
            uvicorn.run(
                "astromorty.web.app:app",
                host="0.0.0.0",
                port=8000,
                log_level="info",
            )
        )

    # Connect to Gateway (if not fully migrated)
    if not CONFIG.HTTP_ONLY_MODE:
        await self.bot.login(CONFIG.BOT_TOKEN)
        await self.bot.connect(reconnect=True)
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/web/test_security.py`

```python
"""Test signature verification."""

def test_verify_signature_valid():
    """Test valid signature verification."""
    pass

def test_verify_signature_invalid():
    """Test invalid signature rejection."""
    pass

def test_verify_signature_missing_headers():
    """Test missing header handling."""
    pass
```

**File:** `tests/web/test_interactions.py`

```python
"""Test interaction handling."""

def test_handle_ping():
    """Test PING interaction handling."""
    pass

def test_handle_slash_command():
    """Test slash command routing."""
    pass

def test_handle_component():
    """Test component interaction routing."""
    pass
```

### Integration Tests

**File:** `tests/integration/test_http_endpoints.py`

```python
"""Integration tests for HTTP endpoints."""

async def test_interactions_endpoint_ping():
    """Test interactions endpoint PING handling."""
    pass

async def test_interactions_endpoint_slash_command():
    """Test slash command via HTTP."""
    pass

async def test_webhook_events_endpoint():
    """Test webhook events reception."""
    pass
```

### End-to-End Tests

- Test with actual Discord bot
- Verify signature validation works
- Test interaction responses
- Test event processing
- Performance testing under load

---

## Deployment Considerations

### Infrastructure Requirements

1. **Public HTTPS Endpoint**
   - Required for Discord to send requests
   - Options:
     - **Cloudflare Worker** (recommended for serverless): `src/worker/` - Deploy separately
     - Reverse proxy (nginx, Caddy) for self-hosted bot
     - Cloud provider (AWS, GCP, Azure) for traditional deployment
   - SSL certificate (Let's Encrypt recommended for self-hosted)

2. **Endpoint URLs**
   - Interactions Endpoint: `https://your-domain.com/interactions` or `https://your-worker.workers.dev`
   - Webhook Events: `https://your-domain.com/webhook-events`

3. **Configuration**
   - Set in Discord Developer Portal
   - Update application settings
   - Test endpoint validation

### Cloudflare Worker Deployment (Recommended)

The project includes a Cloudflare Worker configuration in `src/worker/` that can be deployed separately:

**Benefits:**

- Serverless deployment (no infrastructure management)
- Global edge network (low latency)
- Free tier available
- Automatic scaling
- Separate from main bot deployment

**Setup:**

1. Configure `src/worker/wrangler.toml`
2. Set secrets: `wrangler secret put DISCORD_PUBLIC_KEY`
3. Deploy: `cd src/worker && pnpm deploy`
4. Configure Interactions Endpoint URL in Discord Developer Portal

**Architecture:**

- Worker verifies signatures and forwards to bot backend API
- Or handles interactions directly (limited functionality)
- See `src/worker/README.md` for details

### Environment Variables

```bash
# Discord configuration
DISCORD_PUBLIC_KEY=your_public_key_here
INTERACTIONS_ENDPOINT_URL=https://your-domain.com/interactions
WEBHOOK_EVENTS_URL=https://your-domain.com/webhook-events

# HTTP server configuration
HTTP_SERVER_HOST=0.0.0.0
HTTP_SERVER_PORT=8000

# Migration mode
HTTP_ONLY_MODE=false  # Set to true for full HTTP migration
```

### Docker Updates

**File:** `compose.yaml` or `Dockerfile`

- Expose HTTP server port (8000)
- Configure reverse proxy
- Update health checks

### Monitoring

- Add metrics for HTTP endpoint requests
- Monitor response times
- Track signature verification failures
- Alert on endpoint downtime

---

## Rollback Plan

### Phase 1 Rollback

1. **Disable Interactions Endpoint in Discord Portal**
   - Remove Interactions Endpoint URL
   - Re-enable Gateway interactions

2. **Revert Code Changes**
   - Remove interactions router
   - Remove HTTP endpoint handlers
   - Restore Gateway interaction handling

3. **Redeploy**
   - Deploy previous version
   - Verify Gateway connection restored

### Phase 2 Rollback

1. **Disable Webhook Events URL**
   - Remove from Discord Portal
   - Re-enable Gateway events

2. **Revert Code Changes**
   - Remove webhook events handler
   - Restore Gateway event handling

3. **Redeploy**
   - Deploy previous version
   - Verify all events via Gateway

### Emergency Rollback

- Feature flags for HTTP/WebSocket mode
- Quick configuration change
- No code deployment required

---

## Limitations & Trade-offs

### Limitations

1. **Latency**
   - HTTP requests have higher latency than WebSocket
   - No persistent connection overhead
   - Network round-trip for each event

2. **Real-time Features**
   - Voice connections require WebSocket
   - Presence updates require Gateway
   - Some features may not work with HTTP-only

3. **Event Ordering**
   - HTTP events may arrive out of order
   - Requires event deduplication
   - May need event queuing system

4. **Rate Limiting**
   - Discord rate limits apply to HTTP endpoints
   - Different limits than Gateway
   - Need to handle 429 responses

5. **Bidirectional Communication**
   - Cannot send events via HTTP (only receive)
   - Still use HTTP API for responses
   - Gateway required for some operations

### Trade-offs

**Pros:**

- ✅ Serverless-friendly deployment
- ✅ Better scalability
- ✅ Reduced infrastructure costs
- ✅ No persistent connection management
- ✅ Easier horizontal scaling

**Cons:**

- ❌ Higher latency for some operations
- ❌ More complex event handling
- ❌ Cannot use all Discord features
- ❌ Requires public HTTPS endpoint
- ❌ More complex error handling

---

## Timeline & Resources

### Phase 1: Interactions Endpoint

**Duration:** 2-3 weeks

**Tasks:**

- Week 1: Implementation (signature verification, endpoint handler, router)
- Week 2: Testing and integration
- Week 3: Deployment and monitoring

**Resources:**

- 1-2 developers
- Testing environment
- Discord Developer Portal access

### Phase 2: Webhook Events

**Duration:** 3-4 weeks

**Tasks:**

- Week 1-2: Implementation (event handler, router, subscription config)
- Week 2-3: Testing and integration
- Week 4: Deployment and monitoring

**Resources:**

- 1-2 developers
- Testing environment
- Load testing tools

### Phase 3: Full Migration (Optional)

**Duration:** 2-3 weeks

**Tasks:**

- Week 1: Migrate remaining features
- Week 2: Remove WebSocket code
- Week 3: Testing and deployment

**Resources:**

- 1-2 developers
- Full system testing

### Total Timeline

- **Minimum (Phases 1-2):** 5-7 weeks
- **Full Migration (All Phases):** 7-10 weeks

---

## Next Steps

1. **Review and Approve Plan**
   - Stakeholder review
   - Technical review
   - Resource allocation

2. **Set Up Development Environment**
   - Create feature branch
   - Set up testing environment
   - Configure Discord Developer Portal

3. **Begin Phase 1 Implementation**
   - Start with signature verification
   - Implement interactions endpoint
   - Test with Discord

4. **Iterate and Deploy**
   - Continuous testing
   - Incremental deployment
   - Monitor and adjust

---

## References

- [Discord Interactions API](https://discord.com/developers/docs/interactions/overview)
- [Discord Webhook Events](https://discord.com/developers/docs/events/webhook-events)
- [Discord Signature Verification](https://discord.com/developers/docs/interactions/receiving-and-responding#security-and-authorization)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyNaCl Documentation](https://pynacl.readthedocs.io/)

---

## Appendix

### A. Discord Public Key Extraction

The Discord public key is available in the Developer Portal:

1. Go to <https://discord.com/developers/applications>
2. Select your application
3. Navigate to "General Information"
4. Copy "Public Key" (Ed25519 format)

### B. Endpoint Validation

Discord will send a PING request when you add an endpoint:

- Interactions: `{"type": 1}` → Respond with `{"type": 1}`
- Webhook Events: `{"type": 0}` → Respond with `204 No Content`

### C. Event Subscription Configuration

Configure which events to receive via Webhook Events URL:

- Go to Developer Portal → Your App → Webhook Events
- Select events to subscribe to
- Save configuration

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-27  
**Author:** AI Assistant  
**Status:** Draft - Pending Review
