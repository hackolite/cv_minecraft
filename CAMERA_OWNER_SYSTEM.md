# Camera Block User Object System

## Quick Start

This implementation adds camera block ownership and multi-camera recording control to the Minecraft client/server.

### For Players

1. **Place Camera Blocks**
   - Select camera block from inventory (press `5`)
   - Right-click to place the camera where you want to record

2. **Control Recording**
   - `F1` - Toggle recording for your first camera
   - `F2` - Toggle recording for your second camera
   - `Shift+F3` - Toggle recording for your third camera
   - `F9` - Toggle recording for main player view

3. **Find Recordings**
   - Recordings saved in `recordings/` directory
   - Each camera has its own subdirectory (e.g., `recordings/camera_5/`)
   - Sessions use timestamps for synchronization (e.g., `session_20231004_143025/`)

### For Developers

#### Server-Side Architecture

**Camera Ownership:**
```python
# When a player places a camera block
block_data = {
    "type": "camera",
    "collision": true,
    "block_id": "camera_5",
    "owner": "player_uuid_123"  # NEW: Tracks who placed it
}
```

**Camera Cubes:**
```python
# Each camera gets a Cube instance (like user cubes)
camera_cube = Cube(
    cube_id="camera_5",
    position=(75, 100, 70),
    cube_type="camera"
)
server.camera_cubes["camera_5"] = camera_cube
```

#### Client-Side Architecture

**Camera Tracking:**
```python
# Client maintains list of owned cameras
self.owned_cameras = ["camera_5", "camera_6"]  # block_ids

# Multiple recorders (one per camera)
self.camera_recorders = {
    "camera_5": GameRecorder(output_dir="recordings/camera_5"),
    "camera_6": GameRecorder(output_dir="recordings/camera_6")
}
```

**Recording Control:**
```python
def _toggle_camera_recording(camera_index):
    """Toggle recording for owned_cameras[camera_index]"""
    camera_id = self.owned_cameras[camera_index]
    recorder = self.camera_recorders.get(camera_id)
    recorder.start_recording()  # or stop_recording()
```

### API Changes

#### Camera List Response (Enhanced)
```json
{
  "type": "cameras_list",
  "data": {
    "cameras": [
      {
        "position": [75, 100, 70],
        "block_type": "camera",
        "block_id": "camera_5",
        "collision": true,
        "owner": "player_uuid_123"
      }
    ]
  }
}
```

### Directory Structure

```
recordings/
├── camera_5/
│   └── session_20231004_143025/
│       ├── frame_000001.jpg
│       ├── frame_000002.jpg
│       └── session_info.json
├── camera_6/
│   └── session_20231004_143025/  # Same timestamp for sync!
│       ├── frame_000001.jpg
│       └── session_info.json
└── session_20231004_143025/      # Main player view
    └── ...
```

### Key Files

- **server.py** - Camera ownership, camera_cubes dictionary, cleanup
- **minecraft_client_fr.py** - F1/F2/F3 key bindings, camera recorders
- **protocol.py** - create_block_data() now accepts owner parameter
- **BLOCK_METADATA_SYSTEM.md** - Detailed documentation
- **example_camera_owner_system.py** - Usage examples

### Testing

Run tests with:
```bash
# Start virtual display (headless environment)
Xvfb :99 -screen 0 1024x768x24 &

# Run tests
DISPLAY=:99 python3 tests/test_camera_owner.py
DISPLAY=:99 python3 tests/test_block_metadata.py
```

### Implementation Highlights

1. **Minimal Changes** - Reuses existing Cube/GameRecorder patterns
2. **Backward Compatible** - Existing cameras still work (owner=null)
3. **Clean Architecture** - Clear separation of concerns
4. **Well Tested** - Comprehensive test coverage
5. **Documented** - Examples and detailed docs

### Synchronization

All recordings started at the same time share the same timestamp:
- Format: `%Y%m%d_%H%M%S` (e.g., "20231004_143025")
- session_info.json contains exact start/end times
- Enables frame-accurate multi-camera video synchronization

## See Also

- `BLOCK_METADATA_SYSTEM.md` - Complete documentation
- `example_camera_owner_system.py` - Detailed usage examples
- `tests/test_camera_owner.py` - Test examples
