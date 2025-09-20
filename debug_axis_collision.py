#!/usr/bin/env python3
"""
Debug version to understand collision detection issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, get_player_bounding_box
)

def debug_collision_detection():
    """Debug the collision detection logic."""
    print("🔍 Debug: Collision Detection Analysis")
    print("=" * 60)
    
    # Create a simple test world
    world = {}
    
    # Ground plane at y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
            
    print(f"World blocks: {sorted(world.keys())}")
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test falling case
    print("\n🔍 Debug Test: Falling from y=15 to y=9")
    old_pos = (10.5, 15.0, 10.5)
    new_pos = (10.5, 9.0, 10.5)
    
    print(f"Old position: {old_pos}")
    print(f"New position: {new_pos}")
    
    # Check collision at old position
    old_collision = collision_detector.check_collision(old_pos)
    print(f"Collision at old position: {old_collision}")
    
    # Check collision at new position
    new_collision = collision_detector.check_collision(new_pos)
    print(f"Collision at new position: {new_collision}")
    
    # Check bounding box at new position
    min_corner, max_corner = get_player_bounding_box(new_pos)
    print(f"Player bounding box at new position: {min_corner} to {max_corner}")
    
    # Check which blocks would be in the bounding box
    x_min, y_min, z_min = min_corner
    x_max, y_max, z_max = max_corner
    
    potential_blocks = []
    for x in range(int(x_min) - 1, int(x_max) + 2):
        for y in range(int(y_min) - 1, int(y_max) + 2):
            for z in range(int(z_min) - 1, int(z_max) + 2):
                potential_blocks.append((x, y, z))
    
    print(f"Potential collision blocks: {sorted(potential_blocks)}")
    
    # Check which of these blocks exist in the world
    existing_blocks = [b for b in potential_blocks if b in world]
    print(f"Existing blocks in collision area: {existing_blocks}")
    
    # Find ground level
    ground_level = collision_detector.find_ground_level(new_pos[0], new_pos[2], old_pos[1])
    print(f"Ground level at ({new_pos[0]}, {new_pos[2]}): {ground_level}")
    
    # Test the axis-separated collision
    print(f"\n🔍 Running axis-separated collision resolution:")
    safe_pos, collision_info = collision_detector.resolve_collision(old_pos, new_pos)
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    return True

def debug_simple_movement():
    """Debug simple single-axis movement."""
    print("\n🔍 Debug: Simple Movement Analysis")
    print("=" * 60)
    
    # Create a world with just ground
    world = {}
    
    # Ground plane at y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    collision_detector = MinecraftCollisionDetector(world)
    
    # Test a player standing on the ground
    print("\n🔍 Test: Player standing on ground")
    pos = (10.5, 11.0, 10.5)  # Should be standing on top of y=10 block
    
    collision = collision_detector.check_collision(pos)
    print(f"Position: {pos}")
    print(f"Has collision: {collision}")
    
    # Check bounding box
    min_corner, max_corner = get_player_bounding_box(pos)
    print(f"Bounding box: {min_corner} to {max_corner}")
    
    # The bounding box should be:
    # x: 10.5 ± 0.3 = 10.2 to 10.8
    # y: 11.0 to 11.0 + 1.8 = 11.0 to 12.8  
    # z: 10.5 ± 0.3 = 10.2 to 10.8
    
    # This should NOT intersect with the block at (10, 10, 10) which goes from:
    # x: 10.0 to 11.0
    # y: 10.0 to 11.0
    # z: 10.0 to 11.0
    
    # Since player's Y starts at 11.0 and block's Y ends at 11.0, there should be no overlap
    
    return True

if __name__ == "__main__":
    debug_collision_detection()
    debug_simple_movement()