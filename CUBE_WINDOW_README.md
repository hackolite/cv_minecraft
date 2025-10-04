# Cube Window Abstraction System

## Overview

This system implements a window abstraction for cubes in the Minecraft server, where each cube can optionally have its own pyglet window. This is particularly useful for camera-type cubes that need to provide visual output and screenshot capabilities.

## Features

✅ **Window Abstraction**: Each cube can have an optional pyglet window  
✅ **Camera Type Cubes**: Cubes with `cube_type="camera"` automatically get windows  
✅ **World Rendering**: Camera cubes render the actual world from their perspective  
✅ **Screenshot API**: Camera cubes provide `/camera/image` endpoint returning PNG images  
✅ **Headless Compatibility**: Works without display using dummy classes  
✅ **Resource Management**: Automatic window cleanup when cubes are destroyed  
✅ **Child Cube Support**: Child cubes can also be camera types with their own windows  

## Architecture

### Components

1. **CubeWindow Class** (`protocol.py`)
   - Manages individual pyglet windows for cubes
   - Handles OpenGL rendering and screenshot capture
   - Renders actual world from camera's perspective when model is provided
   - Provides fallback placeholder rendering when model is not available
   - Provides fallback dummy implementation for headless environments

2. **Enhanced Cube Class** (`protocol.py`)
   - Added `cube_type` parameter to distinguish cube types
   - Added `model` parameter to enable world rendering
   - Added `window` attribute for window abstraction
   - Automatic window creation for camera-type cubes
   - Enhanced API endpoints with camera functionality

3. **API Endpoints**
   - Enhanced cube creation with `cube_type` parameter
   - `/camera/image` endpoint returns actual PNG screenshots
   - Cube info includes window status and type information

## Usage Examples

### Creating Camera Cubes

```python
from protocol import Cube
from minecraft_client_fr import EnhancedClientModel

# Create a world model
model = EnhancedClientModel()

# Create a normal cube (no window)
normal_cube = Cube("normal_1", (10, 50, 10), cube_type="normal")

# Create a camera cube with placeholder rendering (no model)
camera_cube = Cube("camera_1", (20, 50, 20), cube_type="camera")

# Create a camera cube with world rendering (with model)
camera_with_world = Cube("camera_2", (30, 50, 30), cube_type="camera", model=model)
```

### API Usage

```bash
# Create a camera cube via API
curl -X POST 'http://localhost:8081/cubes/create?child_id=camera1&cube_type=camera'

# Get screenshot from camera cube
curl http://localhost:8082/camera/image -o screenshot.png

# Get cube information (includes window status)
curl http://localhost:8082/
```

### Response Examples

**Normal Cube Info:**
```json
{
  "cube_id": "normal_1",
  "cube_type": "normal",
  "has_window": false,
  "position": [10, 50, 10],
  "status": "active"
}
```

**Camera Cube Info:**
```json
{
  "cube_id": "camera_1", 
  "cube_type": "camera",
  "has_window": true,
  "position": [20, 50, 20],
  "status": "active"
}
```

**Camera Image Request:**
- Success: Returns PNG image data (Content-Type: image/png)
- Error: Returns JSON with error details

## Implementation Details

### Window Creation

Camera-type cubes automatically create a `CubeWindow` instance with optional model for world rendering:

```python
def _create_window(self, model=None):
    """Create a pyglet window for this cube (used for camera-type cubes).
    
    Args:
        model: Optional world model to render from camera's perspective
    """
    try:
        self.window = CubeWindow(self.id, width=800, height=600, visible=False, model=model, cube=self)
        print(f"✅ Created window for {self.cube_type} cube {self.id}")
    except Exception as e:
        print(f"⚠️  Failed to create window for cube {self.id}: {e}")
        self.window = None
```

### World Rendering

The `CubeWindow` now supports rendering the actual world from the camera's perspective:

1. **With Model** - `_render_world_from_camera()`:
   - Sets up 3D perspective using camera's FOV (70 degrees)
   - Applies camera's rotation (horizontal and vertical)
   - Positions camera at cube's position (with eye height offset)
   - Renders the world using the model's batch

2. **Without Model** - `_render_placeholder_cube()`:
   - Falls back to rendering a simple colored cube
   - Used when model is not provided (e.g., on server side)

The rendering method is automatically selected in `_render_simple_scene()`:

```python
def _render_simple_scene(self):
    """Render the world from the cube's perspective."""
    if self.model and self.cube:
        self._render_world_from_camera()  # Render actual world
    else:
        self._render_placeholder_cube()   # Fallback to placeholder
```

### Screenshot Capture

The `CubeWindow.take_screenshot()` method:
1. Switches to the window's OpenGL context
2. Renders the scene (world or placeholder) using `_render_simple_scene()`
3. Reads pixels from the framebuffer
4. Converts to PNG format using PIL

### Resource Management

Windows are automatically cleaned up when cubes are destroyed:

```python
async def stop_server(self):
    """Stop the FastAPI server for this cube."""
    # ... existing cleanup ...
    
    # Clean up window if it exists
    if self.window:
        self.window.close()
        self.window = None
```

## Environment Setup

### With Display (Full Functionality)

```bash
# Install required system libraries
sudo apt-get install libglu1-mesa libglu1-mesa-dev freeglut3-dev

# Run with display
python demo_cube_window.py
```

### Headless Environment (Limited Functionality)

```bash
# Using Xvfb virtual display
DISPLAY=:99 xvfb-run -a python demo_cube_window.py

# Pure headless (no screenshots)
python demo_cube_window.py
```

## Testing

### Basic Tests

```bash
# Test window creation and API
DISPLAY=:99 xvfb-run -a python test_cube_window.py

# Test integration with existing cube system  
DISPLAY=:99 xvfb-run -a python test_cube_system.py
```

### Demo

```bash
# Interactive demo showing all features
DISPLAY=:99 xvfb-run -a python demo_cube_window.py
```

## API Reference

### Enhanced Cube Creation

**Endpoint:** `POST /cubes/create`

**Parameters:**
- `child_id` (string): ID for the new cube
- `x`, `y`, `z` (float): Position coordinates  
- `cube_type` (string): Cube type ("normal" or "camera")

**Response:**
```json
{
  "message": "Child cube camera1 created",
  "child_cube": {
    "id": "camera1",
    "position": [30.0, 50.0, 30.0],
    "port": 8083,
    "cube_type": "camera"
  }
}
```

### Camera Image Endpoint

**Endpoint:** `GET /camera/image`

**Success Response:**
- Content-Type: `image/png`
- Body: PNG image data

**Error Responses:**
```json
// Not a camera cube
{
  "error": "Not a camera cube",
  "message": "Cube type 'normal' does not support camera images"
}

// Window not available
{
  "error": "Camera window not available", 
  "message": "Window failed to initialize"
}

// Screenshot failed
{
  "error": "Screenshot failed",
  "message": "Failed to capture image from cube window"
}
```

### Enhanced Cube Info

**Endpoint:** `GET /`

**Response includes new fields:**
- `cube_type`: Type of cube ("normal", "camera", etc.)
- `has_window`: Boolean indicating if cube has a window

## Troubleshooting

### Common Issues

1. **"Library GLU not found"**
   ```bash
   sudo apt-get install libglu1-mesa libglu1-mesa-dev
   ```

2. **"No display available"**
   ```bash
   # Use virtual display
   DISPLAY=:99 xvfb-run -a python your_script.py
   ```

3. **"Screenshot failed"**
   - Check if pyglet and OpenGL are properly installed
   - Ensure display environment is available
   - Check cube type is "camera"

### Debug Output

The system provides comprehensive logging:
- ✅ Success operations
- ⚠️  Warnings and fallbacks
- ❌ Error conditions

## Future Enhancements

- [ ] Integration with actual Minecraft world rendering
- [ ] Custom rendering pipelines for different cube types
- [ ] Real-time streaming endpoints
- [ ] Camera positioning and orientation control
- [ ] Multiple rendering modes (wireframe, textured, etc.)
- [ ] Performance optimization for multiple camera cubes