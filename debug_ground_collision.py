#!/usr/bin/env python3
"""
Debug ground collision specifically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box
)

def debug_ground_collision():
    """Debug ground collision in detail."""
    print("🔍 Debug: Ground Collision Issue")
    print("=" * 60)
    
    # Simple world with just ground
    world = {}
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    print(f"Ground blocks: {sorted(world.keys())}")
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test falling
    old_pos = (10.5, 15.0, 10.5)
    new_pos = (10.5, 5.0, 10.5)
    
    print(f"\nTesting fall from {old_pos} to {new_pos}")
    
    # Check collision at final destination
    collision_at_dest = collision_detector.check_collision(new_pos)
    print(f"Collision at destination {new_pos}: {collision_at_dest}")
    
    if collision_at_dest:
        min_corner, max_corner = get_player_bounding_box(new_pos)
        print(f"Player bounding box at destination: {min_corner} to {max_corner}")
        print("Expected to intersect with ground blocks at y=10")
    
    # Check ground level detection
    ground_level = collision_detector.find_ground_level(new_pos[0], new_pos[2], old_pos[1])
    print(f"Ground level at ({new_pos[0]}, {new_pos[2]}): {ground_level}")
    
    # Test collision resolution step by step
    print(f"\nStep-by-step axis processing:")
    
    old_x, old_y, old_z = old_pos
    new_x, new_y, new_z = new_pos
    
    # X axis test
    test_x = (new_x, old_y, old_z)
    collision_x = collision_detector.check_collision(test_x)
    print(f"X axis: {old_pos} → {test_x}, collision: {collision_x}")
    
    current_x = new_x if not collision_x else old_x
    
    # Y axis test
    test_y = (current_x, new_y, old_z)
    collision_y = collision_detector.check_collision(test_y)
    print(f"Y axis: ({current_x}, {old_y}, {old_z}) → {test_y}, collision: {collision_y}")
    
    if collision_y and new_y < old_y:
        print("  Detected ground collision - should snap to ground")
        ground_level = collision_detector.find_ground_level(current_x, old_z, old_y)
        print(f"  Ground level: {ground_level}")
    
    # Test the actual collision resolution
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    print(f"\nFinal result:")
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    return True

if __name__ == "__main__":
    debug_ground_collision()