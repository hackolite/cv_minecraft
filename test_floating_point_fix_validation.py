#!/usr/bin/env python3
"""
Comprehensive test to validate the floating-point precision fix.

This test ensures that:
1. The snapping issue is fixed when player is stable on ground
2. Normal collision behavior still works correctly
3. Gravity still applies when player is falling
4. Jump mechanics still work
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    UnifiedCollisionManager, TickBasedPhysicsManager,
    GRAVITY, COLLISION_EPSILON, GROUND_TOLERANCE, JUMP_VELOCITY
)

def test_stable_ground_no_snapping():
    """Test that player stable on ground doesn't snap continuously."""
    print("🔬 Test 1: Stable Ground - No Snapping")
    print("=" * 50)
    
    world = {(10, 10, 10): 'stone'}
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Player exactly on top of block
    position = (10.5, 11.0, 10.5)
    velocity = (0.0, 0.0, 0.0)
    
    dt = 0.016
    stable_ticks = 0
    
    for tick in range(10):
        old_position = position
        old_velocity = velocity
        
        position, velocity, collision_info = physics_manager.update_tick(
            position, velocity, dt, jumping=False
        )
        
        # Check if position and velocity remain stable
        pos_changed = any(abs(a - b) > COLLISION_EPSILON for a, b in zip(position, old_position))
        vel_changed = any(abs(a - b) > COLLISION_EPSILON for a, b in zip(velocity, old_velocity))
        
        if not pos_changed and not vel_changed and not collision_info['y']:
            stable_ticks += 1
        else:
            print(f"  Tick {tick}: pos_changed={pos_changed}, vel_changed={vel_changed}, y_collision={collision_info['y']}")
    
    success = stable_ticks >= 8  # Allow some initial settling
    print(f"  Stable ticks: {stable_ticks}/10")
    print(f"  ✅ PASS: No snapping detected" if success else f"  ❌ FAIL: Still snapping")
    return success

def test_falling_physics_still_works():
    """Test that gravity and falling physics still work correctly."""
    print("\n🔬 Test 2: Falling Physics")
    print("=" * 50)
    
    world = {(10, 10, 10): 'stone'}
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Player starting in air above block
    position = (10.5, 15.0, 10.5)
    velocity = (0.0, 0.0, 0.0)
    
    dt = 0.016
    fell_correctly = False
    
    for tick in range(100):  # Give enough time to fall
        old_y = position[1]
        position, velocity, collision_info = physics_manager.update_tick(
            position, velocity, dt, jumping=False
        )
        
        # Check if player is falling (Y decreasing)
        if position[1] < old_y:
            fell_correctly = True
        
        # Check if player landed on block (around y=11)
        if collision_info['ground'] and abs(position[1] - 11.0) < 0.1:
            print(f"  Landed at y={position[1]:.3f} after {tick} ticks")
            break
    
    success = fell_correctly and collision_info['ground']
    print(f"  ✅ PASS: Gravity and landing work" if success else f"  ❌ FAIL: Falling physics broken")
    return success

def test_collision_still_prevents_movement():
    """Test that normal collision detection still prevents movement through blocks."""
    print("\n🔬 Test 3: Wall Collision")
    print("=" * 50)
    
    world = {
        (10, 10, 10): 'stone',
        (11, 10, 10): 'stone',  # Wall to the east
        (10, 11, 10): 'stone',  # Floor
    }
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Player on floor, trying to move into wall
    position = (10.5, 11.0, 10.5)
    velocity = (5.0, 0.0, 0.0)  # Fast movement toward wall
    
    dt = 0.016
    
    for tick in range(5):
        old_x = position[0]
        position, velocity, collision_info = physics_manager.update_tick(
            position, velocity, dt, jumping=False
        )
        
        # Player should be blocked by wall
        if collision_info['x']:
            print(f"  Wall collision detected at x={position[0]:.3f}")
            break
    
    # Player should not have moved significantly into the wall
    success = position[0] < 11.0 and collision_info['x']
    print(f"  ✅ PASS: Wall collision works" if success else f"  ❌ FAIL: Player went through wall")
    return success

def test_jump_mechanics():
    """Test that jumping still works correctly."""
    print("\n🔬 Test 4: Jump Mechanics")
    print("=" * 50)
    
    world = {(10, 10, 10): 'stone'}
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Player on ground
    position = (10.5, 11.0, 10.5)
    velocity = (0.0, 0.0, 0.0)
    
    dt = 0.016
    jumped = False
    
    # Trigger jump
    position, velocity, collision_info = physics_manager.update_tick(
        position, velocity, dt, jumping=True
    )
    
    if velocity[1] > 0:  # Should have upward velocity
        jumped = True
        print(f"  Jump initiated with velocity {velocity[1]:.3f}")
        
        # Simulate a few ticks to see if player goes up
        for tick in range(10):
            old_y = position[1]
            position, velocity, collision_info = physics_manager.update_tick(
                position, velocity, dt, jumping=False
            )
            
            if position[1] > old_y:
                print(f"  Player rising: y={position[1]:.3f}")
                break
    
    success = jumped and velocity[1] > 0
    print(f"  ✅ PASS: Jump mechanics work" if success else f"  ❌ FAIL: Jump broken")
    return success

def test_floating_point_edge_cases():
    """Test edge cases with floating-point precision."""
    print("\n🔬 Test 5: Floating-Point Edge Cases")
    print("=" * 50)
    
    world = {(10, 10, 10): 'stone'}
    collision_manager = UnifiedCollisionManager(world)
    physics_manager = TickBasedPhysicsManager(collision_manager)
    
    # Test positions with tiny floating-point errors
    test_positions = [
        (10.5, 11.0000001, 10.5),  # Tiny bit above ground
        (10.5, 10.9999999, 10.5),  # Tiny bit below ground
        (10.5, 11.0, 10.5),        # Exact ground level
    ]
    
    success_count = 0
    
    for i, pos in enumerate(test_positions):
        position = pos
        velocity = (0.0, 0.0, 0.0)
        dt = 0.016
        
        # Run a few ticks to see if snapping occurs
        snapping_detected = False
        for tick in range(5):
            old_position = position
            position, velocity, collision_info = physics_manager.update_tick(
                position, velocity, dt, jumping=False
            )
            
            # Check for snapping (rapid position changes)
            if collision_info['y'] and abs(position[1] - old_position[1]) > COLLISION_EPSILON:
                snapping_detected = True
                break
        
        if not snapping_detected:
            success_count += 1
            print(f"  Position {i+1}: No snapping ✅")
        else:
            print(f"  Position {i+1}: Snapping detected ❌")
    
    success = success_count >= 2  # At least 2/3 should work
    print(f"  ✅ PASS: Edge cases handled" if success else f"  ❌ FAIL: Edge cases cause snapping")
    return success

def main():
    """Run all validation tests."""
    print("🔧 Floating-Point Precision Fix Validation")
    print("="*60)
    
    tests = [
        test_stable_ground_no_snapping,
        test_falling_physics_still_works,
        test_collision_still_prevents_movement,
        test_jump_mechanics,
        test_floating_point_edge_cases,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ FAIL: Exception occurred: {e}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎯 SUCCESS: All tests passed! Fix is working correctly.")
        return True
    else:
        print("⚠️  WARNING: Some tests failed. Fix may need adjustment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)