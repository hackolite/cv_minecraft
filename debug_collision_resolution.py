#!/usr/bin/env python3
"""
Debug the specific collision case that's causing traversal issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def debug_specific_case():
    """Debug the specific case that's causing issues."""
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("=== DEBUGGING COLLISION DETECTION ===")
    print(f"Block at: (5, 10, 5)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT}")
    print()
    
    # Test specific positions
    test_positions = [
        (4.0, 10.5, 4.0),    # Start position - should be safe
        (6.0, 10.5, 6.0),    # End position - should collide  
        (6.0, 10.5, 4.0),    # Intermediate position - might be the issue
        (5.5, 10.5, 5.5),    # Block center - should definitely collide
        (5.0, 10.5, 5.0),    # Block corner - should collide
    ]
    
    for pos in test_positions:
        collision = manager.check_block_collision(pos)
        print(f"Position {pos}: {'COLLISION' if collision else 'SAFE'}")
        
        # Show player bounding box for this position
        px, py, pz = pos
        half_width = PLAYER_WIDTH / 2
        min_x = px - half_width
        max_x = px + half_width
        min_y = py
        max_y = py + PLAYER_HEIGHT
        min_z = pz - half_width
        max_z = pz + half_width
        
        print(f"  Player AABB: ({min_x}, {min_y}, {min_z}) to ({max_x}, {max_y}, {max_z})")
        
        # Check if this intersects with block (5,10,5) which spans (5,10,5) to (6,11,6)
        block_intersects = (min_x < 6 and max_x > 5 and
                           min_y < 11 and max_y > 10 and
                           min_z < 6 and max_z > 5)
        
        print(f"  Should intersect with block (5,10,5): {block_intersects}")
        print(f"  Actual collision detection: {collision}")
        
        if block_intersects != collision:
            print(f"  ❌ MISMATCH! Expected {block_intersects}, got {collision}")
        print()

def debug_movement_resolution():
    """Debug the movement resolution process."""
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print("=== DEBUGGING MOVEMENT RESOLUTION ===")
    
    start = (4.0, 10.5, 4.0)
    end = (6.0, 10.5, 6.0)
    
    print(f"Movement: {start} → {end}")
    
    # Step through the resolution process
    print("\n1. Check if start position is safe:")
    start_safe = not manager._is_position_in_block(start)
    print(f"   Start position safe: {start_safe}")
    
    print("\n2. Check if end position is safe:")
    end_safe = not manager._is_position_in_block(end)
    print(f"   End position safe: {end_safe}")
    
    print("\n3. Since end position is not safe, find safe position:")
    
    # Simulate the _find_safe_position logic
    old_x, old_y, old_z = start
    new_x, new_y, new_z = end
    safe_pos = list(start)
    
    print(f"   Starting with old position: {safe_pos}")
    
    # Test X movement
    if new_x != old_x:
        test_x_pos = (new_x, safe_pos[1], safe_pos[2])
        x_safe = not manager._is_position_in_block(test_x_pos)
        print(f"   Test X movement to {test_x_pos}: {'SAFE' if x_safe else 'BLOCKED'}")
        if x_safe:
            safe_pos[0] = new_x
            print(f"   Updated position: {safe_pos}")
    
    # Test Y movement  
    if new_y != old_y:
        test_y_pos = (safe_pos[0], new_y, safe_pos[2])
        y_safe = not manager._is_position_in_block(test_y_pos)
        print(f"   Test Y movement to {test_y_pos}: {'SAFE' if y_safe else 'BLOCKED'}")
        if y_safe:
            safe_pos[1] = new_y
            print(f"   Updated position: {safe_pos}")
    
    # Test Z movement
    if new_z != old_z:
        test_z_pos = (safe_pos[0], safe_pos[1], new_z)
        z_safe = not manager._is_position_in_block(test_z_pos)
        print(f"   Test Z movement to {test_z_pos}: {'SAFE' if z_safe else 'BLOCKED'}")
        if z_safe:
            safe_pos[2] = new_z
            print(f"   Updated position: {safe_pos}")
    
    print(f"\n4. Final position before verification: {safe_pos}")
    
    # Final verification
    final_safe = not manager._is_position_in_block(tuple(safe_pos))
    print(f"   Final position safe: {final_safe}")
    
    if not final_safe:
        print(f"   Reverting to old position: {start}")
        safe_pos = list(start)
    
    print(f"\n5. Result: {tuple(safe_pos)}")
    
    # Compare with actual result
    actual_result, collision_info = manager.resolve_collision(start, end)
    print(f"   Actual method result: {actual_result}")
    print(f"   Collision info: {collision_info}")

if __name__ == "__main__":
    debug_specific_case()
    debug_movement_resolution()