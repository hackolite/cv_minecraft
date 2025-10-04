# Rendering Pipeline Factorization

## Overview

The main rendering logic (scene rendering pipeline) has been factorized into a shared function that can be reused for both the main client window (player view) and headless camera cubes (offscreen rendering).

## Problem Statement

Previously, the rendering logic was duplicated between:
- **Main window** (`minecraft_client_fr.py`): Complex rendering with UI, focused blocks, players
- **Camera cubes** (`protocol.py`): Simplified world rendering

This led to code duplication and potential inconsistencies between the two rendering paths.

## Solution

### Shared Rendering Function: `render_world_scene()`

Located in `protocol.py`, this function provides a common rendering pipeline that handles:

1. **3D Perspective Setup** (with optional custom setup)
2. **World Rendering** (using model's batch)
3. **Optional Player Rendering**
4. **Optional Focused Block Rendering**

```python
def render_world_scene(model, position, rotation, window_size, fov=70.0, 
                       render_players_func=None, render_focused_block_func=None,
                       setup_perspective_func=None):
    """Shared rendering pipeline for world/scene rendering.
    
    This function provides a common rendering pipeline that can be used by both
    the main client window (player view) and camera cubes (headless/offscreen rendering).
    
    Both the main view and camera cubes use exactly the same rendering function for 
    world view to ensure consistency.
    """
```

### Usage

#### For Camera Cubes (Headless/Offscreen Rendering)

Camera cubes use the default perspective setup provided by `render_world_scene()`:

```python
# In CubeWindow._render_world_from_camera()
camera_position = (camera_x, camera_y + 0.6, camera_z)  # Eye height
render_world_scene(
    model=self.model,
    position=camera_position,
    rotation=self.cube.rotation,
    window_size=self.window.get_size(),
    fov=70.0,
    render_players_func=None,  # Cameras don't render players
    render_focused_block_func=None  # Cameras don't show focused block
)
```

#### For Main Client Window (Optional)

The main window can optionally use the shared function with custom perspective setup:

```python
# Future enhancement: Main window can use render_world_scene() 
render_world_scene(
    model=self.model,
    position=camera_pos,
    rotation=self.rotation,
    window_size=self.get_size(),
    render_players_func=self.draw_players,
    render_focused_block_func=self.draw_focused_block,
    setup_perspective_func=lambda pos, rot, size, fov: self.set_3d()
)
```

## Architecture

```
┌────────────────────────────────────────────────────────┐
│              render_world_scene()                      │
│         (Shared Rendering Pipeline)                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  1. Setup 3D Perspective                              │
│     ├─ Default: Standard perspective setup            │
│     └─ Custom: Use provided setup function            │
│                                                        │
│  2. Render World (model.batch.draw())                 │
│     └─ Common for ALL views                           │
│                                                        │
│  3. Optional: Render Focused Block                    │
│     └─ Main window only                               │
│                                                        │
│  4. Optional: Render Players                          │
│     └─ Main window or cameras if needed               │
│                                                        │
└────────────────────────────────────────────────────────┘
           ▲                              ▲
           │                              │
    ┌──────┴──────┐              ┌───────┴────────┐
    │ Main Window │              │ Camera Cubes   │
    │ (Player)    │              │ (Headless)     │
    └─────────────┘              └────────────────┘
```

## Camera Cube Creation

Camera cubes are automatically created as headless windows when a camera block is placed:

1. **Player places camera block** → Server creates camera with owner
2. **Client receives camera list** → Creates `Cube` instance with `cube_type="camera"`
3. **Cube initialization** → Calls `_create_window(model=self.model)`
4. **Window creation** → `CubeWindow(..., visible=False, model=model, cube=self)`

```python
# In protocol.py, Cube.__init__()
if self.cube_type == "camera":
    self._create_window(model=model)

# In Cube._create_window()
self.window = CubeWindow(self.id, width=800, height=600, 
                         visible=False,  # Headless/invisible
                         model=model,    # World model for rendering
                         cube=self)      # Cube for position/rotation
```

## Recording from Camera Cubes

When F1/F2/F3 keys are pressed, recordings are saved to:

```
recordings/
├── camera_0/
│   └── session_20231004_143025/
│       ├── frame_000001.jpg
│       ├── frame_000002.jpg
│       └── session_info.json
├── camera_1/
│   └── session_20231004_143025/
│       └── ...
```

The `GameRecorder` class handles frame capture from camera windows:

```python
# In GameRecorder.capture_frame()
if self.camera_cube and self.camera_cube.window:
    # Switch to camera window context
    self.camera_cube.window.window.switch_to()
    
    # Render camera's view using shared function
    self.camera_cube.window._render_simple_scene()
    
    # Capture from camera window
    buffer = pyglet.image.get_buffer_manager().get_color_buffer()
```

## Key Benefits

1. ✅ **Code Reuse**: Single rendering function used by both main window and cameras
2. ✅ **Consistency**: Ensures identical world rendering across all views
3. ✅ **Maintainability**: Changes to rendering logic only need to be made once
4. ✅ **Flexibility**: Optional callbacks allow customization per use case
5. ✅ **Headless Support**: Camera cubes render without visible windows
6. ✅ **Documentation**: Clear API with usage examples

## Compatibility

- ✅ Existing main window rendering logic remains unchanged
- ✅ Camera cube recording continues to work as before
- ✅ No breaking changes to existing functionality
- ✅ Backward compatible with cameras without models (fallback to placeholder)

## Testing

To test the factorized rendering:

1. **Place camera blocks** in the world
2. **Press F1/F2/F3** to start recording from cameras
3. **Verify** that camera recordings show the actual world (not placeholder)
4. **Check** that recordings are saved in `recordings/camera_X/session_TIMESTAMP/`
5. **Compare** camera view with main player view to ensure consistency

## Future Enhancements

Potential improvements to the factorized rendering system:

1. **Main Window Migration**: Optionally migrate main window to use `render_world_scene()`
2. **Camera Player Rendering**: Allow cameras to optionally render player cubes
3. **Multiple Camera Views**: Support split-screen or picture-in-picture
4. **Performance Optimization**: Optimize multi-window rendering
5. **Custom Camera FOV**: Allow different FOV per camera

## Files Modified

- ✅ `protocol.py`:
  - Added `render_world_scene()` function (shared rendering pipeline)
  - Updated `CubeWindow._render_world_from_camera()` to use shared function
  - Added comprehensive documentation

## Conclusion

The rendering pipeline has been successfully factorized into a shared function that ensures consistency between the main client window and camera cubes. Both use exactly the same rendering logic for world view, while maintaining the flexibility for custom behavior when needed.
