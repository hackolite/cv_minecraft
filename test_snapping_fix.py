#!/usr/bin/env python3
"""
Test to demonstrate the fix for snapping in all directions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def test_snapping_fix():
    """Test that the snapping fix works for all directions."""
    print("🔧 Testing Snapping Fix in All Directions")
    print("=" * 50)
    
    # Create a simple world with a single block at (0,0,0)
    world = {(0, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world)
    
    # Test cases that were previously failing
    test_cases = [
        {
            "name": "Moving towards -X face (previously failing)",
            "old_pos": (1.0, 0.5, 0.5),
            "new_pos": (-0.3, 0.5, 0.5),  # Would go into block
            "expected_result": "Collision should be detected and player snapped back"
        },
        {
            "name": "Moving towards -Z face (previously failing)",
            "old_pos": (0.5, 0.5, 1.0),
            "new_pos": (0.5, 0.5, -0.3),  # Would go into block
            "expected_result": "Collision should be detected and player snapped back"
        },
        {
            "name": "Diagonal movement towards corner",
            "old_pos": (1.5, 0.5, 1.5),
            "new_pos": (-0.3, 0.5, -0.3),  # Diagonal into block
            "expected_result": "Some movement should be allowed on at least one axis"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   From: {test_case['old_pos']}")
        print(f"   To:   {test_case['new_pos']}")
        print(f"   Expected: {test_case['expected_result']}")
        
        safe_pos, collision_info = manager.resolve_collision(
            test_case['old_pos'], test_case['new_pos']
        )
        
        print(f"   Result:     {safe_pos}")
        print(f"   Collision:  {collision_info}")
        
        # Calculate movement allowed
        old_x, old_y, old_z = test_case['old_pos']
        new_x, new_y, new_z = test_case['new_pos']
        safe_x, safe_y, safe_z = safe_pos
        
        intended_movement = ((new_x - old_x)**2 + (new_y - old_y)**2 + (new_z - old_z)**2)**0.5
        actual_movement = ((safe_x - old_x)**2 + (safe_y - old_y)**2 + (safe_z - old_z)**2)**0.5
        
        if intended_movement > 0:
            efficiency = actual_movement / intended_movement
            print(f"   Movement efficiency: {efficiency:.1%}")
        
        # Check if collision was properly detected
        collision_detected = any(collision_info[axis] for axis in ['x', 'y', 'z'])
        if collision_detected:
            print(f"   ✅ Collision properly detected")
        else:
            print(f"   ❌ No collision detected")

if __name__ == "__main__":
    test_snapping_fix()