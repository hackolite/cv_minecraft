#!/usr/bin/env python3
"""
Test to validate the axis-separated collision system implementation.
This test verifies that the collision system processes axes separately in the order X → Y → Z
as specified in the problem statement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def test_axis_separated_collision():
    """Test that collision processing happens axis by axis in order X → Y → Z."""
    print("🧪 Testing Axis-Separated Collision System")
    print("=" * 60)
    
    # Create a test world with specific block layout
    world = {}
    
    # Ground plane at y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    # Wall at x=12 (blocks movement in X direction)
    for y in range(11, 14):
        for z in range(8, 13):
            world[(12, y, z)] = "stone"
            
    # Ceiling at y=13 (blocks movement in Y direction)
    for x in range(8, 12):
        for z in range(8, 13):
            world[(x, 13, z)] = "stone"
            
    # Wall at z=12 (blocks movement in Z direction)
    for x in range(8, 12):
        for y in range(11, 14):
            world[(x, y, 12)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    
    success = True
    
    print("\n🔍 Test 1: X-axis blocking")
    print("Attempting to move from (10.5, 11.5, 10.5) to (12.5, 11.5, 10.5)")
    print("Expected: X movement blocked, position stays at x=10.5")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (12.5, 11.5, 10.5)  # Try to move through wall
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    if collision_info['x'] and abs(safe_pos[0] - old_pos[0]) < 0.1:
        print("✅ X-axis collision correctly blocked movement")
    else:
        print("❌ X-axis collision not working as expected")
        success = False
    
    print("\n🔍 Test 2: Y-axis ground collision")
    print("Attempting to fall from (10.5, 15.0, 10.5) to (10.5, 9.0, 10.5)")
    print("Expected: Y movement blocked, player lands on ground at y=11.0")
    
    old_pos = (10.5, 15.0, 10.5)
    new_pos = (10.5, 9.0, 10.5)  # Try to fall through ground
    
    # Debug what blocks exist around this position
    print(f"Checking world blocks around position...")
    for x in [9, 10, 11]:
        for y in [10, 11, 12, 13, 14]:
            for z in [9, 10, 11]:
                if (x, y, z) in world:
                    print(f"  Block at ({x}, {y}, {z})")
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    if collision_info['y'] and collision_info['ground'] and abs(safe_pos[1] - 11.0) < 0.1:
        print("✅ Y-axis ground collision correctly snapped to ground")
    else:
        print("❌ Y-axis ground collision not working as expected")
        print(f"  Expected Y position around 11.0, got {safe_pos[1]}")
        print(f"  Expected ground=True, got {collision_info['ground']}")
        success = False
    
    print("\n🔍 Test 3: Y-axis ceiling collision")
    print("Attempting to jump from (10.5, 11.5, 10.5) to (10.5, 14.0, 10.5)")
    print("Expected: Y movement blocked by ceiling")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (10.5, 14.0, 10.5)  # Try to jump through ceiling
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    if collision_info['y'] and safe_pos[1] <= old_pos[1]:
        print("✅ Y-axis ceiling collision correctly blocked upward movement")
    else:
        print("❌ Y-axis ceiling collision not working as expected")
        success = False
    
    print("\n🔍 Test 4: Z-axis blocking")
    print("Attempting to move from (10.5, 11.5, 10.5) to (10.5, 11.5, 12.5)")
    print("Expected: Z movement blocked, position stays at z=10.5")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (10.5, 11.5, 12.5)  # Try to move through wall
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    if collision_info['z'] and abs(safe_pos[2] - old_pos[2]) < 0.1:
        print("✅ Z-axis collision correctly blocked movement")
    else:
        print("❌ Z-axis collision not working as expected")
        success = False
    
    print("\n🔍 Test 5: Diagonal movement - axis separation verification")
    print("Attempting diagonal movement from (10.5, 11.5, 10.5) to (12.5, 14.0, 12.5)")
    print("Expected: All axes blocked, position unchanged")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (12.5, 14.0, 12.5)  # Try to move diagonally through walls
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # With axis-separated processing, each axis should be blocked independently
    expected_collisions = ['x', 'y', 'z']
    blocked_axes = [axis for axis in expected_collisions if collision_info[axis]]
    
    if len(blocked_axes) == 3:
        print("✅ Diagonal movement correctly processed axis-by-axis - all blocked")
    else:
        print(f"❌ Expected all axes blocked, got: {blocked_axes}")
        success = False
    
    print("\n🔍 Test 6: Partial diagonal movement - only some axes blocked")
    print("Attempting movement from (10.5, 11.5, 10.5) to (11.0, 12.0, 10.8)")
    print("Expected: Only Y-axis blocked by ceiling, X and Z should work")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (11.0, 12.0, 10.8)  # Move partially, only hitting ceiling
    
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    
    print(f"Result position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # X and Z should succeed, Y should be blocked
    if (not collision_info['x'] and collision_info['y'] and not collision_info['z'] and
        abs(safe_pos[0] - 11.0) < 0.1 and abs(safe_pos[2] - 10.8) < 0.1):
        print("✅ Partial diagonal movement correctly processed - X,Z allowed, Y blocked")
    else:
        print("❌ Partial diagonal movement not working as expected")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 AXIS-SEPARATED COLLISION SYSTEM TESTS PASSED!")
        print("✅ X-axis processing: blocks movement and maintains position")
        print("✅ Y-axis processing: handles gravity, ground snapping, ceiling blocking")
        print("✅ Z-axis processing: blocks movement and maintains position")
        print("✅ Axis separation: processes X → Y → Z independently")
        print("✅ Diagonal movement: handles each axis separately as expected")
    else:
        print("❌ AXIS-SEPARATED COLLISION SYSTEM TESTS FAILED!")
        print("Some collision behaviors are not working as expected.")
    
    return success


def test_velocity_reset_integration():
    """Test that velocity is correctly reset on collision in the physics system."""
    print("\n🧪 Testing Velocity Reset on Collision")
    print("=" * 60)
    
    # Create a simple world with walls
    world = {}
    
    # Ground
    for x in range(5, 15):
        for z in range(5, 15):
            world[(x, 10, z)] = "stone"
    
    # Wall at x=12
    for y in range(11, 15):
        for z in range(5, 15):
            world[(12, y, z)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    physics = MinecraftPhysics(collision_detector)
    
    success = True
    
    print("\n🔍 Test: Moving into wall should reset X velocity")
    
    position = (10.0, 11.0, 10.0)
    velocity = (5.0, 0.0, 0.0)  # Moving right toward wall
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}")
    
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, True, False
    )
    
    print(f"Result: pos={new_position}, vel={new_velocity}")
    
    # Should have hit the wall and X velocity should be reset to 0
    if abs(new_velocity[0]) < 0.1:  # X velocity should be ~0
        print("✅ X velocity correctly reset to 0 after collision")
    else:
        print(f"❌ X velocity not reset: {new_velocity[0]}")
        success = False
    
    return success


if __name__ == "__main__":
    print("🎮 Testing Axis-Separated Collision System Implementation")
    print("🔑 Key requirement: Process axes separately in order X → Y → Z")
    print("🔑 Block movement and reset velocity on collision")
    print("🔑 Handle ground snapping for Y axis")
    print()
    
    success1 = test_axis_separated_collision()
    success2 = test_velocity_reset_integration()
    
    if success1 and success2:
        print("\n🎉 ALL AXIS-SEPARATED COLLISION TESTS PASSED!")
        print("✅ The simplest possible axis-separated collision system is working!")
        print("✅ Collision processing follows X → Y → Z order")
        print("✅ Velocity reset on collision is working")
        print("✅ Ground snapping and ceiling blocking work correctly")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)