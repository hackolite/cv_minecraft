# Camera View Fix - Quick Reference Guide

## What Was Fixed?

✅ Cameras now generate views from their own position and rotation (not from the player)
✅ Screenshots are automatically saved to `recordings/{camera_id}/` directory
✅ Comprehensive logging shows which camera is being used

## How to Use

### 1. Generate a Screenshot from a Camera

```bash
# Generate screenshot from first available camera
python3 generate_camera_screenshot.py

# Generate from specific camera (recommended)
python3 generate_camera_screenshot.py --camera-id camera_0

# With custom rotation
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 45 -10
```

**Output**: `recordings/camera_0/screenshot_20251004_184206.png`

### 2. Query Camera View Data

```bash
# Query view data from a specific camera
python3 camera_view_query.py --camera-id camera_0 --output cam0_data.json

# Generate screenshot from the data
python3 camera_view_reconstruction.py --input cam0_data.json --output cam0_view.png
```

### 3. Record from Client

In the Minecraft client (`minecraft_client_fr.py`):

1. Press `5` to select the camera block
2. Right-click to place a camera
3. Press `F1` to start/stop recording from camera 0
4. Press `F2` to start/stop recording from camera 1 (if you have multiple cameras)

**Output**: `recordings/camera_X/session_YYYYMMDD_HHMMSS/frame_000001.jpg`

## Diagnostic Logs

When you run camera operations, you'll see helpful logs:

```
📸 Taking screenshot from camera cube: camera_0
   Position: (100, 50, 75)
   Rotation: (45, -15)
🎥 Rendering from camera position (100, 50, 75) with rotation (45, -15)
✅ Screenshot captured successfully from camera camera_0

📷 Using camera: camera_0
💾 Output will be saved to camera directory: recordings/camera_0/screenshot_20251004_184206.png
📁 Screenshot saved in camera directory: recordings/camera_0/screenshot_20251004_184206.png
```

These logs confirm:
- Which camera is being used (camera_0)
- The camera's position in the world (100, 50, 75)
- The camera's rotation (45° horizontal, -15° vertical)
- Where the screenshot is saved

## File Organization

```
cv_minecraft/
└── recordings/
    ├── camera_0/           # Camera 0's folder
    │   ├── screenshot_20251004_184206.png
    │   ├── screenshot_20251004_185432.png
    │   └── session_20251004_190000/
    │       ├── frame_000001.jpg
    │       ├── frame_000002.jpg
    │       └── session_info.json
    ├── camera_1/           # Camera 1's folder
    │   └── ...
    └── camera_2/           # Camera 2's folder
        └── ...
```

## Verify the Fix Works

Run the included tests:

```bash
# Test cube window integration
python3 tests/test_camera_view_fix.py

# Test camera view generation
python3 tests/test_camera_view_integration.py
```

Both should show:
```
✅ ALL TESTS PASSED!
```

## Common Scenarios

### Scenario 1: Multiple Cameras at Different Positions

```bash
# Camera 0 at position (100, 50, 75)
python3 generate_camera_screenshot.py --camera-id camera_0

# Camera 1 at position (200, 60, 150)
python3 generate_camera_screenshot.py --camera-id camera_1
```

Result:
- `recordings/camera_0/screenshot_TIMESTAMP.png` shows view from (100, 50, 75)
- `recordings/camera_1/screenshot_TIMESTAMP.png` shows view from (200, 60, 150)

### Scenario 2: Time-lapse from Same Camera

```bash
# Take multiple screenshots over time
python3 generate_camera_screenshot.py --camera-id camera_0
# Wait 1 minute
python3 generate_camera_screenshot.py --camera-id camera_0
# Wait 1 minute
python3 generate_camera_screenshot.py --camera-id camera_0
```

Result:
```
recordings/camera_0/
├── screenshot_20251004_100000.png
├── screenshot_20251004_100100.png
└── screenshot_20251004_100200.png
```

### Scenario 3: Different Rotations from Same Camera

```bash
# View north (rotation 0, 0)
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 0 0

# View east (rotation 90, 0)
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 90 0

# View south (rotation 180, 0)
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 180 0

# View west (rotation 270, 0)
python3 generate_camera_screenshot.py --camera-id camera_0 --rotation 270 0
```

Each screenshot will be from the same camera position but looking in a different direction.

## Troubleshooting

### Issue: No screenshots being saved

**Check**: Look for log messages like:
```
📷 Using camera: camera_X
💾 Output will be saved to camera directory: recordings/camera_X/screenshot_TIMESTAMP.png
```

If you don't see these, the camera might not exist or the script failed to query it.

### Issue: Screenshots all look the same

**Check**: Look for log messages like:
```
🎥 Rendering from camera position (X, Y, Z) with rotation (H, V)
```

This confirms the camera position and rotation are being used. If you see:
```
🎥 Rendering from default position (no cube reference)
```

Then the camera doesn't have position/rotation data (this is a fallback for compatibility).

### Issue: Screenshots overwriting each other

**Solution**: Use the default filename (screenshot.png) without specifying a custom output path. The script will automatically add timestamps:
```bash
# Good - auto-timestamped
python3 generate_camera_screenshot.py --camera-id camera_0

# Bad - will overwrite
python3 generate_camera_screenshot.py --camera-id camera_0 --output my_screenshot.png
```

## Technical Details

For implementation details, see:
- `CAMERA_VIEW_FIX.md` - Complete technical documentation
- `CAMERA_VIEW_FIX_BEFORE_AFTER.md` - Before/after comparison

For code documentation:
- `protocol.py` - CubeWindow implementation with camera position/rotation
- `generate_camera_screenshot.py` - Screenshot generation with automatic directory creation
- `camera_view_reconstruction.py` - View rendering from camera perspective
