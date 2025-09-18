#!/usr/bin/env python3
"""
Debug the specific ray casting issue where movement through open areas is blocked.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box, 
    get_blocks_in_bounding_box, box_intersects_block
)

def debug_specific_ray_casting_issue():
    """Debug why ray casting blocks movement through open areas."""
    print("🔍 Debugging Ray Casting Over-Blocking Issue")
    print()
    
    # Create the exact world from the failing test
    world = {}
    
    # Ground plane at Y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    # Wall blocks at Y=11
    wall_blocks = [(10, 11, 10), (11, 11, 10), (10, 11, 11), (11, 11, 11)]
    for pos in wall_blocks:
        world[pos] = "stone"
    
    print("World blocks:")
    for pos in sorted(world.keys()):
        print(f"   {world[pos]} at {pos}")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # The failing case: should be free movement
    start_pos = (9.0, 11.0, 9.0)
    end_pos = (12.0, 11.0, 12.0)
    
    print(f"Analyzing movement from {start_pos} to {end_pos}")
    print(f"This path should be clear - both points are in open air")
    print()
    
    # Check if start and end positions have collisions
    print("Position checks:")
    start_collision = detector.check_collision(start_pos)
    end_collision = detector.check_collision(end_pos)
    print(f"   Start {start_pos} collision: {start_collision}")
    print(f"   End {end_pos} collision: {end_collision}")
    print()
    
    # Manual ray casting analysis
    sx, sy, sz = start_pos
    ex, ey, ez = end_pos
    
    dx = ex - sx  # 3.0
    dy = ey - sy  # 0.0  
    dz = ez - sz  # 3.0
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)  # ~4.24
    
    print(f"Ray casting parameters:")
    print(f"   Direction: ({dx}, {dy}, {dz})")
    print(f"   Distance: {distance:.3f}")
    print(f"   Normalized: ({dx/distance:.3f}, {dy/distance:.3f}, {dz/distance:.3f})")
    print()
    
    # Use the same step size as the physics system
    step_size = 0.1
    steps = int(distance / step_size) + 1
    
    print(f"Ray casting with step size {step_size}, {steps} steps:")
    
    for i in range(min(steps + 1, 20)):  # Limit output
        t = min(i * step_size, distance)
        test_x = sx + (dx / distance) * t
        test_y = sy + (dy / distance) * t  
        test_z = sz + (dz / distance) * t
        
        test_pos = (test_x, test_y, test_z)
        
        # Get player bounding box at this position
        min_corner, max_corner = get_player_bounding_box(test_pos)
        blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        print(f"   Step {i:2d}: pos=({test_x:.2f}, {test_y:.2f}, {test_z:.2f})")
        print(f"         Box: ({min_corner[0]:.2f}, {min_corner[1]:.2f}, {min_corner[2]:.2f}) to ({max_corner[0]:.2f}, {max_corner[1]:.2f}, {max_corner[2]:.2f})")
        print(f"         Blocks in range: {sorted(blocks)}")
        
        # Check each block for collision
        collision_found = False
        for block_pos in blocks:
            if block_pos in world:
                intersects = box_intersects_block(min_corner, max_corner, block_pos)
                if intersects:
                    print(f"         🚨 COLLISION with block {block_pos} ({world[block_pos]})")
                    collision_found = True
                    
                    # Detailed intersection analysis
                    bx, by, bz = block_pos
                    print(f"            Block bounds: ({bx}, {by}, {bz}) to ({bx+1}, {by+1}, {bz+1})")
                    
                    # Check each axis
                    x_overlap = min_corner[0] < bx + 1 and max_corner[0] > bx
                    y_overlap = min_corner[1] < by + 1 and max_corner[1] > by
                    z_overlap = min_corner[2] < bz + 1 and max_corner[2] > bz
                    
                    print(f"            X overlap: {min_corner[0]:.3f} < {bx+1} and {max_corner[0]:.3f} > {bx} = {x_overlap}")
                    print(f"            Y overlap: {min_corner[1]:.3f} < {by+1} and {max_corner[1]:.3f} > {by} = {y_overlap}")
                    print(f"            Z overlap: {min_corner[2]:.3f} < {bz+1} and {max_corner[2]:.3f} > {bz} = {z_overlap}")
                    
                    break
        
        if collision_found:
            print(f"         ❌ Ray casting would stop here!")
            break
        else:
            print(f"         ✅ No collision at this step")
    
    print()
    print("Key insights:")
    print("   - Path should be clear since player moves diagonally through open space")
    print("   - If collision detected, it means ray casting is incorrectly intersecting wall blocks")
    print("   - Player bounding box is 0.6×1.8, so should have clearance around walls")

if __name__ == "__main__":
    debug_specific_ray_casting_issue()