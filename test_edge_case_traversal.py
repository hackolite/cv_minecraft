#!/usr/bin/env python3
"""
More comprehensive test for edge cases in single-axis movement.

This test explores potential edge cases in single-axis traversal,
including movements at block boundaries and near-edge positions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_edge_case_x_traversal():
    """Test edge cases for X-axis traversal that might allow passage."""
    print("🔍 Testing Edge Cases - X-Axis Traversal")
    print("=" * 50)
    
    # Create a simple world with a single block
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at position: (5, 10, 5) (occupies 5.0-6.0 in all dimensions)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print(f"Player extends ±{PLAYER_WIDTH/2} from center")
    print()
    
    # Test cases that might allow traversal due to floating point precision or edge cases
    test_cases = [
        {
            'name': 'X-Movement At Exact Block Edge (Z=4.5)',
            'start': (4.0, 10.5, 4.5),   # Player center at 4.5, extends to 5.0 in Z
            'end': (6.0, 10.5, 4.5),     # Should be blocked since player extends into block
            'description': 'Player edge exactly touches block edge - should be blocked'
        },
        {
            'name': 'X-Movement Just Outside Block (Z=4.49)',
            'start': (4.0, 10.5, 4.49),  # Player center at 4.49, extends to 4.99 in Z
            'end': (6.0, 10.5, 4.49),    # Should be allowed since player doesn\'t touch block
            'description': 'Player just outside block - should be allowed'
        },
        {
            'name': 'X-Movement Just Inside Block (Z=4.51)',
            'start': (4.0, 10.5, 4.51),  # Player center at 4.51, extends to 5.01 in Z
            'end': (6.0, 10.5, 4.51),    # Should be blocked since player overlaps block
            'description': 'Player barely overlaps block - should be blocked'
        },
        {
            'name': 'X-Movement Through Block Corner',
            'start': (4.0, 10.5, 5.49),  # Player extends from 4.99 to 5.99 in Z
            'end': (6.0, 10.5, 5.49),    # Should be blocked
            'description': 'Movement through corner of block - should be blocked'
        },
        {
            'name': 'X-Movement at Y Boundary',
            'start': (4.0, 9.5, 5.5),    # Player extends from y=9.5 to y=10.5 (touches block bottom)
            'end': (6.0, 9.5, 5.5),      # Should be blocked
            'description': 'Movement at Y boundary touching block - should be blocked'
        }
    ]
    
    issues_found = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   {test_case['description']}")
        print(f"   Start: {test_case['start']}")
        print(f"   End:   {test_case['end']}")
        
        start_pos = test_case['start']
        target_pos = test_case['end']
        
        # Check if start position has collision
        start_collision = manager.check_block_collision(start_pos)
        print(f"   Start collision: {start_collision}")
        
        # Check if target position has collision
        target_collision = manager.check_block_collision(target_pos)
        print(f"   Target collision: {target_collision}")
        
        # Test movement resolution
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check if the movement behaves as expected
        x_moved = abs(safe_pos[0] - start_pos[0])
        expected_x_movement = abs(target_pos[0] - start_pos[0])
        
        # For cases where player should be outside block (like Z=4.49), movement should be allowed
        if test_case['name'].find('Just Outside') != -1:
            if x_moved < expected_x_movement * 0.9:
                print(f"   ❌ UNEXPECTED BLOCK: Player should move but was blocked")
                issues_found.append(test_case['name'])
            else:
                print(f"   ✅ CORRECTLY ALLOWED: Player moved {x_moved:.3f} in X")
        else:
            # For all other cases, movement should be blocked
            if x_moved >= expected_x_movement * 0.9:
                print(f"   ❌ TRAVERSAL DETECTED: Player moved {x_moved:.3f} in X (expected block)")
                issues_found.append(test_case['name'])
            else:
                print(f"   ✅ CORRECTLY BLOCKED: Player moved {x_moved:.3f} in X")
        
        print()
    
    return len(issues_found) == 0, issues_found

def test_edge_case_z_traversal():
    """Test edge cases for Z-axis traversal that might allow passage."""
    print("🔍 Testing Edge Cases - Z-Axis Traversal")
    print("=" * 50)
    
    # Create a simple world with a single block
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at position: (5, 10, 5) (occupies 5.0-6.0 in all dimensions)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print(f"Player extends ±{PLAYER_WIDTH/2} from center")
    print()
    
    # Test cases that might allow traversal due to floating point precision or edge cases
    test_cases = [
        {
            'name': 'Z-Movement At Exact Block Edge (X=4.5)',
            'start': (4.5, 10.5, 4.0),   # Player center at 4.5, extends to 5.0 in X
            'end': (4.5, 10.5, 6.0),     # Should be blocked since player extends into block
            'description': 'Player edge exactly touches block edge - should be blocked'
        },
        {
            'name': 'Z-Movement Just Outside Block (X=4.49)',
            'start': (4.49, 10.5, 4.0),  # Player center at 4.49, extends to 4.99 in X
            'end': (4.49, 10.5, 6.0),    # Should be allowed since player doesn\'t touch block
            'description': 'Player just outside block - should be allowed'
        },
        {
            'name': 'Z-Movement Just Inside Block (X=4.51)',
            'start': (4.51, 10.5, 4.0),  # Player center at 4.51, extends to 5.01 in X
            'end': (4.51, 10.5, 6.0),    # Should be blocked since player overlaps block
            'description': 'Player barely overlaps block - should be blocked'
        },
        {
            'name': 'Z-Movement Through Block Corner',
            'start': (5.49, 10.5, 4.0),  # Player extends from 4.99 to 5.99 in X
            'end': (5.49, 10.5, 6.0),    # Should be blocked
            'description': 'Movement through corner of block - should be blocked'
        },
        {
            'name': 'Z-Movement at Y Boundary',
            'start': (5.5, 9.5, 4.0),    # Player extends from y=9.5 to y=10.5 (touches block bottom)
            'end': (5.5, 9.5, 6.0),      # Should be blocked
            'description': 'Movement at Y boundary touching block - should be blocked'
        }
    ]
    
    issues_found = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   {test_case['description']}")
        print(f"   Start: {test_case['start']}")
        print(f"   End:   {test_case['end']}")
        
        start_pos = test_case['start']
        target_pos = test_case['end']
        
        # Check if start position has collision
        start_collision = manager.check_block_collision(start_pos)
        print(f"   Start collision: {start_collision}")
        
        # Check if target position has collision
        target_collision = manager.check_block_collision(target_pos)
        print(f"   Target collision: {target_collision}")
        
        # Test movement resolution
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check if the movement behaves as expected
        z_moved = abs(safe_pos[2] - start_pos[2])
        expected_z_movement = abs(target_pos[2] - start_pos[2])
        
        # For cases where player should be outside block (like X=4.49), movement should be allowed
        if test_case['name'].find('Just Outside') != -1:
            if z_moved < expected_z_movement * 0.9:
                print(f"   ❌ UNEXPECTED BLOCK: Player should move but was blocked")
                issues_found.append(test_case['name'])
            else:
                print(f"   ✅ CORRECTLY ALLOWED: Player moved {z_moved:.3f} in Z")
        else:
            # For all other cases, movement should be blocked
            if z_moved >= expected_z_movement * 0.9:
                print(f"   ❌ TRAVERSAL DETECTED: Player moved {z_moved:.3f} in Z (expected block)")
                issues_found.append(test_case['name'])
            else:
                print(f"   ✅ CORRECTLY BLOCKED: Player moved {z_moved:.3f} in Z")
        
        print()
    
    return len(issues_found) == 0, issues_found

def main():
    """Run edge case traversal tests."""
    print("🧪 TESTING EDGE CASE SINGLE-AXIS TRAVERSAL")
    print("=" * 60)
    print("Testing boundary conditions and edge cases for single-axis movement")
    print()
    
    all_issues = []
    
    # Test X-axis edge cases
    x_success, x_issues = test_edge_case_x_traversal()
    all_issues.extend(x_issues)
    
    # Test Z-axis edge cases
    z_success, z_issues = test_edge_case_z_traversal()
    all_issues.extend(z_issues)
    
    print("=" * 60)
    if len(all_issues) == 0:
        print("✅ ALL EDGE CASE TESTS PASSED: No traversal issues detected")
        return True
    else:
        print("❌ EDGE CASE TESTS FAILED:")
        for issue in all_issues:
            print(f"   - {issue}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)