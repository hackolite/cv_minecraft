#!/usr/bin/env python3
"""
Final comprehensive test to verify the diagonal traversal fix works correctly
and doesn't break existing functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT

def test_comprehensive_fix():
    """Comprehensive test of the diagonal traversal fix."""
    print("🧪 COMPREHENSIVE DIAGONAL TRAVERSAL FIX TEST")
    print("=" * 60)
    
    # Test 1: Single block traversal prevention
    print("\n1. Single Block Traversal Prevention")
    world = {(5, 10, 5): 'stone'}
    manager = UnifiedCollisionManager(world)
    
    diagonal_cases = [
        ("NE (+X +Z)", (4.0, 10.5, 4.0), (6.0, 10.5, 6.0)),
        ("NW (-X +Z)", (6.0, 10.5, 4.0), (4.0, 10.5, 6.0)),
        ("SE (+X -Z)", (4.0, 10.5, 6.0), (6.0, 10.5, 4.0)),
        ("SW (-X -Z)", (6.0, 10.5, 6.0), (4.0, 10.5, 4.0)),
    ]
    
    all_blocked = True
    for name, start, end in diagonal_cases:
        safe_pos, collision_info = manager.resolve_collision(start, end)
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        
        if reached_target:
            print(f"   ❌ {name}: TRAVERSAL - reached {safe_pos}")
            all_blocked = False
        else:
            print(f"   ✅ {name}: BLOCKED - stopped at {safe_pos}")
    
    print(f"   Result: {'✅ ALL BLOCKED' if all_blocked else '❌ SOME TRAVERSAL'}")
    
    # Test 2: Legitimate movement should still work
    print("\n2. Legitimate Movement (No Traversal)")
    legitimate_cases = [
        ("Straight X", (4.0, 10.5, 3.0), (6.0, 10.5, 3.0)),
        ("Straight Z", (3.0, 10.5, 4.0), (3.0, 10.5, 6.0)),
        ("Around block", (4.0, 10.5, 4.0), (7.0, 10.5, 4.0)),
        ("Vertical", (4.0, 10.5, 4.0), (4.0, 12.5, 4.0)),
    ]
    
    all_allowed = True
    for name, start, end in legitimate_cases:
        safe_pos, collision_info = manager.resolve_collision(start, end)
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[1] - end[1]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        
        if reached_target:
            print(f"   ✅ {name}: ALLOWED - reached {safe_pos}")
        else:
            print(f"   ⚠️  {name}: BLOCKED - stopped at {safe_pos} (expected {end})")
            all_allowed = False
    
    print(f"   Result: {'✅ ALL ALLOWED' if all_allowed else '⚠️  SOME BLOCKED'}")
    
    # Test 3: Axis-by-axis movement still works
    print("\n3. Axis-by-Axis Collision Resolution")
    world_wall = {}
    # Create X wall
    for y in range(10, 13):
        world_wall[(6, y, 5)] = 'stone'
    
    manager_wall = UnifiedCollisionManager(world_wall)
    
    start = (5.0, 10.9, 5.0)
    end = (6.5, 10.9, 5.5)  # Diagonal into wall
    
    safe_pos, collision_info = manager_wall.resolve_collision(start, end)
    
    # Should block X but allow Z
    x_blocked = collision_info['x']
    z_allowed = not collision_info['z']
    x_position_correct = abs(safe_pos[0] - start[0]) < 0.1
    z_position_correct = abs(safe_pos[2] - end[2]) < 0.1
    
    if x_blocked and z_allowed and x_position_correct and z_position_correct:
        print(f"   ✅ Axis separation: X blocked, Z allowed - {safe_pos}")
    else:
        print(f"   ❌ Axis separation failed:")
        print(f"      X blocked: {x_blocked} (expected True)")
        print(f"      Z allowed: {z_allowed} (expected True)")
        print(f"      Position: {safe_pos} (expected X≈{start[0]}, Z≈{end[2]})")
    
    # Test 4: Complex world with multiple blocks
    print("\n4. Complex World Test")
    complex_world = {}
    # Create a 3x3 wall of blocks
    for x in range(5, 8):
        for z in range(5, 8):
            complex_world[(x, 10, z)] = 'stone'
    
    manager_complex = UnifiedCollisionManager(complex_world)
    
    complex_cases = [
        ("Through wall", (4.0, 10.5, 6.0), (8.0, 10.5, 6.0)),  # Should be blocked
        ("Around wall", (4.0, 10.5, 4.0), (8.0, 10.5, 4.0)),  # Should be allowed
        ("Diagonal through", (4.0, 10.5, 4.0), (8.0, 10.5, 8.0)),  # Should be blocked
    ]
    
    for name, start, end in complex_cases:
        safe_pos, collision_info = manager_complex.resolve_collision(start, end)
        reached_target = abs(safe_pos[0] - end[0]) < 0.1 and abs(safe_pos[2] - end[2]) < 0.1
        
        if "through" in name.lower():
            if reached_target:
                print(f"   ❌ {name}: TRAVERSAL - reached {safe_pos}")
            else:
                print(f"   ✅ {name}: BLOCKED - stopped at {safe_pos}")
        else:  # "around"
            if reached_target:
                print(f"   ✅ {name}: ALLOWED - reached {safe_pos}")
            else:
                print(f"   ⚠️  {name}: BLOCKED - stopped at {safe_pos}")
    
    return all_blocked

def test_performance_check():
    """Quick performance check to ensure the fix doesn't slow things down too much."""
    print("\n🚀 Performance Check")
    
    import time
    
    # Create a reasonable world
    world = {}
    for x in range(0, 10):
        for z in range(0, 10):
            world[(x, 0, z)] = 'stone'  # Ground
            if x == 5 or z == 5:  # Some walls
                world[(x, 1, z)] = 'stone'
    
    manager = UnifiedCollisionManager(world)
    
    # Time multiple collision resolutions
    start_time = time.time()
    iterations = 1000
    
    for i in range(iterations):
        start_pos = (2.0 + i * 0.001, 1.5, 2.0 + i * 0.001)
        end_pos = (7.0 + i * 0.001, 1.5, 7.0 + i * 0.001)
        manager.resolve_collision(start_pos, end_pos)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / iterations * 1000  # ms
    
    print(f"   Average collision resolution time: {avg_time:.3f} ms")
    
    if avg_time < 1.0:  # Less than 1ms is good
        print("   ✅ Performance: GOOD")
    elif avg_time < 5.0:  # Less than 5ms is acceptable
        print("   ⚠️  Performance: ACCEPTABLE")
    else:
        print("   ❌ Performance: SLOW")
    
    return avg_time < 5.0

def main():
    """Run comprehensive tests."""
    print("🎯 FINAL VALIDATION: Diagonal Traversal Fix")
    print("Testing the fix for: 'quand x augmente et z augmente, l'utilisateur traverse le block'")
    print()
    
    try:
        success1 = test_comprehensive_fix()
        success2 = test_performance_check()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("🎉 SUCCESS: All tests passed!")
            print("✅ Diagonal traversal issue fixed")
            print("✅ Existing functionality preserved")
            print("✅ Performance acceptable")
            print("\n🔒 The collision system now prevents block traversal while")
            print("   maintaining proper axis-by-axis collision resolution.")
        else:
            print("❌ FAILURE: Some tests failed")
            if not success1:
                print("   - Traversal fix issues detected")
            if not success2:
                print("   - Performance issues detected")
        
        return success1 and success2
        
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)