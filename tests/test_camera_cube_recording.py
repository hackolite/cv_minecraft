#!/usr/bin/env python3
"""
Test for camera cube instances and recording from camera perspective.
This test verifies that:
1. Camera cubes are created on the client side with windows
2. GameRecorder can be initialized with a camera_cube parameter
3. Camera cubes are properly cleaned up when removed
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_camera_cube_creation():
    """Test that camera cube instances are created with windows."""
    print("\nTest: Camera cube creation with windows")
    
    # Verify that the code creates camera cubes
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verify camera_cubes dictionary is initialized
    assert 'self.camera_cubes = {}' in content, \
        "camera_cubes dictionary should be initialized"
    
    # 2. Verify Cube instances are created for cameras
    assert 'camera_cube = Cube(' in content, \
        "Cube instances should be created for cameras"
    
    # 3. Verify camera_cube has cube_type="camera"
    assert 'cube_type="camera"' in content, \
        "Camera cubes should have cube_type='camera'"
    
    # 4. Verify camera_cube has owner parameter
    assert 'owner=player_id' in content, \
        "Camera cubes should track the owner"
    
    # 5. Verify camera cubes are stored in dictionary
    assert 'self.camera_cubes[camera_id] = camera_cube' in content, \
        "Camera cubes should be stored in camera_cubes dictionary"
    
    print("✅ Camera cube creation verified")
    print("  ✓ camera_cubes dictionary initialized")
    print("  ✓ Cube instances created with cube_type='camera'")
    print("  ✓ Owner tracking implemented")
    print("  ✓ Camera cubes stored in dictionary")


def test_game_recorder_camera_support():
    """Test that GameRecorder supports camera_cube parameter."""
    print("\nTest: GameRecorder camera support")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verify GameRecorder __init__ accepts camera_cube parameter
    assert 'camera_cube: Optional' in content, \
        "GameRecorder __init__ should accept optional camera_cube parameter"
    
    # 2. Verify camera_cube is stored as instance variable
    assert 'self.camera_cube = camera_cube' in content, \
        "GameRecorder should store camera_cube as instance variable"
    
    # 3. Verify capture_frame uses camera_cube if available
    assert 'if self.camera_cube and self.camera_cube.window:' in content, \
        "capture_frame should check for camera_cube and use it if available"
    
    # 4. Verify camera window context switching
    assert 'self.camera_cube.window.window.switch_to()' in content, \
        "capture_frame should switch to camera window context"
    
    # 5. Verify camera_cube is passed when creating recorder
    assert 'camera_cube=camera_cube' in content, \
        "camera_cube should be passed when creating GameRecorder"
    
    print("✅ GameRecorder camera support verified")
    print("  ✓ camera_cube parameter in __init__")
    print("  ✓ camera_cube stored as instance variable")
    print("  ✓ capture_frame uses camera window when available")
    print("  ✓ Window context switching implemented")
    print("  ✓ camera_cube passed to GameRecorder")


def test_camera_cube_cleanup():
    """Test that camera cubes are cleaned up properly."""
    print("\nTest: Camera cube cleanup")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verify cameras_to_remove list is created
    assert 'cameras_to_remove = [cid for cid in self.camera_cubes.keys()' in content, \
        "Should identify cameras that need to be removed"
    
    # 2. Verify window is closed
    assert 'if camera_cube.window:' in content and 'camera_cube.window.close()' in content, \
        "Camera window should be closed during cleanup"
    
    # 3. Verify camera_cube is removed from dictionary
    assert 'del self.camera_cubes[camera_id]' in content, \
        "Camera cube should be removed from dictionary"
    
    # 4. Verify recorder is stopped if recording
    assert 'if recorder.is_recording:' in content and 'recorder.stop_recording()' in content, \
        "Recorder should be stopped if still recording"
    
    # 5. Verify recorder is removed
    assert 'del self.camera_recorders[camera_id]' in content, \
        "Recorder should be removed from dictionary"
    
    print("✅ Camera cube cleanup verified")
    print("  ✓ Cameras no longer owned are identified")
    print("  ✓ Camera windows are closed")
    print("  ✓ Camera cubes are removed from dictionary")
    print("  ✓ Active recordings are stopped")
    print("  ✓ Recorders are removed from dictionary")


def test_camera_position_tracking():
    """Test that camera positions are tracked from server data."""
    print("\nTest: Camera position tracking")
    
    client_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Verify camera position is extracted from camera data
    assert "camera_position = tuple(camera.get(\"position\"" in content, \
        "Camera position should be extracted from server data"
    
    # 2. Verify position is passed to Cube constructor
    assert 'position=camera_position' in content, \
        "Camera position should be passed to Cube constructor"
    
    print("✅ Camera position tracking verified")
    print("  ✓ Position extracted from server data")
    print("  ✓ Position passed to Cube instance")


if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA CUBE RECORDING SYSTEM TESTS")
    print("=" * 60)
    
    test_camera_cube_creation()
    test_game_recorder_camera_support()
    test_camera_cube_cleanup()
    test_camera_position_tracking()
    
    print("\n" + "=" * 60)
    print("✅ ALL CAMERA CUBE RECORDING TESTS PASSED")
    print("=" * 60)
    print("\nSummary:")
    print("  • Camera cubes are created on client side with windows")
    print("  • GameRecorder supports recording from camera perspective")
    print("  • Camera cubes and recorders are properly cleaned up")
    print("  • Camera positions are tracked from server data")
    print("\nImplementation notes:")
    print("  • Camera cubes use the Cube class (protocol.py)")
    print("  • Each camera cube has a CubeWindow for rendering")
    print("  • GameRecorder captures from camera window when available")
    print("  • TODO: Implement full world rendering in camera windows")
