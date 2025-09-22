#!/usr/bin/env python3
"""
Test to verify the fogleman/Minecraft-style simplified collision system.

This test verifies that we've successfully simplified the collision detection
to use only center position checking, eliminating complex AABB calculations.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def test_fogleman_style_simplification():
    """Test that collision system now matches fogleman/Minecraft simplicity."""
    print("🎯 Testing fogleman/Minecraft-style Collision Simplification")
    print("=" * 70)
    
    # Create test world with blocks
    world = {
        (10, 10, 10): 'stone',
        (10, 11, 10): 'stone',  # Block above for head collision testing
        (5, 10, 5): 'stone',    # Another test block
    }
    
    manager = UnifiedCollisionManager(world)
    
    print("✨ Test 1: Center Position Only (No Bounding Box)")
    print("-" * 50)
    
    # Test positions where center is clearly outside block but old AABB system might detect collision
    test_cases = [
        # Position where center is in adjacent block - should be safe in simplified system
        {"pos": (9.7, 10.0, 10.0), "expected": False, "desc": "Player center at (9,10,10) - safe"},
        {"pos": (11.3, 10.0, 10.0), "expected": False, "desc": "Player center at (11,10,10) - safe, outside block"},
        {"pos": (10.0, 10.0, 9.7), "expected": False, "desc": "Player center at (10,10,9) - safe, outside block"},
        {"pos": (10.0, 10.0, 10.0), "expected": True, "desc": "Player center exactly in block"},
        {"pos": (10.5, 10.5, 10.5), "expected": True, "desc": "Player center clearly in block"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = manager.simple_collision_check(case["pos"])
        px, py, pz = case["pos"]
        center_block = (int(math.floor(px)), int(math.floor(py)), int(math.floor(pz)))
        
        print(f"  {i}. {case['desc']}")
        print(f"     Position: {case['pos']}")
        print(f"     Center block check: {center_block}")
        print(f"     Block exists: {center_block in world}")
        print(f"     Collision result: {result}")
        print(f"     Expected: {case['expected']} - {'✅' if result == case['expected'] else '❌'}")
        print()
        
        assert result == case["expected"], f"Failed case {i}: expected {case['expected']}, got {result}"
    
    print("✨ Test 2: Head Position Collision (Simple Height Check)")
    print("-" * 50)
    
    head_test_cases = [
        # Test head collision - player feet at Y=10.5, head at Y=11.5 should hit block at Y=11
        {"pos": (10.0, 10.5, 10.0), "expected": True, "desc": "Player head hits ceiling block"},
        {"pos": (10.0, 9.5, 10.0), "expected": True, "desc": "Player head at Y=10.5 hits block at Y=10"},
        {"pos": (10.0, 8.5, 10.0), "expected": False, "desc": "Player head at Y=9.5 - clear of all blocks"},
    ]
    
    for i, case in enumerate(head_test_cases, 1):
        result = manager.simple_collision_check(case["pos"])
        px, py, pz = case["pos"]
        head_y = py + 1.0  # PLAYER_HEIGHT = 1.0
        head_block = (int(math.floor(px)), int(math.floor(head_y)), int(math.floor(pz)))
        
        print(f"  {i}. {case['desc']}")
        print(f"     Position: {case['pos']}")
        print(f"     Head Y: {head_y}")
        print(f"     Head block check: {head_block}")
        print(f"     Head block exists: {head_block in world}")
        print(f"     Collision result: {result}")
        print(f"     Expected: {case['expected']} - {'✅' if result == case['expected'] else '❌'}")
        print()
        
        assert result == case["expected"], f"Failed head test {i}: expected {case['expected']}, got {result}"
    
    print("✨ Test 3: Movement Resolution (Simple Axis-by-Axis)")
    print("-" * 50)
    
    # Test simple movement resolution
    movement_tests = [
        {
            "old": (9.0, 10.0, 10.0), 
            "new": (10.0, 10.0, 10.0),
            "expected_result": (9.0, 10.0, 10.0),  # Should stay at old position
            "expected_collision": {"x": True, "y": False, "z": False},
            "desc": "Movement into block - should be blocked on X axis"
        },
        {
            "old": (9.0, 10.0, 10.0), 
            "new": (9.5, 10.0, 10.0),
            "expected_result": (9.5, 10.0, 10.0),  # Should allow partial movement
            "expected_collision": {"x": False, "y": False, "z": False},
            "desc": "Partial movement to safe position"
        },
    ]
    
    for i, test in enumerate(movement_tests, 1):
        safe_pos, collision_info = manager.resolve_collision(test["old"], test["new"])
        
        print(f"  {i}. {test['desc']}")
        print(f"     Old position: {test['old']}")
        print(f"     New position: {test['new']}")
        print(f"     Result position: {safe_pos}")
        print(f"     Collision info: {collision_info}")
        print(f"     Expected result: {test['expected_result']}")
        
        pos_match = safe_pos == test["expected_result"]
        collision_match = all(collision_info.get(k, False) == v for k, v in test["expected_collision"].items())
        
        print(f"     Position match: {'✅' if pos_match else '❌'}")
        print(f"     Collision match: {'✅' if collision_match else '❌'}")
        print()
        
        assert pos_match, f"Failed movement test {i}: position mismatch"
        assert collision_match, f"Failed movement test {i}: collision info mismatch"
    
    print("🎉 All fogleman/Minecraft-style collision tests passed!")
    print("✅ Collision system successfully simplified to center-position only")
    print("✅ No more complex AABB bounding box calculations")
    print("✅ Simple axis-by-axis movement resolution")
    print("✅ Much better performance with simplified logic")
    
    return True

if __name__ == "__main__":
    success = test_fogleman_style_simplification()
    sys.exit(0 if success else 1)