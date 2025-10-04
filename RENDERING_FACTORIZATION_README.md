# Rendering Pipeline Factorization - Quick Start

## What Was Done

Factorized the main rendering logic into a shared function (`render_world_scene()`) that can be reused for both:
- **Main client window** (player view)
- **Headless camera cubes** (offscreen rendering for recordings)

## Key Changes

### 1. protocol.py
- Added `render_world_scene()` function (112 new lines)
- Updated `CubeWindow._render_world_from_camera()` to use shared function
- Enhanced documentation

### 2. Documentation
- `RENDERING_PIPELINE_FACTORIZATION.md` - Full documentation
- `RENDERING_FACTORIZATION_SUMMARY.md` - Implementation summary
- This README - Quick start guide

### 3. Testing
- `tests/test_factorized_rendering.py` - 5 test cases (all passing)
- `demo_factorized_rendering.py` - Working demo

## How It Works

### Before (Duplicated Logic)
```
Main Window                Camera Cubes
    ↓                          ↓
set_3d() + batch.draw()   Custom rendering code
```

### After (Shared Function)
```
Main Window                Camera Cubes
    ↓                          ↓
        render_world_scene()
                ↓
    Shared rendering pipeline
```

## Usage

### For Camera Cubes (Automatic)
Camera cubes automatically use the shared function:
```python
# Camera cube created with model
camera = Cube(
    cube_id="camera_1",
    position=(10, 50, 10),
    cube_type="camera",
    model=world_model  # Passed to enable world rendering
)

# Window automatically created (headless)
# Rendering uses shared function automatically
```

### Recording from Cameras
```
F1 → Camera 0 recording → recordings/camera_0/session_TIMESTAMP/
F2 → Camera 1 recording → recordings/camera_1/session_TIMESTAMP/
F3 → Camera 2 recording → recordings/camera_2/session_TIMESTAMP/
```

## Running Tests

```bash
# Run factorized rendering tests
python3 tests/test_factorized_rendering.py

# Run demo
python3 demo_factorized_rendering.py
```

## Benefits

✅ **Code Reuse**: Single rendering function eliminates duplication  
✅ **Consistency**: Both main window and cameras use same logic  
✅ **Maintainability**: Changes only need to be made once  
✅ **Flexibility**: Optional callbacks for customization  
✅ **Testing**: Easy to verify both paths use same logic  

## Backward Compatibility

- ✅ Existing main window rendering unchanged
- ✅ Camera cube recording continues to work  
- ✅ No breaking changes
- ✅ All existing tests still pass

## Documentation

For more details, see:
- `RENDERING_PIPELINE_FACTORIZATION.md` - Complete documentation
- `RENDERING_FACTORIZATION_SUMMARY.md` - Implementation details
- `protocol.py` - Inline code documentation

## Verification

All requirements met:
- [x] Main scene rendering extracted into shared function
- [x] Function can be used by both main window and camera cubes
- [x] Camera cubes render world from their perspective
- [x] Both use exactly the same rendering function
- [x] Headless camera cubes created on camera block placement
- [x] Screenshots saved to recordings/camera_X/session_TIMESTAMP/
- [x] Comprehensive documentation added
- [x] Tests created and passing
- [x] Existing functionality preserved
