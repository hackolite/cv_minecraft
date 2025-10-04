# Tests and Demos Directory

This directory contains all test and demo files for the cv_minecraft project.

## Running Tests

Tests can be run from the project root directory:

```bash
# Run individual tests
python3 tests/test_camera_screenshot_system.py
python3 tests/test_block_metadata.py
python3 tests/test_server_integration.py

# Run demos
python3 tests/demo_camera_screenshots.py
python3 tests/demo_minecraft_client.py
```

## Test Categories

### Camera System Tests
- `test_camera_screenshot_system.py` - Complete camera screenshot workflow tests
- `test_camera_block_visibility.py` - Camera block visibility tests
- `demo_camera_screenshots.py` - Demo generating multiple camera screenshots

### Server and Integration Tests
- `test_server_integration.py` - Server integration tests
- `test_server_connectivity.py` - Server connectivity tests
- `test_integration_final.py` - Final integration tests
- `test_client_server_sync.py` - Client-server synchronization tests

### Block and Metadata Tests
- `test_block_metadata.py` - Block metadata system tests
- `test_block_id_integration.py` - Block ID integration tests
- `test_query_services.py` - Query service tests

### Collision and Physics Tests
- `test_collision_consistency.py` - Collision consistency tests
- `test_collision_fix_verification.py` - Collision fix verification
- `test_collision_logging.py` - Collision logging tests
- `test_simple_collision_system.py` - Simple collision system tests
- `test_unified_collision_api.py` - Unified collision API tests
- `test_player_collision.py` - Player collision tests
- `test_basic_movement.py` - Basic movement tests

### Cube System Tests
- `test_cube_system.py` - Cube system tests
- `test_cube_window.py` - Cube window tests
- `demo_cube_server.py` - Cube server demo
- `demo_cube_window.py` - Cube window demo

### Recording Tests
- `test_game_recorder.py` - Game recorder tests
- `test_threaded_recorder.py` - Threaded recorder tests
- `demo_recorder_improvements.py` - Recorder improvements demo
- `demo_recording.py` - Recording demo

### Other Tests
- `test_minecraft_server.py` - Minecraft server tests
- `test_same_map_validation.py` - Same map validation tests
- `demo_minecraft_client.py` - Minecraft client demo

## Note

All tests should be run with the server running (unless they are unit tests that don't require server connection).
