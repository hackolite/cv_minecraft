#!/usr/bin/env python3
"""
Debug the specific case that's still failing: -X +Z traversal.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def debug_failing_case():
    """Debug the -X +Z case that's still allowing traversal."""
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("=== DEBUGGING FAILING CASE: -X +Z ===")
    print(f"Block at: (5, 10, 5) - spans from (5,10,5) to (6,11,6)")
    print()
    
    start = (6.0, 10.5, 4.0)
    end = (4.0, 10.5, 6.0)
    
    print(f"Movement: {start} → {end}")
    print()
    
    # Step 1: Check path intersection
    print("1. Checking path intersection:")
    samples = 16
    path_intersects = False
    for i in range(1, samples):
        t = i / samples
        sample_x = start[0] + t * (end[0] - start[0])
        sample_y = start[1] + t * (end[1] - start[1])
        sample_z = start[2] + t * (end[2] - start[2])
        sample_pos = (sample_x, sample_y, sample_z)
        
        collision = manager._is_position_in_block(sample_pos)
        print(f"   Sample {i}: {sample_pos} - {'COLLISION' if collision else 'SAFE'}")
        
        if collision:
            path_intersects = True
            print(f"   ❌ Path intersection detected at sample {i}")
            break
    
    if not path_intersects:
        print("   ✅ No path intersection detected")
    
    print()
    
    # Step 2: Test the _path_intersects_blocks method directly
    print("2. Testing _path_intersects_blocks method:")
    method_result = manager._path_intersects_blocks(start, end)
    print(f"   Method result: {method_result}")
    print()
    
    # Step 3: Test axis-by-axis movement
    print("3. Testing axis-by-axis movement:")
    
    safe_pos = list(start)
    print(f"   Starting position: {safe_pos}")
    
    # Test X movement
    new_x = end[0]
    if new_x != start[0]:
        test_x_pos = (new_x, safe_pos[1], safe_pos[2])
        x_pos_safe = not manager._is_position_in_block(test_x_pos)
        x_path_safe = not manager._path_intersects_blocks((safe_pos[0], safe_pos[1], safe_pos[2]), test_x_pos)
        
        print(f"   Test X movement to {test_x_pos}:")
        print(f"     Position safe: {x_pos_safe}")
        print(f"     Path safe: {x_path_safe}")
        
        if x_pos_safe and x_path_safe:
            safe_pos[0] = new_x
            print(f"     ✅ X movement allowed: {safe_pos}")
        else:
            print(f"     🚫 X movement blocked")
    
    # Test Z movement
    new_z = end[2]
    if new_z != start[2]:
        test_z_pos = (safe_pos[0], safe_pos[1], new_z)
        z_pos_safe = not manager._is_position_in_block(test_z_pos)
        z_path_safe = not manager._path_intersects_blocks((safe_pos[0], safe_pos[1], safe_pos[2]), test_z_pos)
        
        print(f"   Test Z movement to {test_z_pos}:")
        print(f"     Position safe: {z_pos_safe}")
        print(f"     Path safe: {z_path_safe}")
        
        if z_pos_safe and z_path_safe:
            safe_pos[2] = new_z
            print(f"     ✅ Z movement allowed: {safe_pos}")
        else:
            print(f"     🚫 Z movement blocked")
    
    print(f"   Final calculated position: {tuple(safe_pos)}")
    print()
    
    # Step 4: Compare with actual method result
    print("4. Actual method result:")
    actual_result, collision_info = manager.resolve_collision(start, end)
    print(f"   Result: {actual_result}")
    print(f"   Collision info: {collision_info}")

if __name__ == "__main__":
    debug_failing_case()