#!/usr/bin/env python3
"""
Debug script to understand the snapping issue in collision detection.
Le problème semble être que le snapping ne fonctionne pas correctement dans tous les sens.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, MinecraftCollisionDetector

def test_snapping_in_all_directions():
    """Test snapping in all 6 directions (+X, -X, +Y, -Y, +Z, -Z)."""
    print("🔍 Testing Snapping in All Directions")
    print("=" * 50)
    
    # Create a simple world with a single block
    world = {(5, 5, 5): "stone"}
    manager = UnifiedCollisionManager(world)
    detector = MinecraftCollisionDetector(world)
    
    # Test positions that should trigger snapping in each direction
    test_cases = [
        # Moving towards +X face of block
        {
            "name": "Moving towards +X face",
            "old_pos": (4.0, 5.5, 5.5),
            "new_pos": (5.3, 5.5, 5.5),  # Would go into block
            "expected_axis": "x"
        },
        # Moving towards -X face of block  
        {
            "name": "Moving towards -X face",
            "old_pos": (6.0, 5.5, 5.5),
            "new_pos": (4.7, 5.5, 5.5),  # Would go into block
            "expected_axis": "x"
        },
        # Moving towards +Y face of block
        {
            "name": "Moving towards +Y face",
            "old_pos": (5.5, 4.0, 5.5),
            "new_pos": (5.5, 5.3, 5.5),  # Would go into block
            "expected_axis": "y"
        },
        # Moving towards -Y face of block
        {
            "name": "Moving towards -Y face",
            "old_pos": (5.5, 7.0, 5.5),
            "new_pos": (5.5, 4.7, 5.5),  # Would go into block
            "expected_axis": "y"
        },
        # Moving towards +Z face of block
        {
            "name": "Moving towards +Z face",
            "old_pos": (5.5, 5.5, 4.0),
            "new_pos": (5.5, 5.5, 5.3),  # Would go into block
            "expected_axis": "z"
        },
        # Moving towards -Z face of block
        {
            "name": "Moving towards -Z face",
            "old_pos": (5.5, 5.5, 6.0),
            "new_pos": (5.5, 5.5, 4.7),  # Would go into block
            "expected_axis": "z"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Old position: {test_case['old_pos']}")
        print(f"   New position: {test_case['new_pos']}")
        
        # Test with both systems
        safe_pos_new, collision_info_new = manager.resolve_collision(
            test_case['old_pos'], test_case['new_pos']
        )
        safe_pos_old, collision_info_old = detector.resolve_collision(
            test_case['old_pos'], test_case['new_pos']
        )
        
        print(f"   Expected collision axis: {test_case['expected_axis']}")
        print(f"   Manager result: {safe_pos_new}")
        print(f"   Manager collision: {collision_info_new}")
        print(f"   Detector result: {safe_pos_old}")
        print(f"   Detector collision: {collision_info_old}")
        
        # Check if collision was detected on expected axis
        expected_collision = collision_info_new.get(test_case['expected_axis'], False)
        if expected_collision:
            print(f"   ✅ Collision correctly detected on {test_case['expected_axis']} axis")
        else:
            print(f"   ❌ Collision NOT detected on {test_case['expected_axis']} axis")
        
        # Check if player was snapped away from block
        old_pos = test_case['old_pos']
        if safe_pos_new != test_case['new_pos']:
            distance_old = calculate_distance(old_pos, test_case['new_pos'])
            distance_safe = calculate_distance(old_pos, safe_pos_new)
            print(f"   Snapping: Moved {distance_old:.3f} → {distance_safe:.3f} units")
            
            if distance_safe < distance_old:
                print(f"   ✅ Player properly snapped back from collision")
            else:
                print(f"   ❌ Player not properly snapped back")
        else:
            print(f"   ❌ No snapping occurred - player position unchanged")

def test_diagonal_snapping():
    """Test snapping when moving diagonally towards a block."""
    print(f"\n🔍 Testing Diagonal Snapping")
    print("=" * 30)
    
    # Create a world with a block
    world = {(5, 5, 5): "stone"}
    manager = UnifiedCollisionManager(world)
    
    # Test diagonal movement towards block corner
    old_pos = (4.0, 5.5, 4.0) 
    new_pos = (5.3, 5.5, 5.3)  # Diagonal movement into block
    
    print(f"Diagonal movement: {old_pos} → {new_pos}")
    
    safe_pos, collision_info = manager.resolve_collision(old_pos, new_pos)
    
    print(f"Safe position: {safe_pos}")
    print(f"Collision info: {collision_info}")
    
    # Check if movement was properly handled
    if safe_pos != new_pos:
        print("✅ Diagonal collision properly handled")
        
        # Check which axes were affected
        axes_blocked = [axis for axis, blocked in collision_info.items() 
                       if blocked and axis in ['x', 'y', 'z']]
        print(f"Blocked axes: {axes_blocked}")
    else:
        print("❌ Diagonal collision not handled")

def calculate_distance(pos1, pos2):
    """Calculate 3D distance between two positions."""
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2 + (pos1[2] - pos2[2])**2)**0.5

def test_edge_cases():
    """Test edge cases for snapping."""
    print(f"\n🔍 Testing Edge Cases")
    print("=" * 20)
    
    # Create a world with multiple blocks
    world = {
        (5, 5, 5): "stone",
        (6, 5, 5): "stone",
        (5, 6, 5): "stone"
    }
    manager = UnifiedCollisionManager(world)
    
    # Test movement between blocks
    test_cases = [
        {
            "name": "Movement between two adjacent blocks",
            "old_pos": (4.5, 5.5, 5.5),
            "new_pos": (6.5, 5.5, 5.5)
        },
        {
            "name": "Movement towards corner of multiple blocks",
            "old_pos": (4.0, 4.0, 5.5),
            "new_pos": (5.5, 5.5, 5.5)
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   {test_case['old_pos']} → {test_case['new_pos']}")
        
        safe_pos, collision_info = manager.resolve_collision(
            test_case['old_pos'], test_case['new_pos']
        )
        
        print(f"   Result: {safe_pos}")
        print(f"   Collision: {collision_info}")

if __name__ == "__main__":
    test_snapping_in_all_directions()
    test_diagonal_snapping()
    test_edge_cases()