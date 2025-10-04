# Tests

This directory contains all test files for the cv_minecraft project.

## Running Tests

Tests can be run individually from the project root directory:

```bash
python3 tests/test_basic_movement.py
python3 tests/test_collision_logging.py
python3 tests/test_game_recorder.py
# ... etc
```

## Test Categories

- **Collision Tests**: `test_collision_*.py`, `test_basic_movement.py`
- **Server Tests**: `test_minecraft_server.py`, `test_server_*.py`
- **Integration Tests**: `test_integration_*.py`, `test_client_server_sync.py`
- **Feature Tests**: `test_camera_*.py`, `test_cube_*.py`, `test_game_recorder.py`
- **Block/World Tests**: `test_block_*.py`, `test_same_map_validation.py`
- **Network Tests**: `test_rtsp_users.py`, `test_query_services.py`

## Test Structure

All tests use `sys.path` manipulation to import modules from the parent directory:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
```

This allows tests to import project modules like `minecraft_physics`, `minecraft_client_fr`, etc.
