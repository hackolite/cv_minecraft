#!/usr/bin/env python3
"""
Debug the Y-axis gravity test failure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics
)

def debug_gravity_test():
    """Debug why the gravity test is failing."""
    print("🔍 Debug: Y-axis Gravity Test Failure")
    print("=" * 60)
    
    # Recreate the test world
    world = {}
    
    # Ground plane
    for x in range(5, 15):
        for z in range(5, 15):
            world[(x, 10, z)] = "stone"
    
    print(f"Ground blocks at y=10: {len([k for k in world.keys() if k[1] == 10])}")
    
    collision_detector = MinecraftCollisionDetector(world)
    physics = MinecraftPhysics(collision_detector)
    
    # Test the exact same conditions as the failing test
    position = (8.0, 15.0, 8.0)
    velocity = (0.0, -5.0, 0.0)
    dt = 0.1
    
    print(f"Initial: pos={position}, vel={velocity}, dt={dt}")
    
    # Check if there's ground below
    ground_level = collision_detector.find_ground_level(position[0], position[2], position[1])
    print(f"Ground level at ({position[0]}, {position[2]}): {ground_level}")
    
    # Check collision at starting position
    start_collision = collision_detector.check_collision(position)
    print(f"Collision at start position: {start_collision}")
    
    # Calculate where the player would move
    new_y = position[1] + velocity[1] * dt
    test_pos = (position[0], new_y, position[2])
    print(f"Player would move to: {test_pos}")
    
    # Check collision at new position
    end_collision = collision_detector.check_collision(test_pos)
    print(f"Collision at end position: {end_collision}")
    
    # Test collision resolution
    safe_pos, collision_info = collision_detector.resolve_collision(position, test_pos)
    print(f"Collision resolution: {position} → {test_pos} = {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Test physics update
    new_position, new_velocity, on_ground = physics.update_position(
        position, velocity, dt, False, False
    )
    
    print(f"Physics result: pos={new_position}, vel={new_velocity}, on_ground={on_ground}")
    
    return True

if __name__ == "__main__":
    debug_gravity_test()