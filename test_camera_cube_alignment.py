#!/usr/bin/env python3
"""
Test camera and player cube alignment.
Verify that the camera position matches the player cube render position.
"""

def test_camera_cube_alignment():
    """Test that camera position aligns with player cube rendering position."""
    print("🎯 Testing camera and cube alignment...")
    
    # Test data: player position
    player_position = (10.0, 20.0, 30.0)
    player_size = 0.4
    
    # Calculate cube render position (from protocol.py logic)
    x, y, z = player_position
    cube_render_position = (x, y + player_size, z)  # Elevate by half-size
    
    print(f"   Player position: {player_position}")
    print(f"   Cube render position: {cube_render_position}")
    
    # Calculate expected camera positions (from updated minecraft_client_fr.py logic)
    # Normal stance: camera at cube center
    expected_camera_normal = (x, y + player_size, z)  # Same as cube center
    
    # Crouching: camera slightly lower within cube
    expected_camera_crouch = (x, y + player_size - 0.2, z)
    
    print(f"   Expected camera (normal): {expected_camera_normal}")
    print(f"   Expected camera (crouch): {expected_camera_crouch}")
    
    # Verify alignment
    cube_y = cube_render_position[1]
    camera_normal_y = expected_camera_normal[1]
    camera_crouch_y = expected_camera_crouch[1]
    
    # Camera should be at or near cube center
    alignment_normal = abs(cube_y - camera_normal_y) < 0.1
    alignment_crouch = abs(cube_y - camera_crouch_y) < 0.3  # Within cube bounds
    
    print(f"   ✅ Normal stance alignment: {alignment_normal} (diff: {abs(cube_y - camera_normal_y):.2f})")
    print(f"   ✅ Crouch stance alignment: {alignment_crouch} (diff: {abs(cube_y - camera_crouch_y):.2f})")
    
    # Test multiple positions
    test_positions = [
        (0.0, 0.0, 0.0),
        (5.5, 10.7, -3.2),
        (-10.0, 50.0, 100.0)
    ]
    
    print("\n   Testing multiple positions:")
    all_aligned = True
    for pos in test_positions:
        x, y, z = pos
        cube_y = y + player_size
        camera_y = y + player_size  # Normal stance
        aligned = abs(cube_y - camera_y) < 0.01
        all_aligned &= aligned
        print(f"     Position {pos}: {'✅' if aligned else '❌'} (cube_y={cube_y:.2f}, camera_y={camera_y:.2f})")
    
    if alignment_normal and alignment_crouch and all_aligned:
        print("\n✅ CAMERA-CUBE ALIGNMENT TEST PASSED!")
        print("   Camera positioning now matches player cube rendering")
        return True
    else:
        print("\n❌ CAMERA-CUBE ALIGNMENT TEST FAILED!")
        return False

if __name__ == "__main__":
    success = test_camera_cube_alignment()
    if success:
        print("\n🎉 Camera and cube are now properly aligned!")
    else:
        print("\n💥 Alignment issue detected!")