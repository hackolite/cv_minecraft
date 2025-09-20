#!/usr/bin/env python3
"""
Debug the comprehensive test failures.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box
)

def debug_test_failures():
    """Debug why the comprehensive tests are failing."""
    print("🔍 Debug: Comprehensive Test Failures")
    print("=" * 60)
    
    # Recreate the test world
    world = {}
    
    # Ground plane
    for x in range(5, 15):
        for z in range(5, 15):
            world[(x, 10, z)] = "stone"
    
    # X-axis wall 
    for y in range(11, 15):
        for z in range(5, 15):
            world[(12, y, z)] = "stone"
    
    print(f"World has {len(world)} blocks")
    print(f"Sample blocks: {list(world.keys())[:10]}")
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Debug test 1: X movement
    print(f"\n🔍 Debug Test 1: X Movement")
    position = (10.0, 11.0, 10.0)
    target_x = 10.0 + 3.0 * 0.1  # Move right
    test_pos = (target_x, 11.0, 10.0)
    
    print(f"Starting position: {position}")
    print(f"Target position: {test_pos}")
    
    # Check if there's a collision at the target position
    collision = collision_detector.check_collision(test_pos)
    print(f"Collision at target: {collision}")
    
    if not collision:
        # Check bounding box
        min_corner, max_corner = get_player_bounding_box(test_pos)
        print(f"Player bounding box: {min_corner} to {max_corner}")
        
        # Check if this intersects wall at x=12
        if max_corner[0] > 12.0:
            print(f"Player box extends to x={max_corner[0]}, should hit wall at x=12!")
        else:
            print(f"Player box ends at x={max_corner[0]}, doesn't reach wall at x=12")
    
    # Test collision resolution
    safe_pos, collision_info = collision_detector.resolve_collision(position, test_pos)
    print(f"Collision resolution: {position} → {test_pos} = {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    return True

if __name__ == "__main__":
    debug_test_failures()