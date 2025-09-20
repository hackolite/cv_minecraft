#!/usr/bin/env python3
"""
Test to validate the collision detection fix for the issue:
"je rentre dans certains cubes, pas tous, pk ?" 
(I enter into certain cubes, not all, why?)

This test validates that our fix ensures consistent collision detection
by using proper bounding box collision detection instead of simple center-point checking.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_collision_consistency_fix():
    """Test that collision detection is now consistent across all blocks."""
    print("🎯 TESTING COLLISION CONSISTENCY FIX")
    print("=" * 60)
    print(f"Player dimensions: {PLAYER_WIDTH}x{PLAYER_WIDTH}x{PLAYER_HEIGHT}")
    print()
    
    # Create a world with multiple blocks in different configurations
    world = {
        (0, 0, 0): 'stone',    # Ground block
        (1, 0, 0): 'stone',    # Adjacent ground block
        (0, 1, 0): 'stone',    # Wall block
        (5, 5, 5): 'stone',    # Isolated block
        (10, 10, 10): 'stone', # Another isolated block
    }
    
    manager = UnifiedCollisionManager(world)
    
    print("🧪 Test 1: Player trying to enter blocks at different positions")
    print("-" * 50)
    
    # Test positions where player bounding box would intersect with blocks
    test_cases = [
        # Player position, Expected collision, Description
        ((0.5, 0.5, 0.5), True, "Inside ground block (0,0,0)"),
        ((1.5, 0.5, 0.5), True, "Inside adjacent ground block (1,0,0)"),
        ((0.5, 1.5, 0.5), True, "Inside wall block (0,1,0)"),
        ((5.5, 5.5, 5.5), True, "Inside isolated block (5,5,5)"),
        ((10.5, 10.5, 10.5), True, "Inside isolated block (10,10,10)"),
        
        # Safe positions that should not collide
        ((0.5, 2.0, 0.5), False, "Above ground blocks"),
        ((3.0, 3.0, 3.0), False, "In empty space"),
        ((7.0, 7.0, 7.0), False, "In empty space between blocks"),
        ((-2.0, 0.5, 0.5), False, "Far from any blocks"),
    ]
    
    all_correct = True
    for position, expected_collision, description in test_cases:
        actual_collision = manager.check_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {description}: collision = {actual_collision}")
        
        if actual_collision != expected_collision:
            all_correct = False
            print(f"      ERROR: Expected {expected_collision}, got {actual_collision}")
    
    print()
    print("🧪 Test 2: Player at block boundaries")
    print("-" * 50)
    
    # Test edge cases at block boundaries where the original bug might occur
    boundary_cases = [
        # Position just at the edge of block boundaries
        ((0.0, 1.0, 0.0), True, "At corner of ground block"),
        ((1.0, 1.0, 0.0), True, "At edge between ground blocks"),
        ((-0.51, 1.0, 0.0), False, "Just outside block collision range"),
        ((-0.49, 1.0, 0.0), True, "Just inside block collision range"),
    ]
    
    for position, expected_collision, description in boundary_cases:
        actual_collision = manager.check_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {description}: collision = {actual_collision}")
        
        if actual_collision != expected_collision:
            all_correct = False
            print(f"      ERROR: Expected {expected_collision}, got {actual_collision}")
    
    print()
    print("🧪 Test 3: Movement resolution consistency")
    print("-" * 50)
    
    # Test that movement resolution works consistently
    movement_cases = [
        # (start_pos, target_pos, expected_blocking)
        ((2.0, 1.5, 0.0), (0.5, 1.5, 0.0), True),   # Moving into wall block at (0,1,0)
        ((2.0, 2.0, 2.0), (5.5, 2.0, 2.0), False),  # Moving to empty space between blocks
        ((2.0, 2.0, 2.0), (3.0, 2.0, 2.0), False),  # Moving to completely empty space
    ]
    
    for start_pos, target_pos, expected_blocking in movement_cases:
        resolved_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        is_blocked = any(collision_info[axis] for axis in ['x', 'y', 'z'])
        status = "✅" if is_blocked == expected_blocking else "❌"
        print(f"   {status} Move {start_pos} → {target_pos}: blocked = {is_blocked}")
        
        if is_blocked != expected_blocking:
            all_correct = False
            print(f"      ERROR: Expected blocking = {expected_blocking}, got {is_blocked}")
    
    print()
    print("📊 RESULTS")
    print("=" * 60)
    
    if all_correct:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Collision detection is now consistent across all blocks")
        print("✅ Players cannot enter ANY blocks inappropriately")
        print("✅ The 'je rentre dans certains cubes' issue is FIXED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("❌ Collision detection still has inconsistencies")
        return False

if __name__ == "__main__":
    success = test_collision_consistency_fix()
    sys.exit(0 if success else 1)