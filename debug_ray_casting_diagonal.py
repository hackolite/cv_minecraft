#!/usr/bin/env python3
"""
Debug ray casting for diagonal movement through corners.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box,
    COLLISION_EPSILON
)

def debug_ray_casting_diagonal():
    """Debug why ray casting doesn't detect corner collisions."""
    print("🔍 Debugging Ray Casting for Diagonal Movement")
    print()
    
    # Create the same world as in the test
    world = {
        (10, 10, 10): "stone",  # Main block
        (11, 10, 10): "stone",  # Block to the right
        (10, 10, 11): "stone",  # Block in front
        (11, 10, 11): "stone",  # Corner block
    }
    
    print("World setup:")
    for pos, block in world.items():
        print(f"   {block} block at {pos}")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test the problematic case - modify to have proper collision
    start_pos = (9.5, 10.5, 9.5)  # Changed from 11.0 to 10.5 to intersect blocks
    end_pos = (11.5, 10.5, 11.5)  # Changed from 11.0 to 10.5 to intersect blocks
    
    print(f"Testing diagonal movement from {start_pos} to {end_pos}")
    print()
    
    # Check if positions collide individually
    start_collision = detector.check_collision(start_pos)
    end_collision = detector.check_collision(end_pos)
    
    print(f"Start collision: {start_collision}")
    print(f"End collision: {end_collision}")
    print()
    
    # Manual ray casting debug
    sx, sy, sz = start_pos
    ex, ey, ez = end_pos
    
    dx = ex - sx
    dy = ey - sy  
    dz = ez - sz
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    print(f"Movement vector: ({dx}, {dy}, {dz})")
    print(f"Distance: {distance}")
    print()
    
    # Normalized direction
    dx_norm = dx / distance
    dy_norm = dy / distance
    dz_norm = dz / distance
    
    print(f"Normalized direction: ({dx_norm}, {dy_norm}, {dz_norm})")
    print()
    
    # Test step-by-step movement with small steps
    step_size = 0.05
    steps = int(distance / step_size) + 1
    
    print(f"Testing with step size: {step_size}, total steps: {steps}")
    print()
    
    collision_found = False
    for i in range(steps + 1):
        t = min(i * step_size, distance)
        test_x = sx + dx_norm * t
        test_y = sy + dy_norm * t
        test_z = sz + dz_norm * t
        
        test_pos = (test_x, test_y, test_z)
        collision = detector.check_collision(test_pos)
        
        if collision or i % 10 == 0 or i == steps:  # Print every 10th step or collisions
            print(f"   Step {i:3d}: t={t:.3f}, pos=({test_x:.3f}, {test_y:.3f}, {test_z:.3f}) collision={collision}")
            
            if collision:
                collision_found = True
                # Show which blocks this position intersects
                min_corner, max_corner = get_player_bounding_box(test_pos)
                print(f"      Player bounding box: {min_corner} to {max_corner}")
                
                # Check each world block manually
                for block_pos, block_type in world.items():
                    block_x, block_y, block_z = block_pos
                    block_min = (float(block_x), float(block_y), float(block_z))
                    block_max = (float(block_x + 1), float(block_y + 1), float(block_z + 1))
                    
                    # Check intersection
                    x_intersect = min_corner[0] < block_max[0] and max_corner[0] > block_min[0]
                    y_intersect = min_corner[1] < block_max[1] and max_corner[1] > block_min[1]
                    z_intersect = min_corner[2] < block_max[2] and max_corner[2] > block_min[2]
                    intersects = x_intersect and y_intersect and z_intersect
                    
                    if intersects:
                        print(f"      Intersects block {block_pos}")
                break
            elif i % 10 == 0:
                # Show bounding box for non-collision steps too
                min_corner, max_corner = get_player_bounding_box(test_pos)
                print(f"      Player bounding box: {min_corner} to {max_corner}")
                
                # Check proximity to blocks
                for block_pos, block_type in world.items():
                    block_x, block_y, block_z = block_pos
                    block_min = (float(block_x), float(block_y), float(block_z))
                    block_max = (float(block_x + 1), float(block_y + 1), float(block_z + 1))
                    
                    # Check intersection
                    x_intersect = min_corner[0] < block_max[0] and max_corner[0] > block_min[0]
                    y_intersect = min_corner[1] < block_max[1] and max_corner[1] > block_min[1]
                    z_intersect = min_corner[2] < block_max[2] and max_corner[2] > block_min[2]
                    
                    if x_intersect and z_intersect:  # XZ intersection (could be above/below)
                        print(f"      Near block {block_pos}: Y overlap = {y_intersect}")
    
    print()
    print(f"Ray casting collision found: {collision_found}")
    
    # Test the official ray casting method
    ray_collision, hit_block = detector.ray_cast_collision(start_pos, end_pos)
    print(f"Official ray casting result: collision={ray_collision}, hit_block={hit_block}")

if __name__ == "__main__":
    debug_ray_casting_diagonal()