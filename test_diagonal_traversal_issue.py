#!/usr/bin/env python3
"""
Test to reproduce the specific issue: "quand x augmente et z augmente, l'utilisateur traverse le block"
(When x increases and z increases, the user traverses through the block)

This test will specifically check diagonal movement in the +X +Z direction to identify the traversal bug.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_diagonal_traversal_issue():
    """Test the specific diagonal traversal issue when both X and Z increase."""
    print("🔍 Testing Diagonal Traversal Issue: X↗️ Z↗️")
    print("=" * 60)
    
    # Create a simple world with a single block that should block diagonal movement
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at position: (5, 10, 5)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print()
    
    # Test cases for diagonal movement in +X +Z direction
    test_cases = [
        {
            'name': 'Small Diagonal Movement (+X +Z)',
            'start': (4.3, 10.5, 4.3),   # Just outside the block corner
            'end': (5.7, 10.5, 5.7),     # Should pass through the block diagonally
            'description': 'Small step diagonal movement through block corner'
        },
        {
            'name': 'Large Diagonal Movement (+X +Z)',
            'start': (4.0, 10.5, 4.0),   # Further outside
            'end': (6.0, 10.5, 6.0),     # Should definitely pass through the block
            'description': 'Large step diagonal movement through block'
        },
        {
            'name': 'Edge Case Diagonal (+X +Z)',
            'start': (4.5, 10.5, 4.5),   # Close to block edge
            'end': (5.5, 10.5, 5.5),     # Right through block center
            'description': 'Movement from edge to center of block'
        },
        {
            'name': 'Fast Diagonal Movement (+X +Z)',
            'start': (3.0, 10.5, 3.0),   # Far outside
            'end': (7.0, 10.5, 7.0),     # Far past the block
            'description': 'Fast movement that should be blocked by block'
        }
    ]
    
    traversal_detected = False
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   {test_case['description']}")
        print(f"   Start: {test_case['start']}")
        print(f"   End:   {test_case['end']}")
        
        # Test the movement
        start_pos = test_case['start']
        target_pos = test_case['end']
        
        # Check if start position has collision
        start_collision = manager.check_block_collision(start_pos)
        print(f"   Start collision: {start_collision}")
        
        # Check if target position has collision  
        target_collision = manager.check_block_collision(target_pos)
        print(f"   Target collision: {target_collision}")
        
        # Resolve the movement
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check if traversal occurred
        # If the player moves significantly closer to or past the block, it's traversal
        start_distance_to_block = max(abs(start_pos[0] - 5.5), abs(start_pos[2] - 5.5))
        safe_distance_to_block = max(abs(safe_pos[0] - 5.5), abs(safe_pos[2] - 5.5))
        
        # If the safe position is closer to the block center than start, traversal might have occurred
        if safe_distance_to_block < start_distance_to_block * 0.8:
            print(f"   ⚠️  Possible traversal detected! Distance reduced from {start_distance_to_block:.2f} to {safe_distance_to_block:.2f}")
            traversal_detected = True
        
        # Check if the player ended up on the opposite side of the block
        start_x_side = 1 if start_pos[0] > 5.5 else -1
        start_z_side = 1 if start_pos[2] > 5.5 else -1
        safe_x_side = 1 if safe_pos[0] > 5.5 else -1
        safe_z_side = 1 if safe_pos[2] > 5.5 else -1
        
        if (start_x_side != safe_x_side or start_z_side != safe_z_side) and not any(collision_info.values()):
            print(f"   ❌ TRAVERSAL DETECTED! Player crossed to opposite side without collision")
            traversal_detected = True
        
        print()
    
    # Test specifically problematic case
    print("🚨 SPECIFIC TRAVERSAL TEST:")
    print("Testing movement from (4.0, 10.5, 4.0) to (6.0, 10.5, 6.0)")
    print("This should be BLOCKED by the stone block at (5, 10, 5)")
    
    start = (4.0, 10.5, 4.0)
    end = (6.0, 10.5, 6.0)
    
    safe_pos, collision_info = manager.resolve_collision(start, end)
    
    print(f"Start: {start}")
    print(f"Target: {end}")
    print(f"Result: {safe_pos}")
    print(f"Collision: {collision_info}")
    
    # This should NOT allow the player to reach (6.0, 10.5, 6.0)
    # The player should be stopped before the block
    if abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1:
        print("❌ TRAVERSAL BUG CONFIRMED: Player reached target despite block!")
        traversal_detected = True
    else:
        print("✅ Movement correctly blocked by collision system")
    
    return not traversal_detected

def test_all_diagonal_directions():
    """Test diagonal movement in all four directions to see if the issue is specific to +X +Z."""
    print("\n🧭 Testing All Diagonal Directions")
    print("=" * 40)
    
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    directions = [
        ("➡️⬆️ (+X +Z)", (4.0, 10.5, 4.0), (6.0, 10.5, 6.0)),
        ("⬅️⬆️ (-X +Z)", (6.0, 10.5, 4.0), (4.0, 10.5, 6.0)), 
        ("➡️⬇️ (+X -Z)", (4.0, 10.5, 6.0), (6.0, 10.5, 4.0)),
        ("⬅️⬇️ (-X -Z)", (6.0, 10.5, 6.0), (4.0, 10.5, 4.0)),
    ]
    
    for name, start, end in directions:
        print(f"{name}: {start} → {end}")
        safe_pos, collision_info = manager.resolve_collision(start, end)
        
        # Check if reached target (indicating traversal)
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        if reached_target:
            print(f"   ❌ TRAVERSAL: Reached {safe_pos}")
        else:
            print(f"   ✅ BLOCKED: Stopped at {safe_pos}")
    
    print()

def main():
    """Run diagonal traversal issue tests."""
    print("🐛 Diagnosing Diagonal Block Traversal Issue")
    print("Issue: 'quand x augmente et z augmente, l'utilisateur traverse le block'")
    print()
    
    try:
        test_all_diagonal_directions()
        success = test_diagonal_traversal_issue()
        
        if success:
            print("\n✅ NO TRAVERSAL ISSUES DETECTED")
            print("The collision system correctly prevents diagonal traversal.")
        else:
            print("\n❌ TRAVERSAL ISSUE CONFIRMED")
            print("The collision system allows players to traverse through blocks diagonally.")
            print("This needs to be fixed!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)