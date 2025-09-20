#!/usr/bin/env python3
"""
Debug ceiling collision specifically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box
)

def debug_ceiling_collision():
    """Debug ceiling collision specifically."""
    print("🔍 Debug: Ceiling Collision Test")
    print("=" * 60)
    
    # Create a world with ground and ceiling
    world = {}
    
    # Ground plane at y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    # Ceiling at y=13 
    for x in range(8, 12):  # Note: range(8, 12) = [8, 9, 10, 11]
        for z in range(8, 13):
            world[(x, 13, z)] = "stone"
    
    print("World blocks around position (10, 13, 10):")
    for x in range(9, 12):
        for y in range(12, 15):
            for z in range(9, 12):
                if (x, y, z) in world:
                    print(f"  Block at ({x}, {y}, {z})")
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test ceiling collision
    print(f"\n🔍 Test: Jump from (10.5, 11.5, 10.5) to (10.5, 14.0, 10.5)")
    old_pos = (10.5, 11.5, 10.5)
    new_pos = (10.5, 14.0, 10.5)
    
    print(f"Old position: {old_pos}")
    print(f"New position: {new_pos}")
    
    # Check if x=10.5 is in the ceiling range
    print(f"Ceiling range: x in [8, 12) = [8, 9, 10, 11]")
    print(f"Player x=10.5 is in ceiling area: {8 <= 10.5 < 12}")
    
    # Check collision at various Y levels
    for test_y in [12.0, 13.0, 13.5, 14.0]:
        test_pos = (10.5, test_y, 10.5)
        collision = collision_detector.check_collision(test_pos)
        print(f"  Collision at y={test_y}: {collision}")
        
        if collision:
            min_corner, max_corner = get_player_bounding_box(test_pos)
            print(f"    Player bounding box: {min_corner} to {max_corner}")
            print(f"    Ceiling block (10, 13, 10): (10.0, 13.0, 10.0) to (11.0, 14.0, 11.0)")
    
    # Test the axis-separated collision
    print(f"\n🔍 Running axis-separated collision resolution:")
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    return True

if __name__ == "__main__":
    debug_ceiling_collision()