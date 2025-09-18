#!/usr/bin/env python3
"""
Debug the ray casting collision detection to understand why diagonal movement fails.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box, 
    get_blocks_in_bounding_box, box_intersects_block, COLLISION_EPSILON
)

def debug_ray_casting():
    """Debug ray casting for diagonal movement through blocks."""
    print("🔍 Debugging Ray Casting for Diagonal Movement")
    print()
    
    # Create the same world from the failing test case
    world = {
        (10, 10, 10): "stone",  # Main block
        (11, 10, 10): "stone",  # Block to the right
        (10, 10, 11): "stone",  # Block in front
        (11, 10, 11): "stone",  # Corner block
    }
    
    detector = MinecraftCollisionDetector(world)
    
    # The failing test case: moving diagonally through corner
    start_pos = (9.5, 11.0, 9.5)
    end_pos = (11.5, 11.0, 11.5)
    
    print(f"Test case: Moving from {start_pos} to {end_pos}")
    print()
    
    # Manual ray casting debug
    sx, sy, sz = start_pos
    ex, ey, ez = end_pos
    
    # Calculate direction and distance
    dx = ex - sx
    dy = ey - sy
    dz = ez - sz
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    print(f"Movement vector: ({dx}, {dy}, {dz})")
    print(f"Total distance: {distance}")
    
    # Normalize direction
    dx /= distance
    dy /= distance
    dz /= distance
    
    print(f"Normalized direction: ({dx:.3f}, {dy:.3f}, {dz:.3f})")
    print()
    
    # Test different step sizes
    step_sizes = [0.1, 0.05, 0.02, 0.01]
    
    for step_size in step_sizes:
        print(f"Testing with step size: {step_size}")
        steps = int(distance / step_size) + 1
        print(f"Number of steps: {steps}")
        
        collision_found = False
        collision_step = -1
        
        for i in range(steps + 1):
            t = min(i * step_size, distance)
            test_x = sx + dx * t
            test_y = sy + dy * t
            test_z = sz + dz * t
            
            test_pos = (test_x, test_y, test_z)
            
            # Get player bounding box at this position
            min_corner, max_corner = get_player_bounding_box(test_pos)
            blocks = get_blocks_in_bounding_box(min_corner, max_corner)
            
            # Check all potential blocks
            step_collision = False
            for block_pos in blocks:
                if block_pos in world:
                    if box_intersects_block(min_corner, max_corner, block_pos):
                        step_collision = True
                        collision_found = True
                        collision_step = i
                        print(f"   Step {i}: collision at {test_pos:.3f} with block {block_pos}")
                        print(f"   Player box: {min_corner} to {max_corner}")
                        break
            
            if step_collision:
                break
                
            # Print some debug steps
            if i % max(1, steps // 10) == 0:
                print(f"   Step {i}: pos={test_pos[0]:.3f}, {test_pos[1]:.3f}, {test_pos[2]:.3f}, blocks={blocks}")
        
        print(f"   Result: {'Collision found' if collision_found else 'No collision'} at step {collision_step}")
        print()
    
    # Now let's check manually what should happen
    print("Manual analysis:")
    print("Path goes from (9.5, 11.0, 9.5) to (11.5, 11.0, 11.5)")
    print("This path should cross through blocks at:")
    
    # Check specific positions along the path that should hit blocks
    check_positions = [
        (10.0, 11.0, 10.0),  # Quarter way
        (10.5, 11.0, 10.5),  # Middle
        (11.0, 11.0, 11.0),  # Three-quarters way
    ]
    
    for pos in check_positions:
        min_corner, max_corner = get_player_bounding_box(pos)
        blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        print(f"Position {pos}:")
        print(f"   Player box: {min_corner} to {max_corner}")
        print(f"   Blocks in range: {blocks}")
        
        collision = False
        for block_pos in blocks:
            if block_pos in world:
                intersects = box_intersects_block(min_corner, max_corner, block_pos)
                print(f"   Block {block_pos}: intersects={intersects}")
                if intersects:
                    collision = True
        
        print(f"   Overall collision: {collision}")
        print()
    
    # The key insight: let's check what blocks the player bounding box should intersect
    # when centered at different positions along the diagonal path
    print("Detailed bounding box analysis:")
    
    mid_pos = (10.5, 11.0, 10.5)
    min_corner, max_corner = get_player_bounding_box(mid_pos)
    
    print(f"Player at {mid_pos}:")
    print(f"   Bounding box: {min_corner} to {max_corner}")
    print(f"   Box X range: {min_corner[0]:.3f} to {max_corner[0]:.3f}")
    print(f"   Box Y range: {min_corner[1]:.3f} to {max_corner[1]:.3f}")
    print(f"   Box Z range: {min_corner[2]:.3f} to {max_corner[2]:.3f}")
    
    # Check intersection with each block individually
    for block_pos in world:
        bx, by, bz = block_pos
        print(f"\n   Block {block_pos} (from {bx} to {bx+1}, {by} to {by+1}, {bz} to {bz+1}):")
        
        # Manual intersection check
        x_intersect = min_corner[0] < bx + 1 and max_corner[0] > bx
        y_intersect = min_corner[1] < by + 1 and max_corner[1] > by  
        z_intersect = min_corner[2] < bz + 1 and max_corner[2] > bz
        
        print(f"      X intersect: {min_corner[0]:.3f} < {bx + 1} and {max_corner[0]:.3f} > {bx} = {x_intersect}")
        print(f"      Y intersect: {min_corner[1]:.3f} < {by + 1} and {max_corner[1]:.3f} > {by} = {y_intersect}")
        print(f"      Z intersect: {min_corner[2]:.3f} < {bz + 1} and {max_corner[2]:.3f} > {bz} = {z_intersect}")
        print(f"      Overall: {x_intersect and y_intersect and z_intersect}")

if __name__ == "__main__":
    debug_ray_casting()