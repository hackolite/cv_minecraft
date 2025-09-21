#!/usr/bin/env python3
"""
Final validation test for the single-axis traversal bug fix.

This test validates the fix for the issue described as:
"augmente en x suelement ou augmente en z seulement je traverse lun bloc"
(increase in x only or increase in z only I traverse through a block)

The bug was that players could traverse through blocks when positioned exactly
at block boundaries during single-axis movement due to floating-point boundary
condition issues in AABB collision detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_original_problem_statement():
    """Test the exact scenario from the problem statement."""
    print("🎯 VALIDATION: Original Problem Statement")
    print("=" * 60)
    print("Problem: 'augmente en x suelement ou augmente en z seulement je traverse lun bloc'")
    print("Translation: 'increase in x only or increase in z only I traverse through a block'")
    print()
    print("Creating test scenario: single block, test X-only and Z-only movement")
    print()
    
    # Create a world with exactly one block as specified in problem statement
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    print(f"✓ Block created at position: (5, 10, 5)")
    print(f"✓ Player dimensions: {PLAYER_WIDTH}×{PLAYER_HEIGHT} (width×height)")
    print()
    
    # Test "augmente en x seulement" (increase in x only)
    print("📍 Testing 'augmente en x seulement' (increase in x only)")
    print("-" * 50)
    
    # Test the critical boundary case that was failing before the fix
    start_pos = (4.0, 10.5, 4.5)  # Player edge exactly touches block edge  
    target_pos = (6.0, 10.5, 4.5)  # Movement only in X direction
    
    print(f"Start position: {start_pos}")
    print(f"Target position: {target_pos}")
    print(f"Movement vector: X=+{target_pos[0] - start_pos[0]}, Y=0, Z=0 (X-only)")
    
    # Check collision detection
    start_collision = manager.check_block_collision(start_pos)
    target_collision = manager.check_block_collision(target_pos)
    
    print(f"Start collision: {start_collision}")
    print(f"Target collision: {target_collision}")
    
    # Test movement resolution
    safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
    
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Validate that movement is blocked
    x_moved = abs(safe_pos[0] - start_pos[0])
    expected_x = abs(target_pos[0] - start_pos[0])
    
    if x_moved < expected_x * 0.1:  # Should be blocked (minimal movement)
        print("✅ X-only movement correctly BLOCKED - no traversal")
        x_test_passed = True
    else:
        print(f"❌ X-only movement NOT BLOCKED - traversal detected! Moved {x_moved:.3f}")
        x_test_passed = False
    
    print()
    
    # Test "augmente en z seulement" (increase in z only)
    print("📍 Testing 'augmente en z seulement' (increase in z only)")
    print("-" * 50)
    
    # Test the critical boundary case that was failing before the fix
    start_pos = (4.5, 10.5, 4.0)  # Player edge exactly touches block edge
    target_pos = (4.5, 10.5, 6.0)  # Movement only in Z direction
    
    print(f"Start position: {start_pos}")
    print(f"Target position: {target_pos}")
    print(f"Movement vector: X=0, Y=0, Z=+{target_pos[2] - start_pos[2]} (Z-only)")
    
    # Check collision detection
    start_collision = manager.check_block_collision(start_pos)
    target_collision = manager.check_block_collision(target_pos)
    
    print(f"Start collision: {start_collision}")
    print(f"Target collision: {target_collision}")
    
    # Test movement resolution
    safe_pos, collision_info = manager.resolve_collision(start_pos, target_pos)
    
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Validate that movement is blocked
    z_moved = abs(safe_pos[2] - start_pos[2])
    expected_z = abs(target_pos[2] - start_pos[2])
    
    if z_moved < expected_z * 0.1:  # Should be blocked (minimal movement)
        print("✅ Z-only movement correctly BLOCKED - no traversal")
        z_test_passed = True
    else:
        print(f"❌ Z-only movement NOT BLOCKED - traversal detected! Moved {z_moved:.3f}")
        z_test_passed = False
    
    print()
    
    return x_test_passed and z_test_passed

def test_boundary_conditions_comprehensive():
    """Test comprehensive boundary conditions to ensure fix is robust."""
    print("🔬 VALIDATION: Comprehensive Boundary Conditions")
    print("=" * 60)
    
    world = {(10, 20, 10): 'stone'}  # Use different coordinates to avoid confusion
    manager = UnifiedCollisionManager(world)
    
    print(f"Block at (10, 20, 10) - occupies 10.0-11.0 in all axes")
    print()
    
    boundary_tests = [
        # Test cases for boundary conditions
        {
            'name': 'X-movement at exact Z boundary (player edge = block edge)',
            'start': (9.0, 20.5, 9.5),   # Player extends to Z=10.0, block starts at Z=10.0
            'target': (11.0, 20.5, 9.5), # X-only movement
            'should_block': True
        },
        {
            'name': 'X-movement just outside Z boundary',
            'start': (9.0, 20.5, 9.49),  # Player extends to Z=9.99, block starts at Z=10.0
            'target': (11.0, 20.5, 9.49), # X-only movement
            'should_block': False
        },
        {
            'name': 'Z-movement at exact X boundary (player edge = block edge)',
            'start': (9.5, 20.5, 9.0),   # Player extends to X=10.0, block starts at X=10.0
            'target': (9.5, 20.5, 11.0), # Z-only movement
            'should_block': True
        },
        {
            'name': 'Z-movement just outside X boundary',
            'start': (9.49, 20.5, 9.0),  # Player extends to X=9.99, block starts at X=10.0
            'target': (9.49, 20.5, 11.0), # Z-only movement
            'should_block': False
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(boundary_tests, 1):
        print(f"{i}. {test['name']}")
        print(f"   Start: {test['start']}")
        print(f"   Target: {test['target']}")
        print(f"   Expected: {'BLOCKED' if test['should_block'] else 'ALLOWED'}")
        
        safe_pos, collision_info = manager.resolve_collision(test['start'], test['target'])
        
        # Calculate actual movement
        start_x, start_y, start_z = test['start']
        target_x, target_y, target_z = test['target']
        safe_x, safe_y, safe_z = safe_pos
        
        if target_x != start_x:  # X movement
            movement = abs(safe_x - start_x)
            expected_movement = abs(target_x - start_x)
            axis = 'X'
        else:  # Z movement
            movement = abs(safe_z - start_z)
            expected_movement = abs(target_z - start_z)
            axis = 'Z'
        
        was_blocked = movement < expected_movement * 0.1
        
        if test['should_block'] == was_blocked:
            print(f"   ✅ CORRECT: Movement {'blocked' if was_blocked else 'allowed'} as expected")
        else:
            print(f"   ❌ INCORRECT: Expected {'block' if test['should_block'] else 'allow'}, got {'block' if was_blocked else 'allow'}")
            all_passed = False
        
        print(f"   Result: {axis} moved {movement:.3f} / {expected_movement:.3f}")
        print()
    
    return all_passed

def main():
    """Run the final validation test."""
    print("🧪 FINAL VALIDATION TEST")
    print("=" * 80)
    print("Testing fix for single-axis traversal bug")
    print("Bug: Players could traverse blocks at exact boundary positions") 
    print("Fix: Corrected AABB collision detection boundary conditions")
    print()
    
    # Test original problem statement
    problem_test_passed = test_original_problem_statement()
    
    # Test comprehensive boundary conditions
    boundary_test_passed = test_boundary_conditions_comprehensive()
    
    print("=" * 80)
    print("FINAL VALIDATION RESULTS:")
    print(f"📋 Original problem statement test: {'✅ PASSED' if problem_test_passed else '❌ FAILED'}")
    print(f"🔬 Boundary conditions test: {'✅ PASSED' if boundary_test_passed else '❌ FAILED'}")
    print()
    
    if problem_test_passed and boundary_test_passed:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ Single-axis traversal bug has been successfully fixed")
        print("✅ Players can no longer traverse through blocks at boundary positions")
        print("✅ AABB collision detection now handles boundary conditions correctly")
        return True
    else:
        print("❌ VALIDATION FAILED!")
        print("❌ Single-axis traversal bug is still present")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)