#!/usr/bin/env python3
"""
Test for single-axis traversal issue.

Based on the problem statement: "augmente en x suelement ou augmente en z seulement je traverse lun bloc"
This translates to: "increase in x only or increase in z only I traverse through a block"

This test specifically checks if there are traversal issues when moving in only one axis at a time.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_single_axis_x_movement():
    """Test movement only in X direction to see if traversal occurs."""
    print("🔍 Testing Single-Axis X Movement Traversal")
    print("=" * 50)
    
    # Create a simple world with a single block
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at position: (5, 10, 5)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print()
    
    # Test cases for X-only movement that should be blocked
    test_cases = [
        {
            'name': 'X-Only Movement Through Block Center',
            'start': (4.0, 10.5, 5.0),   # Y=10.5 to be at block level, Z=5.0 to be in block center
            'end': (6.0, 10.5, 5.0),     # Move through the block center in X direction only
            'description': 'Movement only in X direction through block center - should be blocked'
        },
        {
            'name': 'X-Only Movement Near Block Edge',
            'start': (4.0, 10.5, 5.3),   # Near the edge of the block
            'end': (6.0, 10.5, 5.3),     # Move through the block in X direction only
            'description': 'Movement only in X direction near block edge - should be blocked'
        },
        {
            'name': 'X-Only Movement At Block Boundary',
            'start': (4.0, 10.5, 5.5),   # At the boundary (player extends from 5.0 to 6.0 in Z)
            'end': (6.0, 10.5, 5.5),     # Move through the block in X direction only
            'description': 'Movement only in X direction at block boundary - should be blocked'
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
        
        # Test movement resolution
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check if movement was blocked
        x_moved = abs(safe_pos[0] - start_pos[0])
        expected_x_movement = abs(target_pos[0] - start_pos[0])
        
        if x_moved >= expected_x_movement * 0.9:  # Allow for some floating point error
            print(f"   ❌ TRAVERSAL DETECTED: Player moved {x_moved:.3f} in X (expected block)")
            traversal_detected = True
        else:
            print(f"   ✅ CORRECTLY BLOCKED: Player moved {x_moved:.3f} in X (blocked)")
        
        print()
    
    return not traversal_detected

def test_single_axis_z_movement():
    """Test movement only in Z direction to see if traversal occurs."""
    print("🔍 Testing Single-Axis Z Movement Traversal")
    print("=" * 50)
    
    # Create a simple world with a single block
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at position: (5, 10, 5)")
    print(f"Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print()
    
    # Test cases for Z-only movement that should be blocked
    test_cases = [
        {
            'name': 'Z-Only Movement Through Block Center',
            'start': (5.0, 10.5, 4.0),   # Y=10.5 to be at block level, X=5.0 to be in block center
            'end': (5.0, 10.5, 6.0),     # Move through the block center in Z direction only
            'description': 'Movement only in Z direction through block center - should be blocked'
        },
        {
            'name': 'Z-Only Movement Near Block Edge',
            'start': (5.3, 10.5, 4.0),   # Near the edge of the block
            'end': (5.3, 10.5, 6.0),     # Move through the block in Z direction only
            'description': 'Movement only in Z direction near block edge - should be blocked'
        },
        {
            'name': 'Z-Only Movement At Block Boundary',
            'start': (5.5, 10.5, 4.0),   # At the boundary (player extends from 5.0 to 6.0 in X)
            'end': (5.5, 10.5, 6.0),     # Move through the block in Z direction only
            'description': 'Movement only in Z direction at block boundary - should be blocked'
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
        
        # Test movement resolution
        safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check if movement was blocked
        z_moved = abs(safe_pos[2] - start_pos[2])
        expected_z_movement = abs(target_pos[2] - start_pos[2])
        
        if z_moved >= expected_z_movement * 0.9:  # Allow for some floating point error
            print(f"   ❌ TRAVERSAL DETECTED: Player moved {z_moved:.3f} in Z (expected block)")
            traversal_detected = True
        else:
            print(f"   ✅ CORRECTLY BLOCKED: Player moved {z_moved:.3f} in Z (blocked)")
        
        print()
    
    return not traversal_detected

def main():
    """Run single-axis traversal tests."""
    print("🧪 TESTING SINGLE-AXIS TRAVERSAL ISSUE")
    print("=" * 60)
    print("Problem: 'augmente en x suelement ou augmente en z seulement je traverse lun bloc'")
    print("Translation: 'increase in x only or increase in z only I traverse through a block'")
    print()
    
    success = True
    
    # Test X-only movement
    x_test_success = test_single_axis_x_movement()
    success = success and x_test_success
    
    # Test Z-only movement  
    z_test_success = test_single_axis_z_movement()
    success = success and z_test_success
    
    print("=" * 60)
    if success:
        print("✅ ALL TESTS PASSED: No single-axis traversal issues detected")
    else:
        print("❌ TESTS FAILED: Single-axis traversal issues detected")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)