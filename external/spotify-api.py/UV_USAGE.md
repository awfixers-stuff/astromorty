# UV Usage Guide

This project is now managed entirely via [uv](https://docs.astral.sh/uv/), a fast Python package manager written in Rust.

## Installation

First, ensure you have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Getting Started

### Install Dependencies

To install all dependencies and create a virtual environment:

```bash
uv sync
```

This will:
- Create a `.venv` directory with a virtual environment
- Install all dependencies specified in `pyproject.toml`
- Install the `spotify-api.py` package in editable mode

### Running Python Scripts

Use `uv run` to execute Python scripts with the project's dependencies:

```bash
uv run python your_script.py
```

Or activate the virtual environment:

```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

### Using the Package

```python
from spotifyapi import Client

client = Client(token='your-token')

# Get a new token using client credentials
auth = client.oauth.get(
    client_id='your-client-id',
    client_secret='your-client-secret'
)

# Search for tracks
tracks = client.track.search('some query', 5)

# Get artist info
artist = client.artist.get('artist-id')
```

## Project Management

### Adding Dependencies

To add a new dependency:

```bash
uv add package-name
```

For development dependencies:

```bash
uv add --dev package-name
```

### Removing Dependencies

```bash
uv remove package-name
```

### Updating Dependencies

To update all dependencies:

```bash
uv lock --upgrade
uv sync
```

### Building the Package

To build distribution packages (wheel and sdist):

```bash
uv build
```

This will create files in the `dist/` directory.

## Project Structure

```
spotify-api.py/
├── spotifyapi/          # Main package directory
│   ├── __init__.py      # Package initialization and Client class
│   ├── Album.py         # Album-related functions
│   ├── Artist.py        # Artist-related functions
│   ├── Browse.py        # Browse/discovery functions
│   ├── Episodes.py      # Podcast episode functions
│   ├── Exception.py     # Custom exceptions
│   ├── Oauth.py         # Authentication
│   ├── Playlist.py      # Playlist functions
│   ├── Search.py        # Search functionality
│   ├── Shows.py         # Podcast show functions
│   ├── Track.py         # Track-related functions
│   └── Util.py          # Utility functions
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Locked dependency versions
└── README.md           # Main documentation

```

## Dependencies

This project has only one runtime dependency:
- `requests` - HTTP library for API calls

All dependencies are locked in `uv.lock` to ensure reproducible builds.

## Migration from setup.py

This project has been migrated from `setup.py` to `pyproject.toml`:
- ✅ Modern Python packaging standards (PEP 517/518)
- ✅ Faster dependency resolution with uv
- ✅ Locked dependencies for reproducibility
- ✅ No changes to existing dependencies or functionality

## Troubleshooting

### Virtual Environment Not Found

If you get errors about missing modules, ensure the virtual environment is synced:

```bash
uv sync
```

### Import Errors

Make sure you're running Python through uv or with the virtual environment activated:

```bash
uv run python script.py
```

### Lock File Out of Sync

If `uv.lock` is out of sync with `pyproject.toml`:

```bash
uv lock
uv sync
```

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Project README](README.md)