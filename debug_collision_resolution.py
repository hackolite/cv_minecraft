#!/usr/bin/env python3
"""
Debug the collision resolution to understand why ground detection is failing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def debug_collision_resolution():
    """Debug the collision resolution issue."""
    print("🔍 Debugging Collision Resolution")
    print("=" * 50)
    
    # Create a world identical to the failing test
    world = {
        (0, 0, 0): 'stone',
        (1, 0, 0): 'stone',
        (0, 0, 1): 'stone',
        (1, 0, 1): 'stone',
        (0, 2, 0): 'stone',  # Wall
    }
    
    manager = UnifiedCollisionManager(world)
    
    # Test the exact scenario that's failing
    old_pos = (0.5, 5.0, 0.5)  # High above platform
    new_pos = (0.5, 0.5, 0.5)  # Trying to move into platform
    
    print(f"Old position: {old_pos}")
    print(f"New position: {new_pos}")
    
    # Check collision at new position
    collision_at_new = manager._is_position_in_block(new_pos)
    print(f"Collision at new position: {collision_at_new}")
    
    # Check safe position
    if collision_at_new:
        safe_pos = manager._find_safe_position(old_pos, new_pos)
        print(f"Safe position from _find_safe_position: {safe_pos}")
    
    # Call resolve_collision
    safe_pos, collision_info = manager.resolve_collision(old_pos, new_pos)
    print(f"Final safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Check ground detection separately
    ground_test_pos = (safe_pos[0], safe_pos[1] - 0.05, safe_pos[2])
    ground_collision = manager._is_position_in_block(ground_test_pos)
    print(f"Ground test position: {ground_test_pos}")
    print(f"Ground collision: {ground_collision}")
    
    # Expected behavior
    print(f"\n📋 Expected behavior:")
    print(f"   - Safe position should be around (0.5, 1.0, 0.5) - on top of block")
    print(f"   - Y collision should be True")
    print(f"   - Ground should be True")

if __name__ == "__main__":
    debug_collision_resolution()