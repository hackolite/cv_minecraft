#!/usr/bin/env python3
"""
Test the corner adjustment logic specifically.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, get_player_bounding_box, 
    get_blocks_in_bounding_box, box_intersects_block
)

def test_corner_adjustment():
    """Test the corner adjustment feature."""
    print("🔍 Testing Corner Adjustment Logic")
    print()
    
    # Create the same world from the failing test
    world = {}
    
    # Ground plane at Y=10
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"
    
    # Wall blocks at Y=11 - only the problematic corner
    wall_blocks = [(10, 11, 10)]  # Just one corner block
    for pos in wall_blocks:
        world[pos] = "stone"
    
    print("Simplified world:")
    print("   Ground plane and one wall block at (10, 11, 10)")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test the specific failing case: movement from (9.0, 11.0, 9.0) to (12.0, 11.0, 12.0)
    start_pos = (9.0, 11.0, 9.0)
    end_pos = (12.0, 11.0, 12.0)
    
    print(f"Testing movement from {start_pos} to {end_pos}")
    print()
    
    # Check manual corner adjustment
    print("Manual corner adjustment analysis:")
    
    # Calculate movement direction
    dx = end_pos[0] - start_pos[0]  # 3.0
    dy = end_pos[1] - start_pos[1]  # 0.0
    dz = end_pos[2] - start_pos[2]  # 3.0
    
    print(f"Movement vector: ({dx}, {dy}, {dz})")
    print(f"Diagonal movement: {abs(dx) > 0.001 and abs(dz) > 0.001}")
    print()
    
    # Test corner adjustment at different points along the path
    test_positions = [
        (9.0, 11.0, 9.0),   # Start
        (10.0, 11.0, 10.0), # Near corner
        (10.5, 11.0, 10.5), # At corner  
        (11.0, 11.0, 11.0), # Past corner
        (12.0, 11.0, 12.0), # End
    ]
    
    for pos in test_positions:
        print(f"Position {pos}:")
        
        # Check basic collision
        collision = detector.check_collision(pos)
        print(f"   Basic collision: {collision}")
        
        if collision:
            # Try manual corner adjustments
            adjustment_distance = 0.05
            found_adjustment = False
            
            for x_adj in [-adjustment_distance, 0, adjustment_distance]:
                for z_adj in [-adjustment_distance, 0, adjustment_distance]:
                    if x_adj == 0 and z_adj == 0:
                        continue
                    
                    test_pos = (pos[0] + x_adj, pos[1], pos[2] + z_adj)
                    test_collision = detector.check_collision(test_pos)
                    
                    if not test_collision:
                        print(f"   ✅ Adjustment ({x_adj:+.2f}, {z_adj:+.2f}) works: {test_pos}")
                        found_adjustment = True
                        break
                if found_adjustment:
                    break
            
            if not found_adjustment:
                print(f"   ❌ No corner adjustment found")
        
        print()
    
    # Test the full collision resolution
    print("Full collision resolution test:")
    safe_pos, collision_info = detector.resolve_collision(start_pos, end_pos)
    print(f"   Start: {start_pos}")
    print(f"   Desired: {end_pos}")
    print(f"   Result: {safe_pos}")
    print(f"   Collision info: {collision_info}")
    
    # Calculate movement efficiency
    intended_dx = end_pos[0] - start_pos[0]
    intended_dz = end_pos[2] - start_pos[2]
    intended_distance = math.sqrt(intended_dx**2 + intended_dz**2)
    
    actual_dx = safe_pos[0] - start_pos[0]
    actual_dz = safe_pos[2] - start_pos[2]
    actual_distance = math.sqrt(actual_dx**2 + actual_dz**2)
    
    efficiency = actual_distance / intended_distance if intended_distance > 0 else 1.0
    print(f"   Movement efficiency: {efficiency:.1%}")

if __name__ == "__main__":
    test_corner_adjustment()