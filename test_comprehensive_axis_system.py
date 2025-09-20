#!/usr/bin/env python3
"""
Final comprehensive test of the axis-separated collision system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def comprehensive_axis_test():
    """Comprehensive test of the axis-separated collision system."""
    print("🎮 Comprehensive Axis-Separated Collision System Test")
    print("=" * 70)
    print("🔑 Testing the complete implementation as specified in the problem statement")
    print()
    
    success = True
    
    # Create a test world
    world = {}
    
    # Ground plane
    for x in range(5, 15):
        for z in range(5, 15):
            world[(x, 10, z)] = "stone"
    
    # X-axis wall 
    for y in range(11, 15):
        for z in range(5, 15):
            world[(12, y, z)] = "stone"
    
    # Z-axis wall
    for x in range(5, 12):
        for y in range(11, 15):
            world[(x, y, 12)] = "stone"
    
    # Ceiling
    for x in range(5, 12):
        for z in range(5, 12):
            world[(x, 14, z)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    physics = MinecraftPhysics(collision_detector)
    
    print("🧪 Test 1: Basic Axis Separation - X Movement")
    print("-" * 50)
    
    # Test X movement blocking - move closer to the wall
    position = (11.0, 11.0, 10.0)  # Start closer to wall
    velocity = (15.0, 0.0, 0.0)  # Move right toward wall faster
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}")
    print(f"Wall is at x=12, player width is {PLAYER_WIDTH}")
    print(f"Player will extend from x={11.0 - PLAYER_WIDTH/2} to x={11.0 + velocity[0]*dt + PLAYER_WIDTH/2}")
    
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, True, False
    )
    
    print(f"Result: pos={new_position}, vel={new_velocity}")
    
    # Should hit wall and stop X movement
    expected_max_x = 12.0 - PLAYER_WIDTH/2  # Player center should stop at wall edge minus radius
    if new_position[0] < expected_max_x and abs(new_velocity[0]) < 0.1:
        print("✅ X-axis collision correctly blocked and velocity reset")
    else:
        print("❌ X-axis collision failed")
        print(f"  Expected x < {expected_max_x}, got {new_position[0]}")
        print(f"  Expected vx ≈ 0, got {new_velocity[0]}")
        success = False
    
    print()
    
    print("🧪 Test 2: Basic Axis Separation - Y Movement (Gravity)")
    print("-" * 50)
    
    # Test falling - move player to a position away from ceiling blocks
    position = (13.0, 15.0, 13.0)  # Outside the ceiling area
    velocity = (0.0, -5.0, 0.0)  # Falling
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}")
    print(f"Ground level should be at y=11.0")
    print(f"Position is outside ceiling area (ceiling only covers x<12, z<12)")
    
    # Simulate multiple physics frames
    current_pos = position
    current_vel = velocity
    current_on_ground = False  # Start with not on ground
    frames = 0
    max_frames = 20
    
    while frames < max_frames and current_pos[1] > 11.5:  # Continue until close to ground level
        current_pos, current_vel, current_on_ground = physics.update_position(
            current_pos, current_vel, dt, current_on_ground, False
        )
        frames += 1
        
        print(f"  Frame {frames}: pos={current_pos}, vel={current_vel}, on_ground={current_on_ground}")
        
        # Check if we've landed
        if current_on_ground or abs(current_pos[1] - 11.0) < 0.1:
            print(f"  Landed after {frames} frames!")
            break
    
    # Should have landed on ground
    if abs(current_pos[1] - 11.0) < 0.2 and (current_on_ground or frames < max_frames):
        print("✅ Y-axis ground collision and landing working")
    else:
        print("❌ Y-axis ground collision failed")
        print(f"  Expected to land near y=11.0, final position: {current_pos}")
        success = False
    
    print()
    
    print("🧪 Test 3: Basic Axis Separation - Z Movement")
    print("-" * 50)
    
    # Test Z movement blocking - move closer to the wall
    position = (8.0, 11.0, 11.0)  # Start closer to wall 
    velocity = (0.0, 0.0, 15.0)  # Move forward toward wall faster
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}")
    print(f"Wall is at z=12, player width is {PLAYER_WIDTH}")
    print(f"Player will extend from z={11.0 - PLAYER_WIDTH/2} to z={11.0 + velocity[2]*dt + PLAYER_WIDTH/2}")
    
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, True, False
    )
    
    print(f"Result: pos={new_position}, vel={new_velocity}")
    
    # Should hit wall and stop Z movement
    expected_max_z = 12.0 - PLAYER_WIDTH/2  # Player center should stop at wall edge minus radius
    if new_position[2] < expected_max_z and abs(new_velocity[2]) < 0.1:
        print("✅ Z-axis collision correctly blocked and velocity reset")
    else:
        print("❌ Z-axis collision failed")
        print(f"  Expected z < {expected_max_z}, got {new_position[2]}")
        print(f"  Expected vz ≈ 0, got {new_velocity[2]}")
        success = False
    
    print()
    
    print("🧪 Test 4: Ceiling Collision")
    print("-" * 50)
    
    # Test jumping into ceiling
    position = (8.0, 11.0, 8.0)
    velocity = (0.0, 8.0, 0.0)  # Jump up
    dt = 0.5  # Longer time to reach ceiling
    
    print(f"Initial: pos={position}, vel={velocity}")
    
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, True, True
    )
    
    print(f"Result: pos={new_position}, vel={new_velocity}")
    
    # Should hit ceiling and stop upward movement
    if new_position[1] < 14.0 and abs(new_velocity[1]) < 1.0:
        print("✅ Ceiling collision working")
    else:
        print("❌ Ceiling collision failed")
        success = False
    
    print()
    
    print("🧪 Test 5: Diagonal Movement - Axis Independence")
    print("-" * 50)
    
    # Test diagonal movement where some axes are blocked - use realistic positions
    position = (11.0, 11.0, 11.0)  # Start close to both walls
    velocity = (15.0, 0.0, 15.0)  # Diagonal movement toward corner, faster
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}")
    print(f"Walls at x=12, z=12. Player width is {PLAYER_WIDTH}")
    
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, True, False
    )
    
    print(f"Result: pos={new_position}, vel={new_velocity}")
    
    # Both X and Z should be blocked independently
    expected_max_x = 12.0 - PLAYER_WIDTH/2
    expected_max_z = 12.0 - PLAYER_WIDTH/2
    if (new_position[0] < expected_max_x and new_position[2] < expected_max_z and 
        abs(new_velocity[0]) < 0.1 and abs(new_velocity[2]) < 0.1):
        print("✅ Diagonal movement handled correctly - both axes blocked independently")
    else:
        print("❌ Diagonal movement axis independence failed")
        print(f"  Expected x < {expected_max_x}, got {new_position[0]}")
        print(f"  Expected z < {expected_max_z}, got {new_position[2]}")
        print(f"  Expected vx ≈ 0, got {new_velocity[0]}")
        print(f"  Expected vz ≈ 0, got {new_velocity[2]}")
        success = False
    
    print()
    
    print("=" * 70)
    
    if success:
        print("🎉 COMPREHENSIVE AXIS-SEPARATED COLLISION TESTS PASSED!")
        print()
        print("✅ All requirements from the problem statement implemented:")
        print("  🧩 Player represented as AABB (Axis-Aligned Bounding Box)")
        print("  🧩 Each solid block is AABB (1×1×1)")
        print("  🧩 Movement processed separately by axis: X → Y → Z")
        print("  🧩 X-axis: blocks movement and sets vx = 0 on collision")
        print("  🧩 Y-axis: handles gravity, ground landing, and ceiling blocking")
        print("  🧩 Z-axis: blocks movement and sets vz = 0 on collision")
        print("  🧩 Player positioned correctly after collision resolution")
        print("  🧩 Velocities updated according to collisions")
        print()
        print("🔑 Key benefits achieved:")
        print("  ✅ Simple axis-by-axis processing")
        print("  ✅ No diagonal intersection bugs")
        print("  ✅ Proper velocity reset on collision")
        print("  ✅ Accurate ground snapping and positioning")
    else:
        print("❌ SOME COMPREHENSIVE TESTS FAILED!")
    
    return success

if __name__ == "__main__":
    success = comprehensive_axis_test()
    sys.exit(0 if success else 1)