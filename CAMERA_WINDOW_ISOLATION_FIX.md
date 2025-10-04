# Camera Window Isolation Fix

## Issue (French)
> vérifie bien que chaque caméra enregistrer sa propre windows et pas la windows de l'utilisateur originel

## Translation
Verify that each camera records its own window and not the original user's window.

## Problem
When cameras were recording, they were being passed the main player window in the `capture_frame()` call. While the implementation had logic to use `camera_cube.window` when available, passing the main window parameter was unnecessary and could lead to confusion or potential issues.

## Solution

### Code Changes

#### 1. Made window parameter optional in `GameRecorder.capture_frame()`

**Before:**
```python
def capture_frame(self, window):
    """Capture une frame depuis le buffer Pyglet.
    
    Args:
        window: La fenêtre Pyglet dont on veut capturer le buffer (peut être ignoré si camera_cube est défini)
    """
```

**After:**
```python
def capture_frame(self, window=None):
    """Capture une frame depuis le buffer Pyglet.
    
    Args:
        window: La fenêtre Pyglet dont on veut capturer le buffer (peut être ignoré si camera_cube est défini)
    """
```

#### 2. Camera recorders no longer receive the main window

**Before:**
```python
# In on_draw()
# Capture frames pour toutes les caméras en enregistrement
for camera_id, recorder in self.camera_recorders.items():
    if recorder.is_recording:
        recorder.capture_frame(self)  # ❌ Passing main window
```

**After:**
```python
# In on_draw()
# Capture frames pour toutes les caméras en enregistrement
for camera_id, recorder in self.camera_recorders.items():
    if recorder.is_recording:
        recorder.capture_frame()  # ✅ Camera uses its own window, not main window
```

#### 3. Player recorder still receives the main window

```python
# Capture frame si enregistrement actif
if self.recorder and self.recorder.is_recording:
    self.recorder.capture_frame(self)  # ✅ Player uses main window
```

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        on_draw()                            │
│                                                             │
│  Player Recording:                                          │
│  ┌───────────────────────────────────┐                     │
│  │ self.recorder.capture_frame(self) │                     │
│  │         ↓                          │                     │
│  │   Uses main window                │                     │
│  └───────────────────────────────────┘                     │
│                                                             │
│  Camera Recording:                                          │
│  ┌──────────────────────────────────────────────┐          │
│  │ for camera_id, recorder in camera_recorders: │          │
│  │     recorder.capture_frame()                 │          │
│  │         ↓                                     │          │
│  │   Uses camera_cube.window                    │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Window Context Flow

#### Player Recording
```
on_draw() → capture_frame(main_window)
                ↓
           Use main window buffer
                ↓
           Capture from main window context
```

#### Camera Recording
```
on_draw() → capture_frame()  # No window passed
                ↓
           Check: self.camera_cube.window exists?
                ↓
           YES: Switch to camera_cube.window context
                ↓
           Render camera's scene
                ↓
           Capture from camera window buffer
                ↓
           Restore main window context (if provided)
```

## Verification

### Test Coverage

1. **test_camera_window_isolation.py** (NEW)
   - ✅ Verifies `window` parameter is optional
   - ✅ Verifies cameras call `capture_frame()` without window
   - ✅ Verifies player calls `capture_frame(self)` with window
   - ✅ Verifies camera uses `camera_cube.window` context
   - ✅ Verifies window context isolation

2. **test_camera_cube_recording.py**
   - ✅ Camera cubes created with windows
   - ✅ GameRecorder supports camera_cube parameter
   - ✅ Camera cleanup properly handles windows

3. **test_camera_recording_integration.py**
   - ✅ Full integration workflow
   - ✅ Multiple cameras can record simultaneously
   - ✅ Proper frame capture for all recorders

4. **test_camera_recording_fix.py**
   - ✅ Camera recorders start/stop correctly
   - ✅ on_draw contains capture logic for cameras

## Benefits

### ✅ Complete Window Isolation
Each camera now uses its dedicated `camera_cube.window` for rendering and capture, completely isolated from the main player window.

### ✅ Clear Intent
The code clearly shows the difference:
- Player: `recorder.capture_frame(self)` - uses main window
- Camera: `recorder.capture_frame()` - uses camera's own window

### ✅ Proper Context Management
The window context switching logic is properly encapsulated in `capture_frame()`:
```python
if self.camera_cube and self.camera_cube.window:
    # Switch to camera window
    self.camera_cube.window.window.switch_to()
    
    # Render camera's view
    self.camera_cube.window._render_simple_scene()
    
    # Capture from camera window buffer
    buffer = pyglet.image.get_buffer_manager().get_color_buffer()
    # ...
    
    # Restore main window context if needed
    if window and hasattr(window, 'switch_to'):
        window.switch_to()
```

### ✅ Multiple Simultaneous Recordings
Multiple cameras can record independently, each from its own window:
- Camera 1 records from `camera_cube_1.window`
- Camera 2 records from `camera_cube_2.window`
- Player records from main `MinecraftWindow`

## File Changes

```
modified:   minecraft_client_fr.py
  - Line 715: def capture_frame(self, window=None)
  - Line 1666: recorder.capture_frame()  # Camera uses its own window

modified:   tests/test_camera_recording_fix.py
  - Updated test to check for both player and camera capture patterns

modified:   tests/test_camera_recording_integration.py
  - Updated test to check for both player and camera capture patterns

new file:   tests/test_camera_window_isolation.py
  - Comprehensive test validating window isolation
```

## Conclusion

This fix ensures that **each camera records its own window (`camera_cube.window`)** and **not the original user's window (`MinecraftWindow`)**. The implementation is clean, well-tested, and maintains backward compatibility with player recording while properly isolating camera recordings.

---

**Status:** ✅ **FIXED AND VERIFIED**

All tests pass, confirming that:
- ✅ Each camera uses its own dedicated window
- ✅ Window contexts are properly isolated
- ✅ Multiple cameras can record simultaneously
- ✅ Player recording remains unaffected
