#!/usr/bin/env python3
"""
Debug horizontal movement collision detection.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box,
    COLLISION_EPSILON, PLAYER_HEIGHT
)

def debug_horizontal_movement():
    """Debug why horizontal movement is blocked."""
    print("🔍 Debugging Horizontal Movement")
    print()
    
    # Create the same world as in the test
    world = {}
    
    # Vertical wall at ground level only
    world[(12, 10, 10)] = "stone"
    world[(12, 10, 11)] = "stone"
    
    # Horizontal wall at ground level only
    world[(10, 10, 12)] = "stone"
    world[(11, 10, 12)] = "stone"
    
    # Corner block at ground level only
    world[(12, 10, 12)] = "stone"
    
    # Ground
    for x in range(9, 15):
        for z in range(9, 15):
            world[(x, 9, z)] = "stone"
    
    print("World blocks at Y=10-12:")
    for pos, block in world.items():
        if pos[1] >= 10:
            print(f"   {block} block at {pos}")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test the horizontal movement that's being blocked
    start_pos = (11.5, 10.0, 11.5)
    end_pos = (13.5, 10.0, 11.5)
    
    print(f"Testing horizontal movement from {start_pos} to {end_pos}")
    print(f"Player height: {PLAYER_HEIGHT}")
    print()
    
    # Check bounding boxes at key positions
    test_positions = [
        start_pos,
        (12.0, 10.0, 11.5),  # Midway point
        (12.5, 10.0, 11.5),  # Near the problematic block
        end_pos
    ]
    
    for pos in test_positions:
        print(f"Position {pos}:")
        min_corner, max_corner = get_player_bounding_box(pos)
        print(f"   Bounding box: {min_corner} to {max_corner}")
        
        collision = detector.check_collision(pos)
        print(f"   Collision: {collision}")
        
        # Check which blocks this intersects
        for block_pos, block_type in world.items():
            if block_pos[1] >= 10:  # Only check blocks above ground
                block_x, block_y, block_z = block_pos
                block_min = (float(block_x), float(block_y), float(block_z))
                block_max = (float(block_x + 1), float(block_y + 1), float(block_z + 1))
                
                # Check intersection
                x_intersect = min_corner[0] < block_max[0] and max_corner[0] > block_min[0]
                y_intersect = min_corner[1] < block_max[1] and max_corner[1] > block_min[1]
                z_intersect = min_corner[2] < block_max[2] and max_corner[2] > block_min[2]
                intersects = x_intersect and y_intersect and z_intersect
                
                if intersects or (x_intersect and z_intersect):  # Show near misses too
                    y_gap = ""
                    if not y_intersect:
                        player_y_min, player_y_max = min_corner[1], max_corner[1]
                        block_y_min, block_y_max = block_min[1], block_max[1]
                        if player_y_max <= block_y_min:
                            y_gap = f" (below by {block_y_min - player_y_max:.3f})"
                        elif player_y_min >= block_y_max:
                            y_gap = f" (above by {player_y_min - block_y_max:.3f})"
                    
                    print(f"   {'✅' if intersects else '⚠️ '} Block {block_pos}: X={x_intersect}, Y={y_intersect}{y_gap}, Z={z_intersect}")
        print()
    
    # Test ray casting step by step
    print("Ray casting step by step:")
    ray_collision, hit_block = detector.ray_cast_collision(start_pos, end_pos)
    print(f"Ray casting result: collision={ray_collision}, hit_block={hit_block}")

if __name__ == "__main__":
    debug_horizontal_movement()