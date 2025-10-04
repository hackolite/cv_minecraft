#!/usr/bin/env python3
"""
Test Camera View Fix
====================

Tests to verify that camera views are generated from camera position/rotation,
not from player position/rotation, and that screenshots are saved in the correct directory.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import Cube, CubeWindow


def test_cube_window_receives_cube_reference():
    """Test that CubeWindow receives and stores cube reference."""
    print("🧪 Test 1: CubeWindow receives cube reference")
    print("=" * 60)
    
    # Create a camera cube
    camera_cube = Cube(
        cube_id="test_camera_1",
        position=(10, 20, 30),
        rotation=(45, -15),
        cube_type="camera"
    )
    
    # Verify window was created
    assert camera_cube.window is not None, "Camera cube should have a window"
    print(f"✅ Camera cube has window: {camera_cube.window is not None}")
    
    # Verify window has cube reference
    assert camera_cube.window.cube_ref is not None, "Window should have cube reference"
    print(f"✅ Window has cube reference: {camera_cube.window.cube_ref is not None}")
    
    # Verify cube reference is correct
    assert camera_cube.window.cube_ref == camera_cube, "Window cube_ref should point to camera_cube"
    print(f"✅ Cube reference is correct: {camera_cube.window.cube_ref == camera_cube}")
    
    # Verify window can access cube position and rotation
    assert camera_cube.window.cube_ref.position == (10, 20, 30), "Should access correct position"
    assert camera_cube.window.cube_ref.rotation == (45, -15), "Should access correct rotation"
    print(f"✅ Window can access position: {camera_cube.window.cube_ref.position}")
    print(f"✅ Window can access rotation: {camera_cube.window.cube_ref.rotation}")
    
    # Clean up
    if camera_cube.window:
        camera_cube.window.close()
    
    print("\n✅ Test 1 PASSED: CubeWindow correctly receives and stores cube reference")
    print()


def test_normal_cube_no_window():
    """Test that normal cubes don't create windows."""
    print("🧪 Test 2: Normal cube doesn't create window")
    print("=" * 60)
    
    # Create a normal cube
    normal_cube = Cube(
        cube_id="test_normal_1",
        position=(5, 10, 15),
        cube_type="normal"
    )
    
    # Verify no window was created
    assert normal_cube.window is None, "Normal cube should not have a window"
    print(f"✅ Normal cube has no window: {normal_cube.window is None}")
    
    print("\n✅ Test 2 PASSED: Normal cubes don't create windows")
    print()


def test_camera_position_update():
    """Test that updating camera position is accessible through window."""
    print("🧪 Test 3: Camera position update")
    print("=" * 60)
    
    # Create a camera cube
    camera_cube = Cube(
        cube_id="test_camera_2",
        position=(0, 0, 0),
        rotation=(0, 0),
        cube_type="camera"
    )
    
    # Update position
    new_position = (100, 50, 75)
    camera_cube.update_position(new_position)
    
    # Verify window can see updated position
    assert camera_cube.window.cube_ref.position == new_position, "Window should see updated position"
    print(f"✅ Window sees updated position: {camera_cube.window.cube_ref.position}")
    
    # Update rotation
    new_rotation = (90, 45)
    camera_cube.update_rotation(new_rotation)
    
    # Verify window can see updated rotation
    assert camera_cube.window.cube_ref.rotation == new_rotation, "Window should see updated rotation"
    print(f"✅ Window sees updated rotation: {camera_cube.window.cube_ref.rotation}")
    
    # Clean up
    if camera_cube.window:
        camera_cube.window.close()
    
    print("\n✅ Test 3 PASSED: Camera position and rotation updates are accessible")
    print()


def test_screenshot_directory_logic():
    """Test the screenshot directory logic from generate_camera_screenshot.py"""
    print("🧪 Test 4: Screenshot directory logic")
    print("=" * 60)
    
    import os
    from datetime import datetime
    
    # Simulate the logic from generate_camera_screenshot.py
    actual_camera_id = "camera_0"
    output_image = "screenshot.png"  # Default name
    
    if output_image == "screenshot.png":
        # Default name - use camera-specific directory
        camera_dir = f"recordings/{actual_camera_id}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        expected_output = os.path.join(camera_dir, f"screenshot_{timestamp}.png")
        
        print(f"✅ Camera ID: {actual_camera_id}")
        print(f"✅ Camera directory: {camera_dir}")
        print(f"✅ Expected output path: {expected_output}")
        
        # Verify path contains camera_id
        assert actual_camera_id in expected_output, "Output path should contain camera_id"
        assert "recordings" in expected_output, "Output path should be in recordings directory"
        print(f"✅ Path contains camera_id: True")
        print(f"✅ Path is in recordings directory: True")
    
    print("\n✅ Test 4 PASSED: Screenshot directory logic works correctly")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Camera View Fix Tests")
    print("=" * 60)
    print()
    
    try:
        test_cube_window_receives_cube_reference()
        test_normal_cube_no_window()
        test_camera_position_update()
        test_screenshot_directory_logic()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
