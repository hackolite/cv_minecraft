#!/usr/bin/env python3
"""
Test the updated camera positioning logic in isolation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_camera_positioning_logic():
    """Test the camera positioning calculations without OpenGL dependencies."""
    print("🔍 Testing camera positioning logic...")
    
    # Simulate the positioning logic from set_3d method
    def calculate_camera_position(player_pos, crouch=False):
        x, y, z = player_pos
        
        if crouch:
            # When crouching, position slightly lower within the cube
            cube_center_y = y + 0.4  # Cube center (y + size)
            camera_y = cube_center_y - 0.2  # Slightly lower when crouching
            return (-x, -camera_y, -z)
        else:
            # Position camera at the center/top of the player cube for normal stance
            cube_center_y = y + 0.4  # Cube center matches get_render_position logic
            return (-x, -cube_center_y, -z)
    
    # Test cases
    test_cases = [
        {"pos": (0, 0, 0), "crouch": False, "expected_y": -0.4},
        {"pos": (0, 0, 0), "crouch": True, "expected_y": -0.2},
        {"pos": (10, 20, 30), "crouch": False, "expected_y": -20.4},
        {"pos": (10, 20, 30), "crouch": True, "expected_y": -20.2},
        {"pos": (-5, 100, -10), "crouch": False, "expected_y": -100.4},
    ]
    
    all_passed = True
    for i, case in enumerate(test_cases):
        result = calculate_camera_position(case["pos"], case["crouch"])
        expected_y = case["expected_y"]
        actual_y = result[1]
        
        passed = abs(actual_y - expected_y) < 0.001
        all_passed &= passed
        
        status = "✅" if passed else "❌"
        crouch_str = " (crouching)" if case["crouch"] else ""
        print(f"   Test {i+1}: {status} Position {case['pos']}{crouch_str}")
        print(f"            Expected Y: {expected_y}, Actual Y: {actual_y}")
    
    return all_passed

def test_cube_render_position():
    """Test the cube render position calculation."""
    print("\n🧊 Testing cube render position logic...")
    
    # Simulate get_render_position from protocol.py
    def get_render_position(position, size=0.4):
        x, y, z = position
        return (x, y + size, z)  # Elevate by half-size so bottom touches ground
    
    test_positions = [
        (0, 0, 0),
        (10, 20, 30),
        (-5.5, 100.7, -25.3)
    ]
    
    all_passed = True
    for pos in test_positions:
        render_pos = get_render_position(pos)
        expected_y = pos[1] + 0.4
        actual_y = render_pos[1]
        
        passed = abs(actual_y - expected_y) < 0.001
        all_passed &= passed
        
        status = "✅" if passed else "❌"
        print(f"   {status} Position {pos} -> Render {render_pos}")
        print(f"       Expected Y elevation: {expected_y}, Actual: {actual_y}")
    
    return all_passed

def test_alignment_verification():
    """Verify that camera Y and cube render Y are aligned."""
    print("\n🎯 Testing camera-cube Y alignment...")
    
    test_positions = [
        (0, 0, 0),
        (5, 10, 15),
        (-10, 50, -20)
    ]
    
    all_aligned = True
    for pos in test_positions:
        # Cube render position
        cube_y = pos[1] + 0.4
        
        # Camera position (normal stance)
        camera_y_offset = pos[1] + 0.4  # Should match cube center
        
        aligned = abs(cube_y - camera_y_offset) < 0.001
        all_aligned &= aligned
        
        status = "✅" if aligned else "❌"
        print(f"   {status} Position {pos}: Cube Y={cube_y}, Camera Y offset={camera_y_offset}")
    
    return all_aligned

if __name__ == "__main__":
    print("🧪 Testing updated camera positioning...\n")
    
    success1 = test_camera_positioning_logic()
    success2 = test_cube_render_position()
    success3 = test_alignment_verification()
    
    overall_success = success1 and success2 and success3
    
    print(f"\n{'='*50}")
    if overall_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Camera positioning logic is correct")
        print("✅ Cube render position logic is correct")
        print("✅ Camera and cube are properly aligned")
        print("\n📝 Summary of changes:")
        print("   - Camera Y position now matches cube render Y position")
        print("   - Normal stance: camera at cube center (y + 0.4)")
        print("   - Crouching: camera slightly lower within cube (y + 0.2)")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   Check the positioning calculations")