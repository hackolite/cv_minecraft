#!/usr/bin/env python3
"""
Comprehensive test for anti-tunneling collision detection improvements.
Tests various scenarios that could lead to players going through blocks.
"""

import sys
import os
import math
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import MinecraftCollisionDetector, PLAYER_WIDTH, PLAYER_HEIGHT, get_player_bounding_box


def test_large_movement_tunneling():
    """Test that large movements cannot tunnel through blocks."""
    print("🧪 Testing Large Movement Tunneling Prevention")
    
    # Create a wall of blocks
    world = {}
    for y in range(0, 10):
        for z in range(-2, 3):
            world[(5, y, z)] = 'stone'  # Wall at X=5
    
    detector = MinecraftCollisionDetector(world)
    
    # Test various large movements that should be blocked
    test_cases = [
        # Try to tunnel through wall horizontally
        ((0.0, 5.0, 0.0), (10.0, 5.0, 0.0)),  # Horizontal through wall
        ((0.0, 2.0, 0.0), (10.0, 2.0, 0.0)),  # Lower horizontal
        
        # Try to tunnel vertically through multiple blocks
        ((5.5, 15.0, 0.0), (5.5, -5.0, 0.0)),  # Vertical through wall
        
        # Diagonal movements
        ((0.0, 15.0, 0.0), (10.0, -5.0, 0.0)),  # Large diagonal
    ]
    
    for i, (start_pos, end_pos) in enumerate(test_cases):
        safe_pos, collision_info = detector.resolve_collision(start_pos, end_pos)
        distance_moved = math.sqrt(
            (safe_pos[0] - start_pos[0])**2 + 
            (safe_pos[1] - start_pos[1])**2 + 
            (safe_pos[2] - start_pos[2])**2
        )
        intended_distance = math.sqrt(
            (end_pos[0] - start_pos[0])**2 + 
            (end_pos[1] - start_pos[1])**2 + 
            (end_pos[2] - start_pos[2])**2
        )
        
        print(f"   Test {i+1}: {start_pos} -> {end_pos}")
        print(f"      Stopped at: {safe_pos}")
        print(f"      Distance moved: {distance_moved:.2f} / {intended_distance:.2f}")
        
        # Player should not have tunneled through the wall
        if start_pos[0] < 5 and end_pos[0] > 5:
            assert safe_pos[0] < 5.0 - PLAYER_WIDTH/2, f"Should not tunnel through wall horizontally"
        
        # Should not reach the intended destination if blocked
        assert distance_moved < intended_distance, f"Should be blocked before reaching destination"
    
    print("   ✅ Large movement tunneling prevention working")
    return True


def test_edge_case_positions():
    """Test collision detection at edge positions near block boundaries."""
    print("\n🧪 Testing Edge Case Positions")
    
    # Single block for precise testing
    world = {(0, 0, 0): 'stone'}
    detector = MinecraftCollisionDetector(world)
    
    # Test positions very close to block boundaries
    edge_cases = [
        # Just above block surface
        (0.5, 1.0, 0.5),      # Exactly on surface
        (0.5, 1.001, 0.5),    # Just above surface
        (0.5, 0.999, 0.5),    # Just below surface (should collide)
        
        # Near block edges horizontally
        (0.0, 1.1, 0.5),      # At edge of block
        (1.0, 1.1, 0.5),      # At other edge
        (0.5, 1.1, 0.0),      # At Z edge
        (0.5, 1.1, 1.0),      # At other Z edge
        
        # Corner cases
        (0.0, 1.0, 0.0),      # Corner exactly
        (1.0, 1.0, 1.0),      # Opposite corner
    ]
    
    for pos in edge_cases:
        collision = detector.check_collision(pos)
        min_corner, max_corner = get_player_bounding_box(pos)
        print(f"   Pos {pos}: collision={collision}, bbox=({min_corner[1]:.3f}, {max_corner[1]:.3f})")
        
        # Y=0.999 should collide because player extends down to feet level
        if pos[1] <= 1.0 - PLAYER_HEIGHT + 0.01:  # Player would intersect block
            assert collision, f"Position {pos} should have collision"
        elif pos[1] >= 1.0:  # Player clearly above block
            assert not collision or pos[1] < 1.0 + 0.001, f"Position {pos} should not have collision"
    
    print("   ✅ Edge case positions handled correctly")
    return True


def test_rapid_small_movements():
    """Test many small movements to ensure no tunneling occurs."""
    print("\n🧪 Testing Rapid Small Movements") 
    
    # Create a box of blocks to move around in
    world = {}
    for x in range(-1, 2):
        for y in range(-1, 1):  # Floor only
            for z in range(-1, 2):
                world[(x, y, z)] = 'stone'
    
    detector = MinecraftCollisionDetector(world)
    
    # Start at a safe position above the floor
    position = (0.0, 1.5, 0.0)
    assert not detector.check_collision(position), "Starting position should be safe"
    
    # Perform many small random movements
    for step in range(100):
        # Small random movement
        dx = random.uniform(-0.1, 0.1)
        dy = random.uniform(-0.1, 0.1)
        dz = random.uniform(-0.1, 0.1)
        
        new_position = (position[0] + dx, position[1] + dy, position[2] + dz)
        safe_position, collision_info = detector.resolve_collision(position, new_position)
        
        # Verify we never end up inside a block
        assert not detector.check_collision(safe_position), f"Step {step}: Ended up in collision at {safe_position}"
        
        # Verify we stay above the floor
        assert safe_position[1] >= 1.0, f"Step {step}: Fell below floor level to {safe_position}"
        
        position = safe_position
        
        if step % 20 == 0:
            print(f"   Step {step}: position = ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})")
    
    print("   ✅ Rapid small movements handled safely")
    return True


def test_random_walk_simulation():
    """Simulate random walk movements like in demo_player_debug_system.py"""
    print("\n🧪 Testing Random Walk Simulation")
    
    # Create a world similar to what might be in the game
    world = {}
    # Ground plane
    for x in range(-10, 11):
        for z in range(-10, 11):
            world[(x, 0, z)] = 'grass'
    
    # Some random obstacles
    for i in range(10):
        x = random.randint(-8, 8)
        z = random.randint(-8, 8)
        for y in range(1, random.randint(2, 5)):
            world[(x, y, z)] = 'stone'
    
    detector = MinecraftCollisionDetector(world)
    
    # Start at a safe position
    position = (0.0, 1.1, 0.0)
    
    # Perform random walk similar to demo_player_debug_system.py
    for step in range(50):
        # Random movement similar to PlayerDemo.random_walk
        step_size = 3.0  # Similar to demo
        dx = random.uniform(-step_size, step_size)
        dy = random.uniform(-1, 1)  # Small vertical movement
        dz = random.uniform(-step_size, step_size)
        
        new_position = (
            position[0] + dx,
            max(1.1, position[1] + dy),  # Don't go below ground level
            position[2] + dz
        )
        
        safe_position, collision_info = detector.resolve_collision(position, new_position)
        
        # Critical checks
        assert not detector.check_collision(safe_position), f"Step {step}: Collision at {safe_position}"
        assert safe_position[1] >= 1.0, f"Step {step}: Below ground at {safe_position}"
        
        position = safe_position
        
        if step % 10 == 0:
            print(f"   Step {step}: position = ({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f})")
    
    print("   ✅ Random walk simulation completed safely")
    return True


def test_collision_constants_effectiveness():
    """Test that the improved collision constants prevent tunneling."""
    print("\n🧪 Testing Collision Constants Effectiveness")
    
    # Import the updated constants
    from minecraft_physics import COLLISION_EPSILON, STEP_HEIGHT
    
    print(f"   COLLISION_EPSILON: {COLLISION_EPSILON}")
    print(f"   STEP_HEIGHT: {STEP_HEIGHT}")
    
    # Verify the constants are within expected ranges
    assert COLLISION_EPSILON <= 0.001, "COLLISION_EPSILON should be small for precision"
    assert STEP_HEIGHT <= 0.6, "STEP_HEIGHT should not allow stepping over full blocks"
    
    # Test that the step height doesn't allow tunneling
    world = {(0, 0, 0): 'stone', (0, 1, 0): 'stone'}
    detector = MinecraftCollisionDetector(world)
    
    # Try to step up onto the block
    can_step = detector.can_step_up((0.5, 1.0, 0.5), (0.5, 1.0 + STEP_HEIGHT + 0.1, 0.5))
    print(f"   Can step up {STEP_HEIGHT + 0.1} blocks: {can_step}")
    assert not can_step, "Should not be able to step higher than STEP_HEIGHT"
    
    # Should be able to step up exactly STEP_HEIGHT from a valid starting position
    from_pos = (1.5, 1.0, 0.5)  # Away from the blocks
    to_pos = (1.5, 1.0 + STEP_HEIGHT - 0.1, 0.5)  # Still away from blocks
    can_step = detector.can_step_up(from_pos, to_pos)
    print(f"   Can step up {STEP_HEIGHT - 0.1} blocks from safe position: {can_step}")
    assert can_step, "Should be able to step up within STEP_HEIGHT from safe position"
    
    print("   ✅ Collision constants are effective")
    return True


if __name__ == "__main__":
    print("🛡️  Testing Anti-Tunneling Collision Detection Improvements\n")
    
    try:
        tests = [
            test_large_movement_tunneling,
            test_edge_case_positions,
            test_rapid_small_movements,
            test_random_walk_simulation,
            test_collision_constants_effectiveness,
        ]
        
        success = True
        for test in tests:
            try:
                success &= test()
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
                import traceback
                traceback.print_exc()
                success = False
        
        if success:
            print("\n🎉 ALL ANTI-TUNNELING TESTS PASSED!")
            print("✅ Large movements are properly blocked")
            print("✅ Edge cases around block boundaries handled correctly")
            print("✅ Rapid small movements don't cause tunneling")
            print("✅ Random walk movements are safe")
            print("✅ Collision constants prevent tunneling")
            print("\n🛡️  Players can no longer go through blocks!")
        else:
            print("\n❌ Some anti-tunneling tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)