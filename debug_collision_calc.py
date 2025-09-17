#!/usr/bin/env python3
"""
Debug the collision calculation step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import MinecraftServer, PLAYER_HEIGHT

def debug_collision_calculation():
    """Debug the collision calculation step by step."""
    print("🔍 Debugging Collision Calculation\n")
    
    # Create a minimal server
    server = MinecraftServer()
    server.world.world = {}
    
    # Add a block at (10, 10, 10)
    server.world.world[(10, 10, 10)] = "stone"
    
    # Test position (10, 10.9, 10) - should NOT collide
    x, y, z = 10, 10.9, 10
    player_size = 0.4
    player_height = PLAYER_HEIGHT
    
    print(f"Testing position ({x}, {y}, {z})")
    print(f"Player size: {player_size}, Player height: {player_height}")
    
    # Calculate bounding boxes
    min_x = int(x - player_size)
    max_x = int(x + player_size) + 1
    min_y = int(y)
    max_y = int(y + player_height) + 1
    min_z = int(z - player_size)
    max_z = int(z + player_size) + 1
    
    print(f"Block check ranges:")
    print(f"  X: {min_x} to {max_x-1}")
    print(f"  Y: {min_y} to {max_y-1}")
    print(f"  Z: {min_z} to {max_z-1}")
    
    # Player bounding box
    player_x_min, player_x_max = x - player_size, x + player_size
    player_y_min, player_y_max = y, y + player_height
    player_z_min, player_z_max = z - player_size, z + player_size
    
    print(f"Player bounding box:")
    print(f"  X: {player_x_min} to {player_x_max}")
    print(f"  Y: {player_y_min} to {player_y_max}")
    print(f"  Z: {player_z_min} to {player_z_max}")
    
    # Check each block in range
    print(f"\nChecking blocks in range:")
    
    for check_x in range(min_x, max_x):
        for check_y in range(min_y, max_y):
            for check_z in range(min_z, max_z):
                check_pos = (check_x, check_y, check_z)
                if check_pos in server.world.world:
                    print(f"  Found block at {check_pos}")
                    
                    # Block bounding box
                    block_x_min, block_x_max = check_x, check_x + 1
                    block_y_min, block_y_max = check_y, check_y + 1
                    block_z_min, block_z_max = check_z, check_z + 1
                    
                    print(f"    Block bounding box:")
                    print(f"      X: {block_x_min} to {block_x_max}")
                    print(f"      Y: {block_y_min} to {block_y_max}")
                    print(f"      Z: {block_z_min} to {block_z_max}")
                    
                    # Check overlap
                    x_overlap = (player_x_min < block_x_max) and (player_x_max > block_x_min)
                    y_overlap = (player_y_min < block_y_max) and (player_y_max > block_y_min)
                    z_overlap = (player_z_min < block_z_max) and (player_z_max > block_z_min)
                    
                    print(f"    Overlap checks:")
                    print(f"      X: {x_overlap} ({player_x_min} < {block_x_max}) and ({player_x_max} > {block_x_min})")
                    print(f"      Y: {y_overlap} ({player_y_min} < {block_y_max}) and ({player_y_max} > {block_y_min})")
                    print(f"      Z: {z_overlap} ({player_z_min} < {block_z_max}) and ({player_z_max} > {block_z_min})")
                    
                    if x_overlap and y_overlap and z_overlap:
                        print(f"    ❌ COLLISION DETECTED with block at {check_pos}")
                        return True
                    else:
                        print(f"    ✅ No collision with block at {check_pos}")
    
    print("✅ No collision detected")
    return False

if __name__ == "__main__":
    debug_collision_calculation()