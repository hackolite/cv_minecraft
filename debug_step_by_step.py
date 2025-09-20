#!/usr/bin/env python3
"""
Debug axis-separated collision step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import MinecraftCollisionDetector

def debug_axis_separated_step_by_step():
    """Debug each axis step by step."""
    print("🔍 Debug: Axis-Separated Step by Step")
    print("=" * 60)
    
    # Create a world with ground and ceiling
    world = {}
    
    # Ground plane at y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test simple upward movement (no walls, just ceiling to worry about)
    print(f"\n🔍 Test: Move from (10.5, 11.5, 10.5) to (10.5, 11.5, 10.5)")
    print("(No movement - should have no collisions)")
    
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (10.5, 11.5, 10.5)  # No movement
    
    print(f"Old position: {old_pos}")
    print(f"New position: {new_pos}")
    
    # Check current position collision
    collision_at_old = collision_detector.check_collision(old_pos)
    print(f"Collision at old position: {collision_at_old}")
    
    # Manually test each axis
    current_x, current_y, current_z = old_pos
    new_x, new_y, new_z = new_pos
    
    print(f"\nAxis X test: ({new_x}, {current_y}, {current_z})")
    test_pos_x = (new_x, current_y, current_z)
    collision_x = collision_detector.check_collision(test_pos_x)
    print(f"X collision: {collision_x}")
    
    print(f"\nAxis Y test: ({current_x}, {new_y}, {current_z})")
    test_pos_y = (current_x, new_y, current_z)
    collision_y = collision_detector.check_collision(test_pos_y)
    print(f"Y collision: {collision_y}")
    
    print(f"\nAxis Z test: ({current_x}, {current_y}, {new_z})")
    test_pos_z = (current_x, current_y, new_z)
    collision_z = collision_detector.check_collision(test_pos_z)
    print(f"Z collision: {collision_z}")
    
    # Now test with actual collision resolution
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    print(f"\nCollision resolution result:")
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    return True

if __name__ == "__main__":
    debug_axis_separated_step_by_step()