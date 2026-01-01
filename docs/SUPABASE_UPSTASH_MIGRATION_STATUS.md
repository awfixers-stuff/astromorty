# Supabase & Upstash Migration Status

## Current Status

✅ **Supabase Database**: Configured (DATABASE_URL is set)
❌ **Upstash Redis**: Not configured (EXTERNAL_SERVICES__REDIS_URL missing)

## Issues Found

### 1. Supabase Pooler Connection

Your Supabase connection string is using the **pooler** endpoint (port 6543) which includes a `pgbouncer` option that psycopg doesn't support.

**Current format:**
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-us-west-2.pooler.supabase.com:6543/postgres?pgbouncer=true
```

**Solution:** Use the **direct connection** string from Supabase instead:

1. Go to Supabase Dashboard → Settings → Database
2. Under "Connection string", select **"URI"** (not "Session mode" or "Transaction mode")
3. Copy the connection string (should look like):
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
4. Update your `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

**Note:** The code has been updated to automatically convert pooler connections, but using the direct connection string is recommended for better compatibility.

### 2. Upstash Redis Configuration

Add the following to your `.env` file:

```env
# Get this from: Upstash Dashboard → Your Database → Redis Details
EXTERNAL_SERVICES__REDIS_URL=redis://default:[YOUR-PASSWORD]@[YOUR-ENDPOINT].upstash.io:6379
```

**Steps:**
1. Go to [Upstash Dashboard](https://console.upstash.com/)
2. Select your Redis database
3. Go to "Redis Details"
4. Copy the connection string (format: `redis://default:[PASSWORD]@[ENDPOINT]:6379`)
5. Add to `.env` as `EXTERNAL_SERVICES__REDIS_URL`

## Next Steps

1. **Update Supabase Connection String**
   - Use direct connection (port 5432) instead of pooler (port 6543)
   - Update `DATABASE_URL` in `.env`

2. **Add Upstash Redis Configuration**
   - Add `EXTERNAL_SERVICES__REDIS_URL` to `.env`

3. **Verify Configuration**
   ```bash
   uv run python scripts/migrate_supabase_upstash.py
   ```

4. **Test Database Connection**
   ```bash
   uv run python scripts/test_db_connection.py
   ```

5. **Check Migration Status**
   ```bash
   uv run db status
   ```

6. **Apply Migrations**
   ```bash
   uv run db push
   ```

7. **Start the Bot**
   ```bash
   uv run astromorty start
   ```

## Verification Scripts

Two helper scripts have been created:

- `scripts/migrate_supabase_upstash.py` - Verifies Supabase and Upstash configuration
- `scripts/test_db_connection.py` - Tests database connection without importing all models

## Code Changes Made

1. **Updated `src/astromorty/shared/config/settings.py`**:
   - Added automatic conversion of Supabase pooler connections to direct connections
   - Removes `pgbouncer` option from connection strings
   - Converts port 6543 (pooler) to 5432 (direct)
   - Extracts project reference from username and converts hostname

## Troubleshooting

### Database Connection Fails

- Verify your Supabase connection string uses port **5432** (direct) not **6543** (pooler)
- Check that your password is correct
- Ensure SSL is enabled (should be automatic for Supabase URLs)

### Redis Connection Fails

- Verify the Redis URL format: `redis://default:[PASSWORD]@[ENDPOINT]:6379`
- Check that your Upstash database is active
- Ensure the password is URL-encoded if it contains special characters

### Migration Issues

- Make sure database connection works first
- Check migration files exist in `src/astromorty/database/migrations/versions/`
- Run `uv run db status` to see current migration state

