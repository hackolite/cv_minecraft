#!/usr/bin/env python3
"""
Test the real diagonal movement issue where player can pass through block corners.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def test_real_diagonal_issue():
    """Test the actual diagonal corner tunneling issue."""
    print("🔍 Testing Real Diagonal Corner Tunneling Issue")
    print("Issue: Player can move diagonally through block corners")
    print()
    
    # Create a corridor with a corner - this is where tunneling typically happens
    world = {}
    
    # Create a L-shaped corridor at ground level only
    # Vertical wall
    world[(12, 10, 10)] = "stone"
    world[(12, 10, 11)] = "stone"
    
    # Horizontal wall
    world[(10, 10, 12)] = "stone"
    world[(11, 10, 12)] = "stone"
    
    # Corner block - this is the critical block
    world[(12, 10, 12)] = "stone"
    
    # Ground
    for x in range(9, 15):
        for z in range(9, 15):
            world[(x, 9, z)] = "stone"
    
    print("World setup: L-shaped ground-level obstacles")
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test case: try to move diagonally around the corner at a safe height
    test_cases = [
        {
            "name": "Diagonal movement cutting through corner - should be blocked",
            "start": (11.5, 11.0, 11.5),  # Standing on blocks, safe height
            "end": (12.8, 11.0, 12.8),   # Trying to cut diagonally through corner
            "expected_safe": False,
            "description": "Should be blocked - cutting through corner space"
        },
        {
            "name": "Legitimate movement around corner - should be allowed",
            "start": (11.5, 11.0, 11.5),  # Same start
            "end": (13.5, 11.0, 11.5),   # Move horizontally away from corner
            "expected_safe": True,
            "description": "Should be allowed - horizontal movement at safe height"
        },
        {
            "name": "Small diagonal step towards corner - should be blocked",
            "start": (11.8, 11.0, 11.8),  # Very close to corner
            "end": (12.2, 11.0, 12.2),   # Small step towards corner
            "expected_safe": False,
            "description": "Should be blocked - stepping into corner space"
        },
        {
            "name": "Large diagonal through corner gap - should be blocked",
            "start": (11.0, 11.0, 11.0),  # Further away
            "end": (13.0, 11.0, 13.0),   # Large diagonal movement through corner
            "expected_safe": False,
            "description": "Should be blocked - would tunnel through corner region"
        }
    ]
    
    print("Testing diagonal corner movement cases:")
    failed_cases = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Description: {case['description']}")
        print(f"   Start: {case['start']}")
        print(f"   End:   {case['end']}")
        
        # Test collision resolution
        safe_pos, collision_info = detector.resolve_collision(case['start'], case['end'])
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check ray casting
        ray_collision, hit_block = detector.ray_cast_collision(case['start'], case['end'])
        print(f"   Ray casting: collision={ray_collision}, hit={hit_block}")
        
        # Calculate distances
        start = case['start']
        intended_dx = case['end'][0] - start[0]
        intended_dz = case['end'][2] - start[2]
        intended_distance = math.sqrt(intended_dx*intended_dx + intended_dz*intended_dz)
        
        actual_dx = safe_pos[0] - start[0]
        actual_dz = safe_pos[2] - start[2]
        actual_distance = math.sqrt(actual_dx*actual_dx + actual_dz*actual_dz)
        
        efficiency = actual_distance / intended_distance if intended_distance > 0 else 1.0
        
        # Check if this was considered diagonal
        is_diagonal = abs(intended_dx) > 0.001 and abs(intended_dz) > 0.001
        
        print(f"   Movement type: {'Diagonal' if is_diagonal else 'Non-diagonal'} (dx={intended_dx:.3f}, dz={intended_dz:.3f})")
        print(f"   Distance moved: {actual_distance:.3f}")
        print(f"   Movement efficiency: {efficiency:.1%}")
        
        # Determine if test passed
        if case['expected_safe']:
            # Should be able to move mostly freely
            passed = efficiency > 0.8 and not ray_collision
            status = "✅" if passed else "❌"
        else:
            # Should be significantly blocked
            passed = efficiency < 0.7 or ray_collision
            status = "✅" if passed else "❌"
        
        print(f"   Result: {status} {'PASS' if passed else 'FAIL'}")
        
        if not passed:
            failed_cases.append(case['name'])
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    if failed_cases:
        print(f"❌ {len(failed_cases)} test(s) failed:")
        for case in failed_cases:
            print(f"   - {case}")
        print("\nDiagonal corner tunneling issue is present!")
    else:
        print("✅ All tests passed - diagonal corner collision working correctly")
    
    return len(failed_cases) == 0

if __name__ == "__main__":
    success = test_real_diagonal_issue()
    sys.exit(0 if success else 1)