# Fix: Camera White Areas - glFlush vs glFinish

## Problem Statement
"il y a encore des grandes parties blanches, et l' update ne m'a pas l'air super"
(There are still large white areas, and the update doesn't look very good)

## Previous State
The code was using `glFlush()` after rendering and before capturing the framebuffer:
```python
self.camera_cube.window._render_simple_scene()
glFlush()  # ⚠️ Only schedules execution
buffer = get_color_buffer()
```

This was an improvement over having no synchronization, but it wasn't sufficient.

## The Issue
`glFlush()` and `glFinish()` serve different purposes in OpenGL:

### glFlush()
- **Purpose**: Ensures commands are sent to the GPU for execution
- **Behavior**: Returns immediately after scheduling commands
- **Guarantee**: Commands will start executing "soon"
- **Use case**: When you want to ensure commands are in the pipeline but don't need to wait

### glFinish()
- **Purpose**: Ensures ALL commands are COMPLETELY executed
- **Behavior**: Blocks until every command is fully finished
- **Guarantee**: When it returns, ALL rendering is 100% complete
- **Use case**: When you need to read back results (like framebuffer reads)

## Why This Matters for Framebuffer Reads
When capturing camera images, we need to:
1. Render the scene
2. Read the framebuffer to get the pixels
3. Save/process those pixels

If we use `glFlush()`:
- Commands are scheduled but may not be finished
- Framebuffer read happens before rendering completes
- Result: Incomplete rendering, white areas, artifacts

If we use `glFinish()`:
- Code blocks until ALL rendering is done
- Framebuffer read gets complete, fully-rendered image
- Result: Clean, complete images

## The Fix
Changed from `glFlush()` to `glFinish()` in two locations:

### minecraft_client_fr.py (GameRecorder.capture_frame)
```python
self.camera_cube.window._render_simple_scene()

# Force finish to ensure ALL rendering is complete before capturing
# glFinish() blocks until all OpenGL commands are fully executed
# This prevents capturing white/incomplete images
glFinish()

buffer = pyglet.image.get_buffer_manager().get_color_buffer()
```

### protocol.py (CubeWindow.take_screenshot)
```python
self._render_simple_scene()

# Force finish to ensure ALL rendering is complete
# glFinish() blocks until all OpenGL commands are fully executed
# This prevents capturing white/incomplete images
glFinish()

pixels = glReadPixels(...)
```

## Impact
- **Performance**: Slightly slower (blocks until rendering complete) but necessary for correctness
- **Image Quality**: Eliminates white areas and incomplete rendering
- **Reliability**: Guarantees that captured images show complete, fully-rendered scenes

## Testing
Updated test file `tests/test_camera_buffer_flush.py` to verify:
1. ✅ `glFinish()` is called after rendering
2. ✅ `glFinish()` is called before buffer capture
3. ✅ Proper comments explain why `glFinish()` is used
4. ✅ Complete workflow is correct

## OpenGL Documentation References
From the OpenGL specification:

**glFlush**:
> "Different GL implementations buffer commands in several different locations, including network buffers and the graphics accelerator itself. glFlush empties all of these buffers, causing all issued commands to be executed as quickly as they are accepted by the actual rendering engine."

**glFinish**:
> "glFinish does not return until the effects of all previously called GL commands are complete. Such effects include all changes to GL state, all changes to connection state, and all changes to the frame buffer contents."

The key difference: **glFlush** ensures commands are sent, **glFinish** ensures they are **complete**.

## Conclusion
For any operation that reads back OpenGL state (like framebuffer reads for screenshots or video capture), `glFinish()` is the correct synchronization primitive. It guarantees that what you read is the complete, fully-rendered result.

This is a minimal but critical change that ensures camera images are always complete and free of white areas or rendering artifacts.
