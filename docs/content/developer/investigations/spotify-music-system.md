---
title: Spotify Music System Investigation
description: Investigation into implementing a music system via Spotify API for Tux Discord bot
tags:
  - investigation
  - music
  - spotify
  - voice
  - api-integration
---

# Spotify Music System Investigation

## Executive Summary

This document investigates the implementation of a music system for Tux using Spotify's Web API. The system would allow users to search for tracks, manage playlists, and control music playback in Discord voice channels.

**Key Findings:**

- Spotify API provides excellent metadata and search capabilities
- **Direct audio streaming from Spotify is not possible** - must use alternative sources (YouTube, direct URLs)
- Requires OAuth 2.0 authentication for user-specific features
- Discord voice connections require FFmpeg for audio processing
- Architecture should separate Spotify API (metadata) from audio playback (streaming)

## Architecture Overview

### High-Level Design

```
┌─────────────────┐
│  Discord User   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      Music Module (Cog)              │
│  - Commands (play, pause, skip)    │
│  - Queue management                  │
│  - User interaction                  │
└────────┬────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Spotify      │  │ Audio        │  │ Database     │
│ Service      │  │ Service      │  │ Models       │
│ (Metadata)   │  │ (Playback)   │  │ (Queue)      │
└──────────────┘  └──────────────┘  └──────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Spotify API  │  │ FFmpeg/      │  │ PostgreSQL   │
│ (OAuth)      │  │ yt-dlp       │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Component Responsibilities

1. **Music Module (Cog)**: User-facing Discord commands
2. **Spotify Service**: API integration for search, playlists, metadata
3. **Audio Service**: Voice connection management and playback
4. **Database Models**: Queue persistence, user preferences, playlists

## Spotify API Integration

### Using spotify-api.py Package

We will use the `spotify-api.py` package located in `external/spotify-api.py`. This package provides a Python wrapper for the Spotify Web API with classes for Track, Artist, Album, Playlist, User, and OAuth management.

**Note**: The current version uses synchronous `requests` library. We will need to either:

1. Update it to use `httpx` for async support (recommended)
2. Wrap synchronous calls in `asyncio.to_thread()` for async compatibility

### Type Definitions

We will reference `spotify-types` (TypeScript definitions in `external/spotify-types`) as a guide for creating Python type hints using `TypedDict` or Pydantic models. This ensures type safety and matches Spotify's API response structures.

### Authentication Options

#### 1. Client Credentials Flow (Recommended for Search)

- **Use Case**: Public data access (search, track info, public playlists)
- **No User Auth Required**: Perfect for bot commands
- **Limitations**: Cannot access user-specific data (saved tracks, private playlists)

```python
from spotifyapi import Client

# Get access token using OAuth
client = Client(token='NO TOKEN')  # Leave empty for OAuth
auth_response = client.oauth.get(
    client_id='your-client-id',
    client_secret='your-client-secret'
)
access_token = auth_response['access_token']

# Create client with token
spotify_client = Client(token=access_token)
```

#### 2. Authorization Code Flow (For User Features)

- **Use Case**: User playlists, saved tracks, playback control
- **Requires User Auth**: OAuth redirect flow
- **Complexity**: Higher - requires web server for callback
- **Status**: Not yet implemented in spotify-api.py, will need to add

### Available API Methods (via spotify-api.py)

The `spotify-api.py` package provides the following classes and methods:

#### Track Class

- `track.search(query: str, limit: int)` - Search for tracks
- `track.get(trackID: str, advanced: bool)` - Get track details
- `track.audio_features(trackID: str)` - Get audio features
- `track.audio_analysis(trackID: str)` - Get audio analysis

#### Artist Class

- `artist.search(query: str, limit: int)` - Search for artists
- `artist.get(artistID: str)` - Get artist details
- `artist.albums(artistID: str, limit: int)` - Get artist albums
- `artist.top_tracks(artistID: str)` - Get top tracks
- `artist.related_artists(artistID: str)` - Get related artists

#### Album Class

- `album.search(query: str, limit: int)` - Search for albums
- `album.get(albumID: str)` - Get album details
- `album.get_tracks(albumID: str, limit: int)` - Get album tracks

#### Playlist Class

- `playlist.get(playlistID: str)` - Get playlist details
- `playlist.tracks(playlistID: str, limit: int)` - Get playlist tracks

#### User Class

- `user.get(userID: str)` - Get user details

#### Search Class

- `client.search(query: str, limit: int)` - General search across all types

### Missing Features (To Be Added)

The following features are not yet in `spotify-api.py` and will need to be added:

- User playlists (`GET /v1/me/playlists`)
- User saved tracks (`GET /v1/me/tracks`)
- Recommendations (`GET /v1/recommendations`)
- Authorization Code Flow (for user-specific features)

### Rate Limits

- **Default**: 10,000 requests per hour per application
- **Burst**: Up to 100 requests per second
- **Token Refresh**: Access tokens expire after 1 hour (refresh automatically)

## Audio Playback Architecture

### Critical Limitation

**Spotify does not provide direct audio streaming URLs.** The Spotify Web API only provides metadata, not actual audio files.

### Solution: Hybrid Approach

1. **Use Spotify API** for:
   - Track search and discovery
   - Metadata (title, artist, album art, duration)
   - Playlist information
   - Recommendations

2. **Use Alternative Sources** for actual audio:
   - **YouTube** (via `yt-dlp`) - Most common approach
   - **Direct audio URLs** (if available)
   - **Other streaming services** (SoundCloud, etc.)

### Implementation Flow

```
User: /play <spotify-track-url>
  ↓
1. Extract Spotify track ID from URL
  ↓
2. Query Spotify API for metadata
  ↓
3. Search YouTube for track using metadata
  ↓
4. Download/stream from YouTube via yt-dlp
  ↓
5. Play in Discord voice channel via FFmpeg
```

### Discord Voice Connection

Discord.py provides voice support via `discord.VoiceClient`:

```python
# Connect to voice channel
voice_client = await voice_channel.connect()

# Play audio source
audio_source = discord.FFmpegPCMAudio(
    source=audio_url_or_file,
    executable="ffmpeg",  # Must be installed
    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    options="-vn"  # No video
)

voice_client.play(audio_source)
```

### Required Dependencies

```toml
# For Spotify API
# spotify-api.py is in external/spotify-api.py (local package)

# For audio playback
yt-dlp>=2024.1.0  # YouTube downloader
PyNaCl>=1.5.0  # Already in dependencies - for voice encryption

# FFmpeg must be installed system-wide (not Python package)
# Docker: Add to Containerfile
# Local: Install via package manager
```

## Database Models

### Proposed Models

```python
# src/tux/database/models/models.py

class MusicQueue(BaseModel, table=True):
    """Music queue entry for a guild."""
    
    id: int = Field(primary_key=True, sa_type=BigInteger)
    guild_id: int = Field(foreign_key="guild.id", sa_type=BigInteger)
    user_id: int = Field(sa_type=BigInteger)  # User who queued
    spotify_track_id: str | None = Field(default=None)
    title: str
    artist: str
    duration_ms: int
    thumbnail_url: str | None = Field(default=None)
    audio_source_url: str  # YouTube URL or direct audio URL
    position: int  # Queue position
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Relationships
    guild: Guild = Relationship(back_populates="music_queues")


class MusicPlaylist(BaseModel, table=True):
    """User-created playlists."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    guild_id: int = Field(foreign_key="guild.id", sa_type=BigInteger)
    user_id: int = Field(sa_type=BigInteger)  # Creator
    name: str
    description: str | None = Field(default=None)
    is_public: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Relationships
    guild: Guild = Relationship(back_populates="music_playlists")
    tracks: list[MusicPlaylistTrack] = Relationship(back_populates="playlist")


class MusicPlaylistTrack(BaseModel, table=True):
    """Track in a playlist."""
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    playlist_id: UUID = Field(foreign_key="musicplaylist.id")
    spotify_track_id: str | None = Field(default=None)
    title: str
    artist: str
    duration_ms: int
    thumbnail_url: str | None = Field(default=None)
    position: int  # Order in playlist
    
    # Relationships
    playlist: MusicPlaylist = Relationship(back_populates="tracks")


class MusicGuildSettings(BaseModel, table=True):
    """Guild-specific music settings."""
    
    guild_id: int = Field(
        primary_key=True,
        foreign_key="guild.id",
        sa_type=BigInteger
    )
    default_volume: float = Field(default=0.5, ge=0.0, le=1.0)
    max_queue_size: int = Field(default=100, ge=1, le=500)
    allow_spotify_links: bool = Field(default=True)
    allow_youtube_links: bool = Field(default=True)
    dj_role_id: int | None = Field(default=None, sa_type=BigInteger)
    voice_channel_id: int | None = Field(default=None, sa_type=BigInteger)
```

### Enum Additions

```python
# src/tux/database/models/enums.py

class MusicSource(str, Enum):
    """Source of music track."""
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    DIRECT = "direct"
    SOUNDCLOUD = "soundcloud"
```

## Service Layer Structure

### Spotify Service

```python
# src/tux/services/music/spotify_service.py

import asyncio
from typing import Any
from spotifyapi import Client

class SpotifyService:
    """Service for interacting with Spotify Web API using spotify-api.py."""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._client: Client | None = None
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None
    
    async def _get_client(self) -> Client:
        """Get or create Spotify client with valid token."""
        # Check if token needs refresh
        if (
            self._access_token is None
            or self._token_expires_at is None
            or datetime.now(UTC) >= self._token_expires_at
        ):
            await self._refresh_token()
        
        if self._client is None or self._client.token != self._access_token:
            self._client = Client(token=self._access_token)
        
        return self._client
    
    async def _refresh_token(self) -> None:
        """Refresh access token using Client Credentials flow."""
        # Run synchronous OAuth in thread pool
        temp_client = Client(token='NO TOKEN')
        auth_response = await asyncio.to_thread(
            temp_client.oauth.get,
            self.client_id,
            self.client_secret
        )
        
        self._access_token = auth_response['access_token']
        # Tokens expire after 1 hour
        self._token_expires_at = datetime.now(UTC) + timedelta(seconds=3600)
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 20
    ) -> dict[str, Any]:
        """Search for tracks."""
        client = await self._get_client()
        # Run synchronous search in thread pool
        return await asyncio.to_thread(
            client.track.search,
            query,
            min(limit, 50)  # API limit is 50
        )
    
    async def get_track(
        self,
        track_id: str,
        advanced: bool = False
    ) -> dict[str, Any]:
        """Get track details."""
        client = await self._get_client()
        return await asyncio.to_thread(
            client.track.get,
            track_id,
            advanced
        )
    
    async def get_playlist(
        self,
        playlist_id: str
    ) -> dict[str, Any]:
        """Get playlist details."""
        client = await self._get_client()
        return await asyncio.to_thread(
            client.playlist.get,
            playlist_id
        )
    
    async def get_playlist_tracks(
        self,
        playlist_id: str,
        limit: int = 50
    ) -> dict[str, Any]:
        """Get tracks from playlist."""
        client = await self._get_client()
        return await asyncio.to_thread(
            client.playlist.tracks,
            playlist_id,
            min(limit, 50)
        )
    
    async def get_audio_features(
        self,
        track_id: str
    ) -> dict[str, Any]:
        """Get audio features for a track."""
        client = await self._get_client()
        return await asyncio.to_thread(
            client.track.audio_features,
            track_id
        )
```

### Audio Service

```python
# src/tux/services/music/audio_service.py

class AudioService:
    """Service for managing Discord voice connections and playback."""
    
    def __init__(self, bot: Tux):
        self.bot = bot
        self.voice_clients: dict[int, discord.VoiceClient] = {}
        self.queues: dict[int, asyncio.Queue] = {}
    
    async def connect(
        self,
        guild_id: int,
        channel: discord.VoiceChannel
    ) -> discord.VoiceClient:
        """Connect to voice channel."""
    
    async def disconnect(self, guild_id: int) -> None:
        """Disconnect from voice channel."""
    
    async def play_track(
        self,
        guild_id: int,
        track_url: str,
        metadata: dict[str, Any]
    ) -> None:
        """Play a track in voice channel."""
    
    async def pause(self, guild_id: int) -> None:
        """Pause playback."""
    
    async def resume(self, guild_id: int) -> None:
        """Resume playback."""
    
    async def stop(self, guild_id: int) -> None:
        """Stop playback."""
```

### Queue Service

```python
# src/tux/services/music/queue_service.py

class QueueService:
    """Service for managing music queues."""
    
    def __init__(self, db: DatabaseCoordinator):
        self.db = db
    
    async def add_to_queue(
        self,
        guild_id: int,
        user_id: int,
        track_data: dict[str, Any]
    ) -> MusicQueue:
        """Add track to queue."""
    
    async def get_queue(
        self,
        guild_id: int
    ) -> list[MusicQueue]:
        """Get current queue."""
    
    async def remove_from_queue(
        self,
        guild_id: int,
        queue_id: int
    ) -> None:
        """Remove track from queue."""
    
    async def clear_queue(self, guild_id: int) -> None:
        """Clear entire queue."""
```

## Configuration Requirements

### Environment Variables

```python
# src/tux/shared/config/models.py

class SpotifyConfig(BaseModel):
    """Spotify API configuration."""
    
    CLIENT_ID: Annotated[
        str,
        Field(
            default="",
            description="Spotify API Client ID",
            examples=["your_spotify_client_id"],
        ),
    ]
    
    CLIENT_SECRET: Annotated[
        str,
        Field(
            default="",
            description="Spotify API Client Secret",
            examples=["your_spotify_client_secret"],
        ),
    ]
    
    REDIRECT_URI: Annotated[
        str,
        Field(
            default="http://localhost:3000/callback",
            description="OAuth redirect URI (for user auth features)",
            examples=["http://localhost:3000/callback"],
        ),
    ]


# Add to ExternalServices or create new MusicConfig
class MusicConfig(BaseModel):
    """Music system configuration."""
    
    SPOTIFY: SpotifyConfig = Field(default_factory=SpotifyConfig)
    FFMPEG_PATH: Annotated[
        str,
        Field(
            default="ffmpeg",
            description="Path to FFmpeg executable",
            examples=["ffmpeg", "/usr/bin/ffmpeg"],
        ),
    ]
    MAX_QUEUE_SIZE: Annotated[
        int,
        Field(
            default=100,
            ge=1,
            le=500,
            description="Maximum queue size per guild",
        ),
    ]
```

## Module Structure

### Proposed File Organization

```
src/tux/
├── modules/
│   └── music/
│       ├── __init__.py
│       ├── music.py          # Main cog with commands
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── play.py       # /play command
│       │   ├── queue.py      # /queue command
│       │   ├── skip.py       # /skip command
│       │   ├── pause.py      # /pause command
│       │   ├── resume.py      # /resume command
│       │   ├── stop.py        # /stop command
│       │   └── playlist.py   # Playlist management
│       └── views/
│           ├── __init__.py
│           └── queue_view.py # Interactive queue UI
│
├── services/
│   └── music/
│       ├── __init__.py
│       ├── spotify_service.py    # Spotify API integration
│       ├── audio_service.py     # Voice connection & playback
│       ├── queue_service.py        # Queue management
│       └── youtube_service.py      # YouTube search/download
│
└── database/
    └── models/
        └── models.py  # Add MusicQueue, MusicPlaylist, etc.
```

## Implementation Phases

### Phase 1: Foundation (MVP)

- [ ] Update `spotify-api.py` to use `httpx` for async support (or wrap in async)
- [ ] Create Python type definitions based on `spotify-types`
- [ ] Spotify API service with Client Credentials auth using `spotify-api.py`
- [ ] Basic audio service (connect, play, disconnect)
- [ ] Simple queue (in-memory)
- [ ] `/play` command (Spotify URL → YouTube → Play)
- [ ] `/queue` command (show current queue)
- [ ] `/skip` command
- [ ] `/stop` command

### Phase 2: Enhanced Features

- [ ] Persistent queue (database)
- [ ] `/pause` and `/resume` commands
- [ ] `/volume` command
- [ ] Queue position management
- [ ] Better error handling and user feedback

### Phase 3: Advanced Features

- [ ] Playlist support (database models)
- [ ] `/playlist create/add/remove` commands
- [ ] User authentication (OAuth) for personal playlists
- [ ] Recommendations
- [ ] Search command (`/search`)
- [ ] Now playing embed with controls

### Phase 4: Polish

- [ ] Interactive queue UI (buttons for skip, remove, etc.)
- [ ] Auto-disconnect when empty
- [ ] DJ role permissions
- [ ] Per-guild settings
- [ ] Queue history
- [ ] Statistics

## Dependencies to Add

### Python Dependencies

```toml
# pyproject.toml

dependencies = [
    # ... existing dependencies ...
    "yt-dlp>=2024.1.0",    # YouTube downloader for audio playback
    # FFmpeg must be installed system-wide
]

# Note: spotify-api.py is in external/spotify-api.py
# We will either:
# 1. Add it as a local dependency using uv's path support
# 2. Update it to use httpx and integrate directly
```

### Local Package Integration

Since `spotify-api.py` is in `external/spotify-api.py`, we have several options:

#### Option 1: Add as Local Dependency (Recommended)

```toml
# pyproject.toml
dependencies = [
    # ... existing ...
    "spotify-api.py @ file:///${PROJECT_ROOT}/external/spotify-api.py",
]
```

#### Option 2: Update to Use httpx

Update `spotify-api.py` to use `httpx` instead of `requests` for async support:

- Replace `requests` with `httpx.AsyncClient`
- Make all methods async
- Integrate directly into the codebase

#### Option 3: Wrap in Async Wrapper

Keep synchronous but wrap all calls in `asyncio.to_thread()` (shown in service example above)

### Type Definitions

The `spotify-types` package provides TypeScript definitions that we can use as reference for creating Python type hints:

```python
# src/tux/services/music/types.py
# Reference: external/spotify-types/typings/track.d.ts

from typing import TypedDict, NotRequired

class SimplifiedTrack(TypedDict):
    """Simplified track object from Spotify API."""
    id: str
    name: str
    artists: list[dict[str, Any]]  # SimplifiedArtist[]
    duration_ms: int
    explicit: bool
    preview_url: str | None
    # ... other fields from spotify-types
```

We can create Python equivalents of the TypeScript types for type safety.

### System Dependencies

**FFmpeg** must be installed on the system:

```dockerfile
# Containerfile
RUN apt-get update && apt-get install -y ffmpeg
```

Or via Nix (if using Nix):

```nix
# flake.nix
environment.systemPackages = [ pkgs.ffmpeg ];
```

## Limitations and Considerations

### Technical Limitations

1. **No Direct Spotify Streaming**: Must use YouTube or other sources
2. **Rate Limits**: 10,000 requests/hour (should be sufficient)
3. **Token Management**: Access tokens expire (need refresh logic)
4. **FFmpeg Required**: System dependency, not Python package
5. **Voice Channel Limits**: One voice client per guild

### Legal Considerations

1. **YouTube ToS**: Using yt-dlp may violate YouTube's Terms of Service
2. **Spotify ToS**: Ensure compliance with Spotify's API terms
3. **Copyright**: Playing copyrighted music may have legal implications
4. **Fair Use**: Consider fair use policies in your jurisdiction

### Performance Considerations

1. **Audio Streaming**: Large bandwidth usage
2. **Queue Management**: Database queries for persistent queues
3. **Concurrent Guilds**: Multiple guilds playing simultaneously
4. **Memory Usage**: Audio buffers and queue storage

## Alternative Approaches

### Option 1: Pure YouTube (No Spotify)

- Simpler implementation
- No OAuth complexity
- Less metadata richness
- Still requires yt-dlp

### Option 2: Spotify + YouTube Hybrid (Recommended)

- Rich metadata from Spotify
- Actual playback from YouTube
- Best user experience
- More complex implementation

### Option 3: Direct Audio URLs Only

- Simplest implementation
- Limited track availability
- No search functionality
- Users must provide URLs

## Testing Strategy

### Unit Tests

- Spotify API service (mocked responses)
- Queue service (database operations)
- URL parsing and validation

### Integration Tests

- Spotify API integration (with test credentials)
- Database operations
- Command parsing

### Manual Testing

- Voice connection
- Audio playback
- Queue management
- Error handling

## Security Considerations

1. **Client Secret**: Store securely, never commit to git
2. **OAuth Tokens**: Encrypt user tokens in database
3. **Input Validation**: Validate all Spotify URLs and track IDs
4. **Rate Limiting**: Implement rate limiting for commands
5. **Permissions**: Check user permissions before queueing

## Next Steps

1. **Review and Approve**: Review this investigation document
2. **Update spotify-api.py**:
   - Option A: Update to use `httpx` for async support (recommended)
   - Option B: Keep synchronous and wrap in `asyncio.to_thread()` (faster to implement)
3. **Create Python Type Definitions**:
   - Reference `spotify-types` TypeScript definitions
   - Create Python `TypedDict` or Pydantic models for type safety
4. **Integrate Local Package**: Add `spotify-api.py` as local dependency in `pyproject.toml`
5. **Set Up Spotify App**: Create Spotify Developer account and app
6. **Implement Phase 1**: Start with MVP features
7. **Test Locally**: Test with development bot
8. **Iterate**: Add features based on feedback

## Package Integration

### Current Package Structure

```
external/
├── spotify-api.py/
│   ├── spotifyapi/
│   │   ├── __init__.py
│   │   ├── Client.py (main client)
│   │   ├── Oauth.py (token management)
│   │   ├── Track.py
│   │   ├── Artist.py
│   │   ├── Album.py
│   │   ├── Playlist.py
│   │   ├── User.py
│   │   └── ...
│   └── pyproject.toml
└── spotify-types/
    └── typings/
        ├── track.d.ts
        ├── artist.d.ts
        ├── album.d.ts
        └── ...
```

### Integration Options

#### Option 1: Local Path Dependency (Quick Start)

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "spotify-api.py @ file:///${PROJECT_ROOT}/external/spotify-api.py",
]
```

Then use in code:

```python
from spotifyapi import Client
```

#### Option 2: Update to Async (Recommended Long-term)

Update `spotify-api.py` to use `httpx`:

- Replace `import requests` with `import httpx`
- Change all methods to async
- Use `httpx.AsyncClient` instead of `requests.request`
- Integrate directly into codebase

#### Option 3: Async Wrapper (Temporary Solution)

Keep package as-is, wrap in async service:

```python
# Already shown in SpotifyService example above
# Uses asyncio.to_thread() to run sync code in thread pool
```

## Package Update Requirements

### spotify-api.py Updates Needed

1. **Async Support** (High Priority):
   - Replace `requests` with `httpx.AsyncClient`
   - Convert all methods to async
   - Add proper error handling
   - Update `Client` class to manage async client lifecycle

2. **Type Hints** (Medium Priority):
   - Add return type annotations
   - Use types from `spotify-types` as reference
   - Add proper type hints for all methods

3. **Additional Features** (Future):
   - Authorization Code Flow support
   - User playlists endpoint (`GET /v1/me/playlists`)
   - User saved tracks endpoint (`GET /v1/me/tracks`)
   - Recommendations endpoint (`GET /v1/recommendations`)
   - Better error handling and retries
   - Rate limiting awareness

4. **Dependencies Update**:
   - Update `pyproject.toml` to use `httpx` instead of `requests`
   - Ensure Python 3.13+ compatibility

### spotify-types Usage

The TypeScript definitions in `spotify-types` serve as:

- **Reference** for API response structures
- **Documentation** for field names and types
- **Guide** for creating Python type definitions

We can create a Python equivalent module:

```python
# src/tux/services/music/spotify_types.py
# Based on external/spotify-types/typings/*.d.ts

from typing import TypedDict, NotRequired

class SimplifiedTrack(TypedDict):
    """Simplified track object - matches spotify-types/track.d.ts"""
    id: str
    name: str
    artists: list[dict[str, Any]]  # SimplifiedArtist[]
    duration_ms: int
    explicit: bool
    preview_url: str | None
    # ... map all fields from TypeScript definition

class Track(SimplifiedTrack):
    """Full track object - matches spotify-types/track.d.ts"""
    album: dict[str, Any]  # SimplifiedAlbum
    popularity: int
    # ... additional fields
```

This ensures type safety and matches Spotify's actual API responses.

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotify Authorization Guide](https://developer.spotify.com/documentation/web-api/concepts/authorization)
- [Discord.py Voice Documentation](https://discordpy.readthedocs.io/en/stable/api.html#voice)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
