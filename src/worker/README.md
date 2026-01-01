# Astromorty Discord Interactions Cloudflare Worker

This Cloudflare Worker handles Discord HTTP interactions (slash commands, buttons, modals) received via the Interactions Endpoint URL. It can be deployed separately from the main bot and either forwards interactions to the bot's backend API or handles them directly.

## Features

- ✅ Discord signature verification (Ed25519)
- ✅ PING/PONG handling for endpoint validation
- ✅ Forward interactions to bot backend API
- ✅ Direct interaction handling (fallback mode)
- ✅ Support for all interaction types (commands, components, modals, autocomplete)

## Setup

### Prerequisites

- Node.js 20+ and pnpm
- Cloudflare account with Workers enabled
- Wrangler CLI installed: `npm install -g wrangler`

### Installation

```bash
cd src/worker
pnpm install
```

### Configuration

1. **Set Cloudflare secrets:**

```bash
# Required: Discord application public key
wrangler secret put DISCORD_PUBLIC_KEY

# Optional: Bot backend API URL (if forwarding interactions)
wrangler secret put BOT_API_URL
```

2. **Update `wrangler.toml`:**

- Set your Cloudflare account ID
- Configure custom domain routes if needed
- Adjust environment settings

### Development

```bash
# Start local development server
pnpm dev

# Or from repo root
wrangler dev --config src/worker/wrangler.toml
```

### Deployment

```bash
# Deploy to production
pnpm deploy:production

# Deploy to preview environment
pnpm deploy:preview

# Or from repo root
wrangler deploy --config src/worker/wrangler.toml
```

## Architecture

### Forwarding Mode (Recommended)

When `BOT_API_URL` is configured, the worker forwards all interactions to the bot's backend API:

```
Discord → Worker → Bot Backend API → Response
```

**Benefits:**
- Full command functionality
- Access to bot's database and services
- Centralized command handling

### Direct Mode (Fallback)

When `BOT_API_URL` is not configured, the worker handles interactions directly:

```
Discord → Worker → Response
```

**Limitations:**
- Only returns deferred responses
- No command execution
- No database access
- Limited functionality

## Configuration Options

### Environment Variables

- **`DISCORD_PUBLIC_KEY`** (required): Discord application public key (Ed25519 hex)
- **`BOT_API_URL`** (optional): URL to bot's backend API endpoint (e.g., `https://api.your-domain.com`)

### Wrangler Configuration

See `wrangler.toml` for:
- Worker name and compatibility settings
- Environment-specific configurations
- KV namespace bindings (optional)
- Durable Objects (optional)

## Discord Developer Portal Setup

1. Go to https://discord.com/developers/applications
2. Select your application
3. Navigate to "General Information"
4. Scroll to "Interactions Endpoint URL"
5. Enter your worker URL: `https://astromorty-interactions.<your-subdomain>.workers.dev`
6. Discord will send a PING request to validate
7. If validation succeeds, the endpoint is active

## Testing

### Local Testing

```bash
# Start worker locally
pnpm dev

# Test PING request
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"type": 1}'
```

### Production Testing

1. Deploy the worker
2. Configure Interactions Endpoint URL in Discord Developer Portal
3. Test a slash command in Discord
4. Check worker logs: `wrangler tail`

## Monitoring

- **Logs**: `wrangler tail` or Cloudflare Dashboard
- **Metrics**: Available in Cloudflare Dashboard
- **Errors**: Check worker logs and error responses

## Troubleshooting

### Signature Verification Fails

- Verify `DISCORD_PUBLIC_KEY` is set correctly
- Check that the public key matches your Discord application
- Ensure signature headers are being forwarded correctly

### Backend Connection Errors

- Verify `BOT_API_URL` is correct and accessible
- Check backend API is running and accepting requests
- Ensure backend endpoint is `/interactions`

### Interaction Not Responding

- Check worker logs for errors
- Verify interaction type is supported
- Ensure response format matches Discord's requirements

## Related Documentation

- [HTTP Endpoint Migration Plan](../../docs/http-endpoint-migration-plan.md)
- [Implementation Status](../../docs/http-endpoint-implementation-status.md)
- [Discord Interactions API](https://discord.com/developers/docs/interactions/overview)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)

