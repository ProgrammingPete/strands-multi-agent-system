# UV Package Manager Migration

All documentation has been updated to use `uv` instead of direct `python` commands, following the project's standard package management approach.

## Updated Files

### Documentation Files
- ✅ `backend/README.md` - Updated all Python and uvicorn commands
- ✅ `backend/QUICK_START.md` - Updated startup and testing commands
- ✅ `backend/IMPLEMENTATION_SUMMARY.md` - Updated testing examples

### Scripts
- ✅ `start_backend.sh` - Updated to use `uv run`

## Command Changes

### Running the Server

**Before:**
```bash
python -m backend.main
uvicorn backend.main:app --reload
```

**After:**
```bash
uv run python -m backend.main
uv run uvicorn backend.main:app --reload
```

### Running Tests

**Before:**
```bash
python backend/test_server.py
pytest tests/
```

**After:**
```bash
uv run python backend/test_server.py
uv run pytest tests/
```

### Docker

**Before:**
```dockerfile
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**After:**
```dockerfile
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service

**Before:**
```ini
Environment="PATH=/opt/canvalo/.venv/bin"
ExecStart=/opt/canvalo/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**After:**
```ini
ExecStart=/usr/local/bin/uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Benefits of Using UV

1. **Consistent Environment**: `uv run` ensures the correct virtual environment is used
2. **Dependency Management**: Automatically handles dependency resolution
3. **Project Standard**: Aligns with the project's existing tooling
4. **Simplified Setup**: No need to manually activate virtual environments

## Quick Reference

### Development
```bash
# Start server
./start_backend.sh
# or
uv run python -m backend.main

# Run tests
uv run python backend/test_server.py

# Install dependencies
uv sync
```

### Production
```bash
# Start with uvicorn
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker run -p 8000:8000 canvalo-backend
```

## Notes

- The `main.py` file's `if __name__ == "__main__"` block remains unchanged as it uses `uvicorn.run()` directly
- All shell scripts now use `uv run` for consistency
- Docker containers include `uv` installation in the build process
- Systemd services use the global `uv` installation

## Verification

All commands have been tested and verified to work with the `uv` package manager:
- ✅ Server starts successfully
- ✅ Dependencies are properly resolved
- ✅ Virtual environment is automatically managed
- ✅ No manual activation required
