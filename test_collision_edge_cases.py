#!/usr/bin/env python3
"""
Test the exact collision detection issue that allows sinking.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer

def test_collision_edge_cases():
    """Test collision detection edge cases that might allow sinking."""
    print("🔍 Testing Collision Detection Edge Cases\n")
    
    # Create a minimal server with no generated world
    server = MinecraftServer()
    server.world.world = {}  # Clear the generated world
    
    # Add a simple block
    server.world.world[(10, 10, 10)] = "stone"
    
    print("✅ Created minimal world with one stone block at (10, 10, 10)")
    
    # Test positions that should and shouldn't collide
    test_cases = [
        # Position, Expected collision, Description
        ((10, 11, 10), False, "Standing on top of block"),
        ((10, 10.9, 10), True, "Just inside block surface - should collide"),
        ((10, 10.5, 10), True, "Inside the block"),
        ((10, 10.0, 10), True, "At block bottom"),
        ((10, 9.5, 10), True, "Below block (overlapping)"),
        ((10, 12, 10), False, "Well above block"),
        ((10.5, 11, 10), False, "Next to block horizontally"),
        ((9.5, 11, 10), False, "Next to block horizontally"),
        ((10, 11, 10.5), False, "Next to block in Z"),
        ((10, 11, 9.5), False, "Next to block in Z"),
        ((10, 11.1, 10), False, "Just above block surface - should NOT collide"),
    ]
    
    print("Testing collision detection:")
    failed_tests = []
    
    for position, expected_collision, description in test_cases:
        actual_collision = server._check_ground_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {description}: pos={position}, expected={expected_collision}, actual={actual_collision}")
        
        if actual_collision != expected_collision:
            failed_tests.append((position, expected_collision, actual_collision, description))
    
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} tests failed:")
        for pos, exp, act, desc in failed_tests:
            print(f"   - {desc}: expected {exp}, got {act} at {pos}")
        return False
    else:
        print(f"\n✅ All collision detection tests passed!")
        return True

def test_player_size_bounds():
    """Test that player size is correctly accounted for in collision."""
    print("\n🔍 Testing Player Size Collision Bounds\n")
    
    # Create a minimal server
    server = MinecraftServer()
    server.world.world = {}
    
    # Add a block
    server.world.world[(0, 0, 0)] = "stone"
    
    # Player size is 0.4 (half-size), so full size is 0.8x0.8
    # Player height is 1.8
    
    print("Testing player bounding box collision (player size = 0.4, height = 1.8):")
    
    test_cases = [
        # Position, Expected collision, Description
        ((0, 1, 0), False, "Center above block"),
        ((0.3, 1, 0), False, "Within player bounds but not colliding"),
        ((0.4, 1, 0), False, "At edge of player bounds"),
        ((0.5, 1, 0), False, "Outside player bounds"),
        ((0, 1.9, 0), False, "Above player height"),
        ((0, 0.9, 0), True, "Within player height, overlapping block"),
        ((0.8, 1, 0), False, "Far from block"),
    ]
    
    failed_tests = []
    for position, expected_collision, description in test_cases:
        actual_collision = server._check_ground_collision(position)
        status = "✅" if actual_collision == expected_collision else "❌"
        print(f"   {status} {description}: pos={position}, expected={expected_collision}, actual={actual_collision}")
        
        if actual_collision != expected_collision:
            failed_tests.append((position, expected_collision, actual_collision, description))
    
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} bounds tests failed:")
        for pos, exp, act, desc in failed_tests:
            print(f"   - {desc}: expected {exp}, got {act} at {pos}")
        return False
    else:
        print(f"\n✅ All bounds tests passed!")
        return True

if __name__ == "__main__":
    print("🎮 Testing Collision Detection Edge Cases\n")
    
    try:
        success = True
        success &= test_collision_edge_cases()
        success &= test_player_size_bounds()
        
        if success:
            print("\n🎉 ALL COLLISION EDGE CASE TESTS PASSED!")
        else:
            print("\n❌ Some collision edge case tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)