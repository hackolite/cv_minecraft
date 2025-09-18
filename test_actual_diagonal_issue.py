#!/usr/bin/env python3
"""
Test the actual diagonal movement issue: player should be able to move diagonally
around single blocks but gets stuck on corners.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def test_actual_diagonal_issue():
    """Test the actual diagonal movement issue that players experience."""
    print("🔍 Testing Actual Diagonal Movement Issue")
    print("Real issue: Player gets stuck on single block corners during diagonal movement")
    print()
    
    # Create a realistic world with isolated blocks that should allow diagonal movement around them
    world = {}
    
    # Ground plane
    for x in range(5, 16):
        for z in range(5, 16):
            world[(x, 10, z)] = "stone"
    
    # Single isolated blocks that player should be able to move around
    isolated_blocks = [
        (10, 11, 10),  # Single block obstacle
    ]
    
    for pos in isolated_blocks:
        world[pos] = "stone"
    
    print("World setup:")
    print("   Ground plane from (5,10,5) to (15,10,15)")
    print("   Single obstacle block at (10,11,10)")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test cases that represent the real issue
    test_cases = [
        {
            "name": "Move diagonally around single block - should work",
            "start": (9.2, 11.0, 9.2),      # Approaching block corner
            "end": (10.8, 11.0, 10.8),     # Past block corner diagonally
            "should_succeed": True,
            "expected_efficiency": 0.7      # Realistic: player slides along one axis
        },
        {
            "name": "Move diagonally very close to block corner",
            "start": (9.8, 11.0, 9.8),      # Very close to corner
            "end": (10.2, 11.0, 10.2),     # Just past corner
            "should_succeed": False,        # Too close to block - should be blocked
            "expected_efficiency": 0.1      # Mostly blocked
        },
        {
            "name": "Move directly through block center - should fail",
            "start": (9.5, 11.0, 10.5),     # Directly approaching center
            "end": (10.5, 11.0, 10.5),     # Through block center
            "should_succeed": False,
            "expected_efficiency": 0.1      # Should be mostly blocked
        },
        {
            "name": "Wide diagonal movement around block",
            "start": (8.5, 11.0, 8.5),      # Wide approach
            "end": (11.5, 11.0, 11.5),     # Wide exit
            "should_succeed": True,
            "expected_efficiency": 0.9      # Should work well
        },
        {
            "name": "Sliding along block edge",
            "start": (9.0, 11.0, 10.3),     # Starting at edge
            "end": (11.0, 11.0, 10.3),     # Moving along edge
            "should_succeed": False,        # Edge is too close to block
            "expected_efficiency": 0.2      # Should be mostly blocked
        }
    ]
    
    print("Testing realistic diagonal movement scenarios:")
    failed_cases = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Start: {case['start']}")
        print(f"   End:   {case['end']}")
        
        # Test collision resolution
        safe_pos, collision_info = detector.resolve_collision(case['start'], case['end'])
        print(f"   Result: {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Calculate movement efficiency
        intended_dx = case['end'][0] - case['start'][0]
        intended_dy = case['end'][1] - case['start'][1]
        intended_dz = case['end'][2] - case['start'][2]
        intended_distance = math.sqrt(intended_dx**2 + intended_dy**2 + intended_dz**2)
        
        actual_dx = safe_pos[0] - case['start'][0]
        actual_dy = safe_pos[1] - case['start'][1]
        actual_dz = safe_pos[2] - case['start'][2]
        actual_distance = math.sqrt(actual_dx**2 + actual_dy**2 + actual_dz**2)
        
        efficiency = actual_distance / intended_distance if intended_distance > 0 else 1.0
        print(f"   Efficiency: {efficiency:.1%} (expected ≥{case['expected_efficiency']:.0%})")
        
        # Determine success
        if case['should_succeed']:
            test_passed = efficiency >= case['expected_efficiency']
            expected = f"SUCCESS (≥{case['expected_efficiency']:.0%})"
        else:
            test_passed = efficiency <= case['expected_efficiency']
            expected = f"BLOCKED (≤{case['expected_efficiency']:.0%})"
        
        actual = f"{efficiency:.0%} efficiency"
        status = "✅" if test_passed else "❌"
        
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}")
        print(f"   Result: {status} {'PASS' if test_passed else 'FAIL'}")
        
        if not test_passed:
            failed_cases.append(case['name'])
    
    print(f"\n{'='*80}")
    print("SUMMARY:")
    if failed_cases:
        print(f"❌ {len(failed_cases)} test(s) failed:")
        for case in failed_cases:
            print(f"   - {case}")
        print("\n🐛 Diagonal movement around single blocks needs improvement!")
    else:
        print("✅ All tests passed - diagonal movement working correctly!")
        print("🎉 Issue fixed: Player can now move diagonally around blocks without getting stuck!")
    
    return len(failed_cases) == 0

if __name__ == "__main__":
    success = test_actual_diagonal_issue()
    sys.exit(0 if success else 1)