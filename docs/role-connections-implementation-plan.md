# Discord Role Connections Implementation Plan

## 📋 Overview

This plan outlines the implementation of Discord Role Connections for the Astromorty bot, allowing users to link external accounts and receive automatic role assignments based on verification metadata.

## 🎯 Objectives

1. **OAuth2 Flow**: Implement secure OAuth2 authorization for external account linking
2. **Metadata Management**: Handle Discord's role connection metadata system
3. **Automatic Role Assignment**: Assign/remove roles based on verified connections
4. **User Interface**: Provide commands for users to manage their connections
5. **Admin Controls**: Give server administrators control over role connections
6. **Security**: Implement proper token handling and verification

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Discord Bot   │    │   Web Server     │    │  External API  │
│   (astromorty) │◄──►│   (FastAPI)      │◄──►│ (GitHub/Twitter)│
│                │    │                │    │                │
│ - on_ready()    │    │ - OAuth flow   │    │ - Verify data   │
│ - on_member_update│    │ - Store tokens │    │ - Return profile │
│ - Commands      │    │ - Webhooks     │    │                │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                            ▲
                            │
                    ┌─────────────┐
                    │  Discord API  │
                    │ (Push metadata)│
                    └─────────────┘
```

## 📦 Dependencies & Prerequisites

### Required Libraries (add to pyproject.toml)
```toml
dependencies = [
    # ... existing dependencies ...
    "fastapi>=0.104.0",           # Web server for OAuth handling
    "uvicorn[standard]>=0.24.0",    # ASGI server
    "python-multipart>=0.0.6",       # Form data handling
    "cryptography>=41.0.0",           # JWT token validation
    "python-jose[cryptography]>=3.3.0", # JWT handling
]
```

### Discord Application Setup
```bash
# Required Discord Application Settings
✅ Bot Application with Message Content Intent
✅ Enable Role Connections Verification URL
✅ Configure OAuth2 Redirect URIs
✅ Define Role Connection Metadata Types
✅ Set Bot Permissions for role management
```

## 🗂️ Implementation Phases

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Discord Application Configuration
- [ ] Create/configure Discord application for Role Connections
- [ ] Set up verification URL: `https://your-domain.com/api/role-connections/verify`
- [ ] Configure OAuth2 redirect URIs
- [ ] Define metadata types in Discord Developer Portal

#### 1.2 Web Server Foundation
- [ ] Create `src/astromorty/web/` package
- [ ] Implement FastAPI application structure
- [ ] Set up basic health check endpoint
- [ ] Configure CORS middleware for Discord redirects

#### 1.3 Database Models
- [ ] Create `RoleConnection` model for storing user connections
- [ ] Create `ConnectionPlatform` enum (GitHub, Twitter, Steam, etc.)
- [ ] Create database migrations
- [ ] Implement CRUD controllers for role connections

### Phase 2: OAuth2 Implementation (Week 2)

#### 2.1 OAuth Flow Endpoints
```python
# src/astromorty/web/routes/oauth.py
@app.get("/api/role-connections/{platform}/authorize")
async def authorize_oauth(platform: str):
    """Initiate OAuth flow for specific platform"""
    
@app.post("/api/role-connections/{platform}/callback")  
async def oauth_callback(platform: str, code: str, state: str):
    """Handle OAuth callback from external platform"""
```

#### 2.2 Token Management
- [ ] Secure token storage (encryption at rest)
- [ ] Token refresh mechanisms
- [ ] Secure token deletion on unlink

#### 2.3 State Management
- [ ] Generate secure OAuth state tokens
- [ ] Validate state to prevent CSRF attacks
- [ ] Handle state timeout/cleanup

### Phase 3: External API Integration (Week 3)

#### 3.1 Supported Platforms
```python
# src/astromorty/services/external_apis/
class GitHubService:
    """GitHub API integration for role connections"""
    
class TwitterService:
    """Twitter API integration for role connections"""
    
class SteamService:
    """Steam API integration for role connections"""
```

#### 3.2 Profile Verification
- [ ] GitHub: Verify user exists, check specific repositories
- [ ] Twitter: Verify user exists, check follower count
- [ ] Steam: Verify user exists, check account age/level

#### 3.3 Metadata Mapping
```python
# Connection metadata to push to Discord
CONNECTION_METADATA = {
    "github": {
        "platform_name": "GitHub",
        "platform_username": "octocat",
        "verified": True,
        "account_created": "2023-01-01"
    },
    "twitter": {
        "platform_name": "Twitter", 
        "platform_username": "discorddev",
        "verified": True,
        "follower_count": 1000
    }
}
```

### Phase 4: Discord Integration (Week 4)

#### 4.1 Metadata API
```python
# src/astromorty/services/role_connections.py
class RoleConnectionManager:
    async def push_user_metadata(self, user_id: int, metadata: dict):
        """Push role connection metadata to Discord"""
        
    async def remove_user_metadata(self, user_id: int, platform_name: str):
        """Remove role connection metadata from Discord"""
```

#### 4.2 Role Assignment Logic
```python
# src/astromorty/modules/role_connections.py
class RoleConnections(commands.Cog):
    @commands.hybrid_command(name="link", description="Link your external account")
    async def link_command(self, ctx: commands.Context[Astromorty], platform: str):
        """Initiate account linking"""
        
    @commands.hybrid_command(name="unlink", description="Unlink your account") 
    async def unlink_command(self, ctx: commands.Context[Astromorty], platform: str):
        """Remove account linking"""
```

#### 4.3 Event Handlers
```python
# src/astromorty/core/events/role_connections.py
@commands.Cog.listener()
async def on_member_update(self, before: discord.Member, after: discord.Member):
    """Handle role updates from Discord role connections"""
    
@commands.Cog.listener() 
async def on_ready(self):
    """Sync existing role connections on bot startup"""
```

### Phase 5: User Interface (Week 5)

#### 5.1 User Commands
```python
# Link Management Commands
@commands.hybrid_command(name="connections")
async def show_connections(self, ctx: commands.Context[Astromorty]):
    """Show user's linked accounts"""
    
@commands.hybrid_command(name="verify")
async def verify_connection(self, ctx: commands.Context[Astromorty], platform: str):
    """Manually trigger verification for linked account"""
```

#### 5.2 User Dashboard (Optional)
```python
# src/astromorty/web/routes/dashboard.py
@app.get("/dashboard/connections")
async def connections_dashboard():
    """Web dashboard for managing connections"""
    
@app.post("/dashboard/connections/unlink")  
async def unlink_connection_web():
    """Web interface to unlink connections"""
```

#### 5.3 User Notifications
- [ ] Success/error messages for linking attempts
- [ ] Role assignment notifications
- [ ] Connection expiry warnings

### Phase 6: Admin Controls (Week 6)

#### 6.1 Administrative Commands
```python
# src/astromorty/modules/admin/role_connections.py
@commands.has_permissions(administrator=True)
@commands.hybrid_command(name="admin-connections")
async def admin_connections(self, ctx: commands.Context[Astromorty]):
    """Admin interface for managing user connections"""
    
@commands.hybrid_command(name="admin-verify-user")
async def admin_verify_user(self, ctx: commands.Context[Astromorty], user: discord.User):
    """Force verification of user's connections"""
```

#### 6.2 Configuration Management
```python
# src/astromorty/modules/config/role_connections.py
@commands.has_permissions(administrator=True)
@commands.hybrid_command(name="config-role-connections")
async def config_role_connections(self, ctx: commands.Context[Astromorty]):
    """Configure role connection settings"""
    # Platform enable/disable
    # Required verification criteria
    # Auto-assignment roles
```

#### 6.3 Audit & Monitoring
- [ ] Connection attempt logging
- [ ] Admin action audit trail
- [ ] Rate limiting per user/platform

## 🔒 Security Considerations

### Token Security
```python
# Secure token storage
class SecureTokenStorage:
    def encrypt_token(self, token: str) -> str:
        """Encrypt access tokens at rest"""
        
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access tokens for use"""
```

### OAuth Security
- [ ] Use PKCE (Proof Key for Code Exchange) for OAuth flows
- [ ] Validate redirect URIs to prevent open redirects
- [ ] Implement state token expiration (5-10 minutes)
- [ ] HTTPS only for all endpoints

### API Security
- [ ] Rate limiting per user/IP
- [ ] Input validation and sanitization
- [ ] SQL injection prevention
- [ ] CSRF protection for web forms

## 📊 Data Models

### Database Schema
```sql
-- Role Connections Table
CREATE TABLE role_connections (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES discord_users(id),
    platform VARCHAR(50) NOT NULL,
    platform_user_id VARCHAR(255) NOT NULL,
    platform_username VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Connection Platforms Table  
CREATE TABLE connection_platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    oauth_client_id VARCHAR(255) NOT NULL,
    oauth_client_secret_encrypted TEXT,
    oauth_authorize_url VARCHAR(500) NOT NULL,
    oauth_token_url VARCHAR(500) NOT NULL,
    oauth_scopes TEXT,
    verification_endpoint VARCHAR(500),
    is_enabled BOOLEAN DEFAULT TRUE,
    verification_criteria JSONB
);
```

### Pydantic Models
```python
# src/astromorty/database/models/role_connections.py
class RoleConnection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    platform: str
    platform_user_id: str  
    platform_username: str
    access_token_encrypted: str | None = None
    refresh_token_encrypted: str | None = None
    expires_at: datetime | None = None
    is_verified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectionPlatform(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    display_name: str
    oauth_client_id: str
    oauth_client_secret_encrypted: str
    oauth_authorize_url: str
    oauth_token_url: str
    oauth_scopes: str
    verification_endpoint: str | None = None
    is_enabled: bool = True
    verification_criteria: dict[str, Any] = Field(default_factory=dict)
```

## 🚀 File Structure

### New Files to Create
```
src/astromorty/
├── web/                          # FastAPI web application
│   ├── __init__.py
│   ├── app.py                    # FastAPI app factory
│   ├── routes/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── oauth.py               # OAuth endpoints
│   │   ├── dashboard.py          # User dashboard
│   │   ├── admin.py              # Admin endpoints
│   │   └── webhooks.py           # Discord webhooks
│   ├── middleware/                 # Custom middleware
│   │   ├── __init__.py
│   │   ├── cors.py               # CORS handling
│   │   ├── auth.py               # Authentication
│   │   └── rate_limit.py         # Rate limiting
│   ├── templates/                  # HTML templates
│   │   ├── oauth.html            # OAuth consent page
│   │   └── dashboard.html       # Dashboard pages
│   └── static/                     # Static assets
├── services/
│   ├── role_connections.py         # Core service logic
│   └── external_apis/               # External platform APIs
│       ├── __init__.py
│       ├── github.py
│       ├── twitter.py
│       └── base.py
├── database/models/
│   ├── role_connections.py        # Database models
│   └── connection_platforms.py
├── modules/
│   ├── role_connections.py        # User commands
│   └── admin/
│       └── role_connections.py  # Admin commands
└── core/events/
    ├── role_connections.py        # Discord event handlers
    └── webhooks.py               # Webhook handlers
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/web/test_oauth.py
class TestOAuthFlow:
    async def test_github_oauth_flow(self):
        """Test complete GitHub OAuth flow"""
        
    async def test_state_validation(self):
        """Test OAuth state token validation"""
        
    async def test_token_encryption(self):
        """Test secure token storage"""
```

### Integration Tests
```python
# tests/integration/test_role_connections.py
class TestRoleConnectionFlow:
    async def test_complete_linking_flow(self):
        """Test from OAuth to role assignment"""
        
    async def test_unlinking_flow(self):
        """Test connection removal and role cleanup"""
```

### E2E Tests
```python
# tests/e2e/test_discord_integration.py
class TestDiscordIntegration:
    async def test_discord_role_assignment(self):
        """Test Discord API role assignment"""
        
    async def test_webhook_processing(self):
        """Test Discord webhook processing"""
```

## 📈 Monitoring & Metrics

### Performance Metrics
```python
# src/astromorty/services/monitoring/role_connections.py
class RoleConnectionMetrics:
    def track_connection_attempt(self, platform: str, success: bool):
        """Track connection success rates"""
        
    def track_verification_time(self, platform: str, duration: float):
        """Track verification performance"""
        
    def track_role_assignments(self, count: int):
        """Track role assignment volume"""
```

### Health Checks
```python
# src/astromorty/web/health.py
@app.get("/health/role-connections")
async def health_check():
    """Comprehensive health monitoring"""
    return {
        "status": "healthy",
        "services": {
            "database": await check_database_health(),
            "discord_api": await check_discord_health(),
            "external_apis": await check_external_apis_health()
        },
        "metrics": await get_connection_metrics()
    }
```

## 🚀 Deployment Configuration

### Environment Variables
```bash
# Role Connections Configuration
ROLE_CONNECTIONS_SECRET_KEY=your-encryption-key
ROLE_CONNECTIONS_WEB_HOST=0.0.0.0
ROLE_CONNECTIONS_WEB_PORT=8000
ROLE_CONNECTIONS_DISCORD_BOT_TOKEN=your-bot-token

# External API Keys (encrypted)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
```

### Docker Updates
```dockerfile
# Add to existing Containerfile
RUN pip install fastapi uvicorn python-multipart
EXPOSE 8000
CMD ["uvicorn", "astromorty.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Deployment
```yaml
# docker-compose.role-connections.yml
services:
  astromorty-bot:
    # ... existing bot service ...
    
  astromorty-web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ROLE_CONNECTIONS_WEB_HOST=0.0.0.0
      - ROLE_CONNECTIONS_WEB_PORT=8000
    depends_on:
      - astromorty-bot
```

## 📚 Documentation Updates

### User Documentation
```markdown
# Role Connections Documentation
## Overview
Connect your GitHub, Twitter, and other accounts to receive automatic roles in Discord.

## Supported Platforms
- **GitHub**: Repository verification, contribution count
- **Twitter**: Follower count, account verification
- **Steam**: Account age, gaming activity

## Commands
- `/link github` - Link your GitHub account
- `/connections` - View your linked accounts  
- `/unlink github` - Unlink your account
```

### Admin Documentation
```markdown
# Role Connections Admin Guide
## Configuration
Configure role connection settings per server.

## Troubleshooting
Common issues and solutions for role connections.
```

## 🔄 Implementation Timeline

### Week 1: Foundation
- Day 1-2: Discord app setup and basic web server
- Day 3-4: Database models and migrations
- Day 5-7: Basic OAuth flow implementation

### Week 2: External APIs  
- Day 8-10: GitHub API integration
- Day 11-12: Twitter API integration
- Day 13-14: Profile verification logic

### Week 3: Discord Integration
- Day 15-17: Discord API integration for metadata
- Day 18-19: Role assignment system
- Day 20-21: Event handlers and user commands

### Week 4: Polish & Testing
- Day 22-24: Admin controls and configuration
- Day 25-26: Comprehensive testing
- Day 27-28: Documentation and deployment prep

### Week 5: Launch
- Day 29-30: Production deployment
- Day 31: Monitoring and maintenance setup

## 🎯 Success Metrics

### Technical Metrics
- OAuth flow success rate > 95%
- Role assignment accuracy > 99%  
- API response time < 500ms
- Uptime > 99.9%

### User Experience
- Onboarding completion rate > 90%
- Support ticket reduction > 50%
- User satisfaction score > 4.5/5

---

**Created**: 2025-12-31  
**Author**: Astromorty Development Team  
**Status**: Implementation Plan - Ready for Development