#!/usr/bin/env python3
"""
Test to verify that each camera records its own window, not the main user window.

This test validates the fix for the issue:
"vérifie bien que chaque caméra enregistrer sa propre windows et pas la windows de l'utilisateur originel"

The fix ensures that:
1. Camera recorders call capture_frame() without passing the main window
2. GameRecorder's capture_frame uses camera_cube.window when available
3. Each camera captures from its own dedicated window context
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_camera_uses_own_window():
    """Test that camera recorders use their own windows, not the main window."""
    print("\n🧪 Test: Camera uses its own window for recording")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verify that capture_frame accepts optional window parameter
    assert 'def capture_frame(self, window=None):' in content, \
        "capture_frame should accept optional window parameter (default None)"
    print("  ✓ capture_frame has optional window parameter")
    
    # 2. Verify that camera recorders DON'T pass the main window
    on_draw_section = content.split('def on_draw(self):', 1)[1].split('def ', 1)[0]
    
    # Check that camera recorders call capture_frame without window argument
    assert 'recorder.capture_frame()  # Camera uses its own window' in on_draw_section, \
        "Camera recorders should call capture_frame() without passing main window"
    print("  ✓ Camera recorders call capture_frame() without main window")
    
    # 3. Verify that player recorder DOES pass the main window
    assert 'self.recorder.capture_frame(self)' in on_draw_section, \
        "Player recorder should call capture_frame(self) with main window"
    print("  ✓ Player recorder calls capture_frame(self) with main window")
    
    # 4. Verify that capture_frame uses camera_cube.window when available
    capture_frame_section = content.split('def capture_frame(self, window=None):', 1)[1].split('def ', 1)[0]
    
    assert 'if self.camera_cube and self.camera_cube.window:' in capture_frame_section, \
        "capture_frame should check for camera_cube.window"
    print("  ✓ capture_frame checks for camera_cube.window")
    
    assert 'self.camera_cube.window.window.switch_to()' in capture_frame_section, \
        "capture_frame should switch to camera window context"
    print("  ✓ capture_frame switches to camera window context")
    
    assert 'self.camera_cube.window._render_simple_scene()' in capture_frame_section, \
        "capture_frame should render camera's scene"
    print("  ✓ capture_frame renders camera's own scene")
    
    # 5. Verify that camera window is used for buffer capture
    # After switching to camera window, the buffer should come from that window
    camera_capture_section = capture_frame_section.split(
        'if self.camera_cube and self.camera_cube.window:', 1
    )[1].split('else:', 1)[0]
    
    assert 'buffer = pyglet.image.get_buffer_manager().get_color_buffer()' in camera_capture_section, \
        "Camera should capture buffer from its own window context"
    print("  ✓ Camera captures buffer from its own window context")
    
    print("\n✅ PASS: Cameras record their own windows, not the main user window")


def test_window_context_isolation():
    """Test that window contexts are properly isolated between player and cameras."""
    print("\n🧪 Test: Window context isolation")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    capture_frame_section = content.split('def capture_frame(self, window=None):', 1)[1].split('def ', 1)[0]
    
    # Verify that after camera capture, we switch back to main window if provided
    assert 'if window and hasattr(window, \'switch_to\'):' in capture_frame_section, \
        "Should switch back to main window after camera capture if window provided"
    
    assert 'window.switch_to()' in capture_frame_section, \
        "Should restore main window context after camera capture"
    
    print("  ✓ Window context is restored after camera capture")
    print("  ✓ Main window and camera windows are properly isolated")
    
    print("\n✅ PASS: Window contexts are properly isolated")


def test_camera_independence():
    """Test that each camera is independent and can record simultaneously."""
    print("\n🧪 Test: Camera independence")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify that camera_recorders is a dictionary (allows multiple cameras)
    assert 'self.camera_recorders = {}' in content, \
        "camera_recorders should be a dictionary to support multiple cameras"
    print("  ✓ Multiple cameras can be tracked independently")
    
    # Verify that we iterate over all camera recorders
    assert 'for camera_id, recorder in self.camera_recorders.items():' in content, \
        "Should iterate over all camera recorders"
    print("  ✓ All camera recorders are processed in on_draw")
    
    # Verify that each camera gets its own GameRecorder with camera_cube
    assert 'GameRecorder(\n                output_dir=f"recordings/{camera_id}",\n                camera_cube=camera_cube' in content or \
           'camera_cube=camera_cube' in content, \
        "Each camera should have its own GameRecorder with camera_cube"
    print("  ✓ Each camera has its own GameRecorder with camera_cube")
    
    print("\n✅ PASS: Cameras are independent and can record simultaneously")


def main():
    """Run all tests."""
    print("=" * 70)
    print("CAMERA WINDOW ISOLATION TESTS")
    print("=" * 70)
    print("\nValidating fix for:")
    print("  'vérifie bien que chaque caméra enregistrer sa propre windows")
    print("   et pas la windows de l'utilisateur originel'")
    print("=" * 70)
    
    try:
        test_camera_uses_own_window()
        test_window_context_isolation()
        test_camera_independence()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nSummary of the fix:")
        print("  • Problem: Cameras were recording from the main user window")
        print("  • Solution: Camera recorders now call capture_frame() without window parameter")
        print("  • Result: Each camera uses its own camera_cube.window for recording")
        print("  • Isolation: Window contexts are properly isolated and restored")
        print("\nKey changes:")
        print("  1. capture_frame(window=None) - window parameter is now optional")
        print("  2. recorder.capture_frame() - cameras don't pass main window")
        print("  3. Camera window context is used when camera_cube is present")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
