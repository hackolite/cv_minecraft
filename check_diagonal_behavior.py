#!/usr/bin/env python3
"""
Check if the diagonal movement is actually correct behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def check_diagonal_behavior():
    """Check if diagonal movement behavior is correct."""
    print("🔍 Checking Diagonal Movement Behavior")
    print("=" * 60)
    
    # Create world with blocks
    world = {
        (10, 10, 10): "stone",
        (11, 10, 10): "stone", 
        (10, 10, 11): "stone",
        (11, 10, 11): "stone"
    }
    
    print(f"World blocks: {list(world.keys())}")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test case 2 from the failing test
    print("🔍 Test Case 2: Moving diagonally through corner")
    start_pos = (9.5, 11.0, 9.5)
    end_pos = (11.5, 11.0, 11.5)
    
    print(f"Start: {start_pos}")
    print(f"End: {end_pos}")
    
    # Check bounding boxes
    start_min, start_max = get_player_bounding_box(start_pos)
    end_min, end_max = get_player_bounding_box(end_pos)
    
    print(f"Start bounding box: {start_min} to {start_max}")
    print(f"End bounding box: {end_min} to {end_max}")
    
    # Check if these bounding boxes intersect with any blocks
    print(f"\nChecking intersection with blocks:")
    for block_pos in world.keys():
        bx, by, bz = block_pos
        block_min = (float(bx), float(by), float(bz))
        block_max = (float(bx+1), float(by+1), float(bz+1))
        
        # Check start position
        start_intersect = (start_min[0] < block_max[0] and start_max[0] > block_min[0] and
                          start_min[1] < block_max[1] and start_max[1] > block_min[1] and
                          start_min[2] < block_max[2] and start_max[2] > block_min[2])
        
        # Check end position  
        end_intersect = (end_min[0] < block_max[0] and end_max[0] > block_min[0] and
                        end_min[1] < block_max[1] and end_max[1] > block_min[1] and
                        end_min[2] < block_max[2] and end_max[2] > block_min[2])
        
        print(f"  Block {block_pos} ({block_min} to {block_max}):")
        print(f"    Start intersect: {start_intersect}")
        print(f"    End intersect: {end_intersect}")
    
    # The key insight: player at y=11.0 with height 1.8 goes from y=11.0 to y=12.8
    # Blocks at y=10 go from y=10.0 to y=11.0
    # So player bottom (y=11.0) just touches block top (y=11.0)
    # This should be considered touching/collision!
    
    print(f"\n🔍 Analysis:")
    print(f"Player at y=11.0 spans from y=11.0 to y={11.0 + PLAYER_HEIGHT}")
    print(f"Blocks at y=10 span from y=10.0 to y=11.0")
    print(f"Player bottom touches block top at y=11.0")
    print(f"This should be considered a collision for proper behavior!")
    
    return True

if __name__ == "__main__":
    check_diagonal_behavior()