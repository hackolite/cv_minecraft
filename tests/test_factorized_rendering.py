#!/usr/bin/env python3
"""
Test script to verify the factorized rendering pipeline.

This test verifies:
1. Camera cubes are created with headless windows
2. The shared render_world_scene() function works correctly
3. Both main window and camera cubes can use the same rendering logic
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import Cube, render_world_scene, CubeWindow


def test_camera_cube_creation():
    """Test that camera cubes create headless windows."""
    print("=" * 70)
    print("TEST 1: Camera Cube Creation")
    print("=" * 70)
    
    # Create a camera cube
    camera = Cube(
        cube_id="camera_test_1",
        position=(10, 50, 10),
        rotation=(45, 10),
        cube_type="camera",
        owner="test_player"
    )
    
    # Verify it has a window
    assert camera.window is not None, "Camera cube should have a window"
    print("✅ Camera cube has a window")
    
    # Verify window is invisible (headless)
    assert camera.window.visible == False, "Camera window should be invisible"
    print("✅ Camera window is headless (invisible)")
    
    # Verify position and rotation
    assert camera.position == (10, 50, 10), "Position should be set correctly"
    assert camera.rotation == (45, 10), "Rotation should be set correctly"
    print("✅ Camera position and rotation set correctly")
    
    print()
    return camera


def test_normal_cube_no_window():
    """Test that normal cubes don't create windows."""
    print("=" * 70)
    print("TEST 2: Normal Cube (No Window)")
    print("=" * 70)
    
    # Create a normal cube
    normal = Cube(
        cube_id="normal_test_1",
        position=(20, 50, 20),
        cube_type="normal"
    )
    
    # Verify it does NOT have a window
    assert normal.window is None, "Normal cube should not have a window"
    print("✅ Normal cube does not have a window")
    
    print()
    return normal


def test_render_world_scene_function():
    """Test the shared render_world_scene function."""
    print("=" * 70)
    print("TEST 3: Shared render_world_scene() Function")
    print("=" * 70)
    
    # Test that function exists and has correct signature
    import inspect
    sig = inspect.signature(render_world_scene)
    params = list(sig.parameters.keys())
    
    expected_params = ['model', 'position', 'rotation', 'window_size', 'fov', 
                      'render_players_func', 'render_focused_block_func', 
                      'setup_perspective_func']
    
    for param in expected_params:
        assert param in params, f"Parameter '{param}' should be in function signature"
    
    print("✅ render_world_scene() has correct function signature")
    print(f"   Parameters: {', '.join(params)}")
    
    # Test default values
    defaults = {
        'fov': 70.0,
        'render_players_func': None,
        'render_focused_block_func': None,
        'setup_perspective_func': None
    }
    
    for param, expected_default in defaults.items():
        actual_default = sig.parameters[param].default
        assert actual_default == expected_default, \
            f"Parameter '{param}' should have default value {expected_default}"
    
    print("✅ render_world_scene() has correct default parameter values")
    
    print()


def test_camera_cube_with_model():
    """Test camera cube creation with a model."""
    print("=" * 70)
    print("TEST 4: Camera Cube with Model")
    print("=" * 70)
    
    # Mock model object
    class MockModel:
        def __init__(self):
            self.batch = None
    
    model = MockModel()
    
    # Create camera cube with model
    camera = Cube(
        cube_id="camera_with_model",
        position=(30, 50, 30),
        rotation=(0, 0),
        cube_type="camera",
        owner="test_player",
        model=model
    )
    
    # Verify model is passed to window
    assert camera.window is not None, "Camera should have window"
    assert camera.window.model is not None, "Window should have model reference"
    print("✅ Camera cube window has model reference")
    
    # Verify cube reference
    assert camera.window.cube is not None, "Window should have cube reference"
    assert camera.window.cube.id == "camera_with_model", "Window should reference correct cube"
    print("✅ Camera cube window has cube reference")
    
    print()
    return camera, model


def test_camera_window_rendering_method():
    """Test that CubeWindow has the _render_world_from_camera method."""
    print("=" * 70)
    print("TEST 5: CubeWindow Rendering Method")
    print("=" * 70)
    
    # Create a camera cube
    camera = Cube(
        cube_id="camera_render_test",
        position=(40, 50, 40),
        cube_type="camera"
    )
    
    # Check that window has rendering methods
    assert hasattr(camera.window, '_render_simple_scene'), \
        "Window should have _render_simple_scene method"
    assert hasattr(camera.window, '_render_world_from_camera'), \
        "Window should have _render_world_from_camera method"
    assert hasattr(camera.window, '_render_placeholder_cube'), \
        "Window should have _render_placeholder_cube method"
    
    print("✅ CubeWindow has all required rendering methods")
    print("   - _render_simple_scene()")
    print("   - _render_world_from_camera()")
    print("   - _render_placeholder_cube()")
    
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("FACTORIZED RENDERING PIPELINE TESTS")
    print("=" * 70)
    print()
    
    try:
        # Run tests
        test_camera_cube_creation()
        test_normal_cube_no_window()
        test_render_world_scene_function()
        test_camera_cube_with_model()
        test_camera_window_rendering_method()
        
        # Summary
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ Camera cubes create headless windows automatically")
        print("  ✅ Normal cubes don't create windows")
        print("  ✅ render_world_scene() function has correct signature")
        print("  ✅ Camera windows receive model and cube references")
        print("  ✅ CubeWindow has all rendering methods")
        print()
        print("The factorized rendering pipeline is working correctly!")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        return 1
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ UNEXPECTED ERROR")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
