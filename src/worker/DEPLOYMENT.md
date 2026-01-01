# Cloudflare Worker Deployment Guide

This guide covers deploying the Astromorty Discord Interactions Cloudflare Worker.

## Prerequisites

1. **Cloudflare Account**
   - Sign up at https://dash.cloudflare.com/
   - Enable Workers (free tier available)

2. **Wrangler CLI**
   ```bash
   npm install -g wrangler
   # Or
   pnpm add -g wrangler
   ```

3. **Authentication**
   ```bash
   wrangler login
   ```

## Initial Setup

### 1. Install Dependencies

```bash
cd src/worker
pnpm install
```

### 2. Configure Wrangler

Update `wrangler.toml`:
- Set your Cloudflare `account_id` (found in Cloudflare Dashboard)

### 3. Set Secrets

```bash
# Required: Discord application public key
wrangler secret put DISCORD_PUBLIC_KEY
# Enter your public key when prompted

# Optional: Bot backend API URL (if forwarding interactions)
wrangler secret put BOT_API_URL
# Enter your backend URL, e.g., https://api.your-domain.com
```

**Getting Discord Public Key:**
1. Go to https://discord.com/developers/applications
2. Select your application
3. Navigate to "General Information"
4. Copy "Public Key" (Ed25519 format)

## Development

### Local Development

```bash
# Start local development server
pnpm dev

# Or with specific port
wrangler dev --port 8787
```

The worker will be available at `http://localhost:8787`

### Testing Locally

```bash
# Test PING request
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"type": 1}'

# Should return: {"type":1}
```

## Deployment

### Production Deployment

```bash
# Deploy to production
pnpm deploy:production

# Or manually
wrangler deploy --env production
```

After deployment, your worker will be available at:
`https://astromorty-interactions.<your-subdomain>.workers.dev`

### Preview Deployment

```bash
# Deploy to preview environment
pnpm deploy:preview

# Or manually
wrangler deploy --env preview
```

### Custom Domain (Optional)

1. Add domain in Cloudflare Dashboard
2. Update `wrangler.toml`:
   ```toml
   [env.production]
   routes = [
     { pattern = "interactions.your-domain.com", custom_domain = true }
   ]
   ```
3. Redeploy

## Discord Developer Portal Configuration

1. Go to https://discord.com/developers/applications
2. Select your application
3. Navigate to "General Information"
4. Scroll to "Interactions Endpoint URL"
5. Enter your worker URL:
   - Production: `https://astromorty-interactions.<subdomain>.workers.dev`
   - Or custom domain: `https://interactions.your-domain.com`
6. Click "Save Changes"
7. Discord will send a PING request to validate
8. If validation succeeds, endpoint is active

## Monitoring

### View Logs

```bash
# Tail worker logs in real-time
wrangler tail

# Or for specific environment
wrangler tail --env production
```

### Cloudflare Dashboard

- **Workers & Pages** → Select your worker → View logs, metrics, errors
- **Analytics**: Request count, error rate, response times
- **Logs**: Detailed request/response logs

## Troubleshooting

### Signature Verification Fails

**Symptoms:**
- Discord shows "Invalid signature" error
- Worker returns 401

**Solutions:**
1. Verify `DISCORD_PUBLIC_KEY` is set correctly:
   ```bash
   wrangler secret list
   ```
2. Ensure public key matches Discord application
3. Check signature headers are being forwarded (if using backend)

### Backend Connection Errors

**Symptoms:**
- Worker returns "Error connecting to bot backend"
- Backend not receiving requests

**Solutions:**
1. Verify `BOT_API_URL` is set:
   ```bash
   wrangler secret list
   ```
2. Check backend is running and accessible
3. Verify backend endpoint is `/interactions`
4. Test backend directly:
   ```bash
   curl -X POST https://your-backend.com/interactions \
     -H "Content-Type: application/json" \
     -d '{"type": 1}'
   ```

### Worker Not Responding

**Symptoms:**
- Discord shows interaction timeout
- No response from worker

**Solutions:**
1. Check worker logs: `wrangler tail`
2. Verify worker is deployed: Check Cloudflare Dashboard
3. Test worker directly:
   ```bash
   curl -X POST https://astromorty-interactions.<subdomain>.workers.dev \
     -H "Content-Type: application/json" \
     -d '{"type": 1}'
   ```
4. Check worker status in Cloudflare Dashboard

## Environment-Specific Configuration

### Production

- Use production secrets
- Custom domain (optional)
- Full observability enabled

### Preview

- Use preview secrets
- Workers.dev subdomain
- Testing and staging

## Updating Secrets

```bash
# Update existing secret
wrangler secret put DISCORD_PUBLIC_KEY

# Delete secret (if needed)
wrangler secret delete DISCORD_PUBLIC_KEY
```

## Rollback

If something goes wrong:

1. **Revert to previous version:**
   ```bash
   wrangler versions list
   wrangler versions deploy <version-id>
   ```

2. **Or disable Interactions Endpoint:**
   - Go to Discord Developer Portal
   - Remove Interactions Endpoint URL
   - Save changes

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Worker

on:
  push:
    branches: [main]
    paths:
      - 'src/worker/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 10.25.0
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: pnpm install --frozen-lockfile
        working-directory: src/worker
      - run: pnpm deploy:production
        working-directory: src/worker
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

## Best Practices

1. **Always test in preview first** before production deployment
2. **Monitor logs** after deployment to catch issues early
3. **Use custom domains** for production (more professional)
4. **Set up alerts** in Cloudflare Dashboard for errors
5. **Keep secrets secure** - never commit secrets to git
6. **Version control** - use `wrangler versions` for rollbacks

## Related Documentation

- [Worker README](./README.md)
- [HTTP Endpoint Migration Plan](../../docs/http-endpoint-migration-plan.md)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Docs](https://developers.cloudflare.com/workers/wrangler/)

