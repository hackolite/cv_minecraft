#!/usr/bin/env python3
"""
Debug the safe position calculation before collision check.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, COLLISION_EPSILON

def test_debug_safe_position():
    """Debug the safe position calculation."""
    print("🔍 DEBUG: Safe Position Calculation")
    print("=" * 50)
    
    world_blocks = {(51, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world_blocks)
    
    # Simulate the algorithm manually
    old_x = 53.0
    new_x = 49.0
    y = 0.5
    z = 0.5
    clearance = 0.0
    player_half_width = PLAYER_WIDTH / 2
    block_y = int(math.floor(y))
    block_z = int(math.floor(z))
    safe_x = new_x  # Default to intended position
    
    print(f"Inputs: old_x={old_x}, new_x={new_x}, y={y}, z={z}")
    print(f"Block coordinates to check: y={block_y}, z={block_z}")
    print(f"Player half width: {player_half_width}")
    print(f"Collision epsilon: {COLLISION_EPSILON}")
    print()
    
    # Simulate moving left logic
    print("Moving left - checking range:")
    range_start = int(math.floor(new_x))
    range_end = int(math.floor(old_x)) + 2
    print(f"Range: {range_start} to {range_end-1} (range({range_start}, {range_end}))")
    
    for block_x in range(range_start, range_end):
        print(f"  Checking block_x={block_x}")
        if (block_x, block_y, block_z) in world_blocks:
            block_type = world_blocks[(block_x, block_y, block_z)]
            if block_type != "air":
                print(f"    Found block at ({block_x}, {block_y}, {block_z})")
                calculated_safe_x = float(block_x) + player_half_width + clearance + COLLISION_EPSILON * 10
                safe_x = min(calculated_safe_x, old_x)
                print(f"    Calculated: float({block_x}) + {player_half_width} + {clearance} + {COLLISION_EPSILON * 10} = {calculated_safe_x}")
                print(f"    After min with old_x: min({calculated_safe_x}, {old_x}) = {safe_x}")
                break
    
    print(f"Final safe_x: {safe_x}")
    
    # Test collision at this position
    collision = manager.check_collision((safe_x, y, z), "player1")
    print(f"Collision at ({safe_x}, {y}, {z}): {collision}")
    
    if collision:
        print(f"Collision detected - would fallback to old_x: {old_x}")
    else:
        print(f"No collision - would return safe_x: {safe_x}")
    
    # Test what the actual function returns
    actual_result = manager._snap_to_safe_x_position(old_x, new_x, y, z, "player1", clearance)
    print(f"Actual function result: {actual_result}")

if __name__ == "__main__":
    test_debug_safe_position()