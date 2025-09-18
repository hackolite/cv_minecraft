#!/usr/bin/env python3
"""
Test realistic diagonal movement collision scenarios.
The issue "sur des mouvement en biais, je rentre dans les bocks" 
likely refers to movement at ground level, not above blocks.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT
)

def test_realistic_diagonal_scenarios():
    """Test realistic scenarios where diagonal movement might fail."""
    print("🔍 Testing Realistic Diagonal Movement Scenarios")
    print("Issue: When moving diagonally at ground level, player goes through blocks")
    print()
    
    # Create a more realistic world layout
    # Ground level at Y=10, player walks at Y=11 (on top of ground)
    world = {}
    
    # Create a ground plane
    for x in range(8, 13):
        for z in range(8, 13):
            world[(x, 10, z)] = "stone"  # Ground level
    
    # Create some walls/obstacles at ground level (Y=11)
    wall_blocks = [
        (10, 11, 10), (11, 11, 10),  # Wall across
        (10, 11, 11), (11, 11, 11),  # Wall behind
    ]
    
    for pos in wall_blocks:
        world[pos] = "stone"
    
    print("World setup:")
    print("   Ground plane from (8,10,8) to (12,10,12)")
    print("   Wall blocks at Y=11:", wall_blocks)
    print()
    
    detector = MinecraftCollisionDetector(world)
    
    # Test cases for realistic diagonal movement issues
    test_cases = [
        {
            "name": "Walking on ground, no obstacles",
            "start": (9.0, 11.0, 9.0),  # On ground level  
            "end": (12.0, 11.0, 12.0),   # Diagonal across open area
            "should_block": False
        },
        {
            "name": "Walking diagonally through wall corner",
            "start": (9.5, 11.0, 9.5),  # Just outside wall
            "end": (11.5, 11.0, 11.5),  # Through wall corner
            "should_block": True
        },
        {
            "name": "Walking diagonally along wall edge", 
            "start": (9.5, 11.0, 10.5),  # Along wall
            "end": (11.5, 11.0, 10.5),  # Along wall edge
            "should_block": True
        },
        {
            "name": "Small diagonal step into wall",
            "start": (10.4, 11.0, 10.4),  # Very close to wall
            "end": (10.6, 11.0, 10.6),   # Small step into wall
            "should_block": True
        },
        {
            "name": "Fast diagonal movement through narrow gap",
            "start": (9.0, 11.0, 10.5),   # Start before wall
            "end": (12.0, 11.0, 10.5),    # End after wall (going through)
            "should_block": True
        },
        {
            "name": "Player already inside wall trying to move",
            "start": (10.5, 11.0, 10.5),  # Center of wall block
            "end": (11.0, 11.0, 11.0),    # Try to move to another wall block
            "should_block": True
        }
    ]
    
    print("Testing realistic diagonal movement cases:")
    failed_cases = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   Start: {case['start']}")
        print(f"   End:   {case['end']}")
        
        # Check initial positions
        start_collision = detector.check_collision(case['start'])
        end_collision = detector.check_collision(case['end'])
        print(f"   Start collision: {start_collision}")
        print(f"   End collision: {end_collision}")
        
        # Test collision resolution
        safe_pos, collision_info = detector.resolve_collision(case['start'], case['end'])
        print(f"   Safe position: {safe_pos}")
        print(f"   Collision info: {collision_info}")
        
        # Test ray casting
        ray_collision, hit_block = detector.ray_cast_collision(case['start'], case['end'])
        print(f"   Ray casting: collision={ray_collision}, hit={hit_block}")
        
        # Calculate movement efficiency
        intended_dx = case['end'][0] - case['start'][0]
        intended_dy = case['end'][1] - case['start'][1]
        intended_dz = case['end'][2] - case['start'][2]
        intended_distance = math.sqrt(intended_dx**2 + intended_dy**2 + intended_dz**2)
        
        actual_dx = safe_pos[0] - case['start'][0]
        actual_dy = safe_pos[1] - case['start'][1]
        actual_dz = safe_pos[2] - case['start'][2]
        actual_distance = math.sqrt(actual_dx**2 + actual_dy**2 + actual_dz**2)
        
        movement_efficiency = actual_distance / intended_distance if intended_distance > 0 else 1.0
        
        print(f"   Movement efficiency: {movement_efficiency:.2%}")
        
        # Determine if test passed
        if case['should_block']:
            # Movement should be significantly blocked
            test_passed = (ray_collision or 
                          any(collision_info[k] for k in ['x', 'y', 'z']) or 
                          movement_efficiency < 0.5)
            expected = "BLOCKED"
        else:
            # Movement should be mostly free
            test_passed = (not ray_collision and 
                          not any(collision_info[k] for k in ['x', 'y', 'z']) and 
                          movement_efficiency > 0.9)
            expected = "FREE"
        
        actual = "BLOCKED" if not test_passed and case['should_block'] else "FREE" if test_passed and not case['should_block'] else "UNEXPECTED"
        status = "✅" if test_passed else "❌"
        
        print(f"   Expected: {expected}, Actual: {actual}")
        print(f"   Result: {status} {'PASS' if test_passed else 'FAIL'}")
        
        if not test_passed:
            failed_cases.append(case['name'])
    
    print(f"\n{'='*80}")
    print("SUMMARY:")
    if failed_cases:
        print(f"❌ {len(failed_cases)} test(s) failed:")
        for case in failed_cases:
            print(f"   - {case}")
        print("\n🐛 Issues found with diagonal movement collision detection!")
    else:
        print("✅ All tests passed - diagonal movement collision working correctly")
    
    return len(failed_cases) == 0

if __name__ == "__main__":
    success = test_realistic_diagonal_scenarios()
    sys.exit(0 if success else 1)