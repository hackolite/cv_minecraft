#!/usr/bin/env python3
"""
Debug the ground detection issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics
)

def debug_ground_detection():
    """Debug why ground detection is triggering at y=15."""
    print("🔍 Debug: Ground Detection Issue")
    print("=" * 60)
    
    # Recreate the test world
    world = {}
    
    # Ground plane
    for x in range(5, 15):
        for z in range(5, 15):
            world[(x, 10, z)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test ground detection at y=15
    position = (8.0, 15.0, 8.0)
    
    print(f"Testing position: {position}")
    
    # Check collision at the position itself
    collision = collision_detector.check_collision(position)
    print(f"Collision at position: {collision}")
    
    # Check ground status update
    collision_info = {'x': False, 'y': False, 'z': False, 'ground': False}
    collision_detector._update_ground_status(collision_info, position)
    print(f"Ground status after update: {collision_info['ground']}")
    
    # Check what the ground status update is actually testing
    from minecraft_physics import COLLISION_EPSILON, GROUND_TOLERANCE
    
    print(f"\nGround detection tests:")
    for test_distance in [COLLISION_EPSILON, GROUND_TOLERANCE]:
        test_pos = (position[0], position[1] - test_distance, position[2])
        test_collision = collision_detector.check_collision(test_pos)
        print(f"  Testing {test_distance} below: pos={test_pos}, collision={test_collision}")
    
    return True

if __name__ == "__main__":
    debug_ground_detection()