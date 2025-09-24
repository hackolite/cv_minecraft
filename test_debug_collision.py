#!/usr/bin/env python3
"""
Debug version to understand the collision detection range.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH

def debug_collision_range():
    """Debug the collision detection range."""
    print("🔍 DEBUG: Collision Detection Range")
    print("=" * 50)
    
    world_blocks = {(51, 10, 10): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    # Simulate the range calculation for moving left
    old_x = 53.0
    new_x = 50.0
    y = 10.5
    z = 10.0
    
    print(f"Moving left from {old_x} to {new_x}")
    print(f"Block exists at: (51, 10, 10)")
    print()
    
    # Show the range calculation
    range_start = int(math.floor(new_x))
    range_end = int(math.floor(old_x)) + 2
    
    print(f"Range calculation:")
    print(f"  start = int(math.floor({new_x})) = {range_start}")
    print(f"  end = int(math.floor({old_x})) + 2 = {range_end}")
    print(f"  range({range_start}, {range_end}) = {list(range(range_start, range_end))}")
    print()
    
    # Check each position in the range
    block_y = int(math.floor(y))
    block_z = int(math.floor(z))
    
    print(f"Checking positions with y={block_y}, z={block_z}:")
    
    for block_x in range(range_start, range_end):
        exists = (block_x, block_y, block_z) in world_blocks
        if exists:
            block_type = world_blocks[(block_x, block_y, block_z)]
            print(f"  ({block_x}, {block_y}, {block_z}): EXISTS, type={block_type}")
        else:
            print(f"  ({block_x}, {block_y}, {block_z}): does not exist")
    
    print()
    print("Testing the actual collision function:")
    player_half_width = PLAYER_WIDTH / 2
    clearance = 0.0
    safe_x = new_x  # Default to intended position
    
    print(f"Initial safe_x: {safe_x}")
    
    # Simulate the moving left logic
    for block_x in range(range_start, range_end):
        print(f"  Checking block_x={block_x}")
        if (block_x, block_y, block_z) in world_blocks:
            block_type = world_blocks[(block_x, block_y, block_z)]
            if block_type != "air":
                print(f"    Found block at ({block_x}, {block_y}, {block_z})")
                safe_x = float(block_x) + player_half_width + clearance
                safe_x = min(safe_x, old_x)
                print(f"    Calculated safe_x: {safe_x}")
                break
    
    print(f"Final safe_x before collision check: {safe_x}")
    
    # Test the collision check
    collision = manager.check_collision((safe_x, y, z), "player1")
    print(f"Collision check at ({safe_x}, {y}, {z}): {collision}")
    
    if collision:
        print(f"Collision detected, falling back to old_x: {old_x}")
        final_result = old_x
    else:
        final_result = safe_x
    
    print(f"Final result: {final_result}")
    
    # Compare with actual function
    actual_result = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    print(f"Actual function result: {actual_result}")
    print(f"Match: {'YES' if abs(actual_result - final_result) < 0.001 else 'NO'}")

if __name__ == "__main__":
    debug_collision_range()