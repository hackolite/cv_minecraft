#!/usr/bin/env python3
"""
Test to reproduce the diagonal movement issue where player goes through blocks.
"sur des mouvement en biais, je rentre dans les bocks"
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, COLLISION_EPSILON
)

def test_diagonal_movement_issue():
    """Test diagonal movement to see if player can go through blocks."""
    print("🔍 Testing Diagonal Movement Issue")
    print("Issue: When moving diagonally, player goes through blocks")
    print()
    
    # Create a simple world with blocks
    world = {
        (10, 10, 10): "stone",  # Main block
        (11, 10, 10): "stone",  # Block to the right
        (10, 10, 11): "stone",  # Block in front
        (11, 10, 11): "stone",  # Corner block
    }
    
    print("World setup:")
    for pos, block in world.items():
        print(f"   {block} block at {pos}")
    print()
    
    # Test collision detector
    detector = MinecraftCollisionDetector(world)
    
    # Test cases for diagonal movement
    test_cases = [
        {
            "name": "Standing safely above blocks",
            "start": (10.5, 12.0, 10.5),
            "end": (10.5, 12.0, 10.5),
            "expected_safe": True
        },
        {
            "name": "Moving diagonally through corner",
            "start": (9.5, 10.5, 9.5),  # Player intersecting with block space
            "end": (11.5, 10.5, 11.5),  # Through the corner of blocks
            "expected_safe": False
        },
        {
            "name": "Moving diagonally adjacent to blocks",
            "start": (9.5, 11.0, 10.5), 
            "end": (11.5, 11.0, 10.5),  # Moving along blocks but not through
            "expected_safe": True
        },
        {
            "name": "Fast diagonal movement through block",
            "start": (9.8, 10.5, 9.8),  # Near corner
            "end": (11.2, 10.5, 11.2),  # Through blocks diagonally
            "expected_safe": False
        },
        {
            "name": "Small diagonal step into block",
            "start": (10.7, 10.5, 10.7),  # Close to block center
            "end": (10.8, 10.5, 10.8),  # Small step into block
            "expected_safe": False
        }
    ]
    
    print("Testing diagonal movement cases:")
    failed_cases = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Start: {case['start']}")
        print(f"   End:   {case['end']}")
        
        # Test if start position is safe
        start_collision = detector.check_collision(case['start'])
        print(f"   Start collision: {start_collision}")
        
        # Test if end position is safe  
        end_collision = detector.check_collision(case['end'])
        print(f"   End collision: {end_collision}")
        
        # Test collision resolution
        safe_pos, collision_info = detector.resolve_collision(case['start'], case['end'])
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Check ray casting for tunneling
        ray_collision, hit_block = detector.ray_cast_collision(case['start'], case['end'])
        print(f"   Ray casting collision: {ray_collision}, hit: {hit_block}")
        
        # Calculate actual distance moved
        dx = safe_pos[0] - case['start'][0]
        dy = safe_pos[1] - case['start'][1] 
        dz = safe_pos[2] - case['start'][2]
        distance_moved = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Calculate intended distance
        idx = case['end'][0] - case['start'][0]
        idy = case['end'][1] - case['start'][1]
        idz = case['end'][2] - case['start'][2]
        intended_distance = math.sqrt(idx*idx + idy*idy + idz*idz)
        
        print(f"   Distance intended: {intended_distance:.3f}")
        print(f"   Distance moved: {distance_moved:.3f}")
        
        # Determine if this case passed
        if case['expected_safe']:
            # Should be able to move freely
            if intended_distance < COLLISION_EPSILON:
                # Zero-distance movement should always pass if no collision
                passed = not ray_collision
            else:
                passed = not ray_collision and distance_moved > intended_distance * 0.9
            status = "✅" if passed else "❌"
        else:
            # Should be blocked or limited
            passed = ray_collision or distance_moved < intended_distance * 0.5
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
        print("\nThis indicates the diagonal movement issue is present!")
    else:
        print("✅ All tests passed - diagonal movement collision working correctly")
    
    return len(failed_cases) == 0

if __name__ == "__main__":
    success = test_diagonal_movement_issue()
    sys.exit(0 if success else 1)