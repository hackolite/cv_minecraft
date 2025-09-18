#!/usr/bin/env python3
"""
Debug the sliding collision system step by step.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box, 
    get_blocks_in_bounding_box, box_intersects_block
)

def debug_sliding_collision():
    """Debug the sliding collision system."""
    print("🔍 Debugging Sliding Collision System")
    print()
    
    # Create simple world - just one block
    world = {}
    
    # Ground plane
    for x in range(5, 16):
        for z in range(5, 16):
            world[(x, 10, z)] = "stone"
    
    # Single obstacle
    world[(10, 11, 10)] = "stone"
    
    print("World: Ground plane + single block at (10,11,10)")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test the failing case: diagonal movement around block
    start_pos = (9.2, 11.0, 9.2)
    end_pos = (10.8, 11.0, 10.8)
    
    print(f"Testing movement from {start_pos} to {end_pos}")
    print()
    
    # Check basic collision status
    print("1. Basic collision checks:")
    start_collision = detector.check_collision(start_pos)
    end_collision = detector.check_collision(end_pos)
    print(f"   Start collision: {start_collision}")
    print(f"   End collision: {end_collision}")
    print()
    
    # Try the full movement manually
    print("2. Full movement test:")
    if not detector.check_collision(end_pos):
        print("   ✅ Full movement is possible!")
    else:
        print("   ❌ Full movement blocked")
        
        # Debug the end position collision
        min_corner, max_corner = get_player_bounding_box(end_pos)
        blocks = get_blocks_in_bounding_box(min_corner, max_corner)
        
        print(f"   End position bounding box: {min_corner} to {max_corner}")
        print(f"   Blocks in range: {blocks}")
        
        for block_pos in blocks:
            if block_pos in world:
                intersects = box_intersects_block(min_corner, max_corner, block_pos)
                print(f"   Block {block_pos}: intersects={intersects}")
    print()
    
    # Test corner adjustment manually
    print("3. Corner adjustment test:")
    
    # Calculate movement direction
    dx = end_pos[0] - start_pos[0]  # 1.6
    dy = end_pos[1] - start_pos[1]  # 0.0
    dz = end_pos[2] - start_pos[2]  # 1.6
    
    print(f"   Movement: ({dx}, {dy}, {dz})")
    print(f"   Diagonal: {abs(dx) > 0.001 and abs(dz) > 0.001}")
    
    # Try manual corner adjustments
    adjustment_distances = [0.02, 0.05, 0.1, 0.15]
    
    for adj_dist in adjustment_distances:
        print(f"   Testing adjustment distance: {adj_dist}")
        
        # Try perpendicular adjustments
        movement_length = math.sqrt(dx*dx + dz*dz)
        if movement_length > 0:
            move_x = dx / movement_length
            move_z = dz / movement_length
            perp_x = -move_z  # Perpendicular
            perp_z = move_x
            
            for direction in [-1, 1]:
                adj_x = perp_x * direction * adj_dist
                adj_z = perp_z * direction * adj_dist
                test_pos = (end_pos[0] + adj_x, end_pos[1], end_pos[2] + adj_z)
                
                collision = detector.check_collision(test_pos)
                print(f"      Perp adjustment {direction} ({adj_x:+.3f}, {adj_z:+.3f}): collision={collision}")
                
                if not collision:
                    print(f"      ✅ Found working adjustment: {test_pos}")
                    break
        break  # Just test first distance for now
    
    print()
    
    # Test axis-by-axis sliding
    print("4. Axis-by-axis sliding test:")
    current_x, current_y, current_z = start_pos
    
    # Try X movement
    test_x_pos = (end_pos[0], current_y, current_z)
    x_collision = detector.check_collision(test_x_pos)
    print(f"   X movement to {test_x_pos}: collision={x_collision}")
    if not x_collision:
        current_x = end_pos[0]
        print(f"   ✅ X movement allowed, new pos: ({current_x}, {current_y}, {current_z})")
    
    # Try Z movement
    test_z_pos = (current_x, current_y, end_pos[2])
    z_collision = detector.check_collision(test_z_pos)
    print(f"   Z movement to {test_z_pos}: collision={z_collision}")
    if not z_collision:
        current_z = end_pos[2]
        print(f"   ✅ Z movement allowed, new pos: ({current_x}, {current_y}, {current_z})")
    
    print(f"   Final sliding result: ({current_x}, {current_y}, {current_z})")
    
    # Calculate efficiency
    intended_distance = math.sqrt(dx*dx + dz*dz)
    actual_dx = current_x - start_pos[0]
    actual_dz = current_z - start_pos[2]
    actual_distance = math.sqrt(actual_dx*actual_dx + actual_dz*actual_dz)
    efficiency = actual_distance / intended_distance
    print(f"   Sliding efficiency: {efficiency:.1%}")
    print()
    
    # Compare with actual system
    print("5. Actual collision system result:")
    safe_pos, collision_info = detector.resolve_collision(start_pos, end_pos)
    print(f"   System result: {safe_pos}")
    print(f"   Collision info: {collision_info}")
    
    actual_dx = safe_pos[0] - start_pos[0]
    actual_dz = safe_pos[2] - start_pos[2]
    actual_distance = math.sqrt(actual_dx*actual_dx + actual_dz*actual_dz)
    efficiency = actual_distance / intended_distance
    print(f"   System efficiency: {efficiency:.1%}")

if __name__ == "__main__":
    debug_sliding_collision()