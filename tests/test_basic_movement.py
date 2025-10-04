#!/usr/bin/env python3
"""
Simple test to verify basic movement works after collision fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import MinecraftCollisionDetector

def test_basic_movement():
    """Test that basic movement still works."""
    print("🔍 Testing Basic Movement After Collision Fix")
    print()
    
    # Simple world with one block
    world = {(10, 10, 10): "stone"}
    detector = MinecraftCollisionDetector(world)
    
    test_cases = [
        {
            "name": "Simple horizontal movement (no collision)",
            "start": (8.0, 11.0, 8.0),
            "end": (9.0, 11.0, 8.0),
            "should_work": True
        },
        {
            "name": "Horizontal movement into block",
            "start": (9.5, 10.5, 10.5),
            "end": (10.5, 10.5, 10.5),
            "should_work": False
        },
        {
            "name": "Diagonal movement around block",
            "start": (9.0, 11.0, 9.0),
            "end": (11.0, 11.0, 9.0),  # Should slide around block
            "should_work": True
        },
        {
            "name": "Diagonal movement through block corner (should be blocked by my fix)",
            "start": (9.5, 10.5, 9.5),
            "end": (10.8, 10.5, 10.8),
            "should_work": False
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test['name']}")
        start_pos = test['start']
        end_pos = test['end']
        
        # Test collision resolution
        safe_pos, collision_info = detector.resolve_collision(start_pos, end_pos)
        
        # Calculate movement distance
        dx = safe_pos[0] - start_pos[0]
        dz = safe_pos[2] - start_pos[2]
        distance_moved = (dx*dx + dz*dz)**0.5
        
        # Calculate intended distance
        idx = end_pos[0] - start_pos[0]
        idz = end_pos[2] - start_pos[2]
        intended_distance = (idx*idx + idz*idz)**0.5
        
        efficiency = distance_moved / intended_distance if intended_distance > 0 else 1.0
        
        print(f"   Start: {start_pos}")
        print(f"   End: {end_pos}")
        print(f"   Result: {safe_pos}")
        print(f"   Efficiency: {efficiency:.1%}")
        
        if test['should_work']:
            passed = efficiency > 0.8
            status = "✅" if passed else "❌"
            print(f"   Expected: Should work - {status}")
        else:
            passed = efficiency < 0.7
            status = "✅" if passed else "❌"
            print(f"   Expected: Should be blocked - {status}")
        
        if not passed:
            all_passed = False
        
        print()
    
    if all_passed:
        print("✅ All basic movement tests passed!")
    else:
        print("❌ Some basic movement tests failed!")
    
    return all_passed

if __name__ == "__main__":
    success = test_basic_movement()
    sys.exit(0 if success else 1)