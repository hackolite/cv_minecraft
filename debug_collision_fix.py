#!/usr/bin/env python3
"""
Debug test pour comprendre pourquoi le fix ne fonctionne pas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def debug_x_axis_resolution():
    """Debug the X-axis resolution logic."""
    print("🔧 Debug X-Axis Resolution")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Test case that should be fixed
    old_x = 4.8
    new_x = 5.2
    y = 10.5
    z = 4.3  # Outside the block in Z
    
    print(f"Input: old_x={old_x}, new_x={new_x}, y={y}, z={z}")
    print(f"Block at: (5, 10, 5)")
    print()
    
    # Test the new resolution method directly
    result_x = manager._resolve_x_axis_movement(old_x, new_x, y, z, "debug")
    
    print(f"Result X: {result_x}")
    print(f"Expected X: should be <= 4.5 (block_x - player_width/2 = 5.0 - 0.5)")
    
    # Check what should happen:
    # Player at old_x=4.8 going to new_x=5.2
    # Player bounds at new_x: [5.2-0.5, 5.2+0.5] = [4.7, 5.7]
    # Block bounds: [5.0, 6.0]
    # These overlap, so collision should occur
    # Safe position should be x = 5.0 - 0.5 = 4.5
    
    player_bounds_new = (new_x - 0.5, new_x + 0.5)
    block_bounds = (5.0, 6.0)
    overlap = player_bounds_new[0] < block_bounds[1] and player_bounds_new[1] > block_bounds[0]
    
    print(f"Player bounds at new_x: {player_bounds_new}")
    print(f"Block bounds: {block_bounds}")
    print(f"Should overlap: {overlap}")
    
    if overlap:
        expected_safe_x = 5.0 - 0.5
        print(f"Expected safe X: {expected_safe_x}")
        
        if abs(result_x - expected_safe_x) > 0.001:
            print(f"❌ BUG: result_x={result_x} != expected={expected_safe_x}")
        else:
            print(f"✅ Correct result")
    
    print()

def debug_full_collision_resolution():
    """Debug the full collision resolution."""
    print("🔧 Debug Full Collision Resolution")
    print("=" * 50)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    # Test the problematic diagonal movement
    start = (4.8, 10.5, 4.3)
    end = (5.2, 10.5, 5.7)
    
    print(f"Start: {start}")
    print(f"End: {end}")
    print()
    
    # Debug step by step
    print("Step-by-step resolution:")
    
    # Should the end position be in collision?
    end_collision = manager.check_block_collision(end)
    print(f"End position collision: {end_collision}")
    
    # Resolve collision
    safe_pos, collision_info = manager.resolve_collision(start, end)
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Check if final position has collision
    final_collision = manager.check_block_collision(safe_pos)
    print(f"Final position collision: {final_collision}")
    
    # Analyze what went wrong
    safe_x, safe_y, safe_z = safe_pos
    player_right_edge = safe_x + 0.5
    player_front_edge = safe_z + 0.5
    
    print(f"Player right edge: {player_right_edge} (should be <= 5.0)")
    print(f"Player front edge: {player_front_edge} (should be <= 5.0)")
    
    if player_right_edge > 5.0:
        print(f"❌ X+ penetration: {player_right_edge - 5.0}")
    if player_front_edge > 5.0:
        print(f"❌ Z+ penetration: {player_front_edge - 5.0}")

def main():
    debug_x_axis_resolution()
    debug_full_collision_resolution()

if __name__ == "__main__":
    main()