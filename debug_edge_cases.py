#!/usr/bin/env python3
"""
Targeted test to understand specific edge cases in collision detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager

def test_edge_cases():
    """Test specific edge cases for collision detection."""
    print("🔍 Analyzing Edge Cases in Collision Detection")
    print("=" * 50)
    
    # Single block at origin
    world = {(0, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world)
    
    # Test cases that might be failing
    test_cases = [
        {
            "name": "Close approach to -X face",
            "start": (1.0, 0.5, 0.5),
            "target": (0.3, 0.5, 0.5),  # Closer to the block
        },
        {
            "name": "Very close approach to -X face",
            "start": (0.8, 0.5, 0.5),
            "target": (0.3, 0.5, 0.5),  # Very close
        },
        {
            "name": "Edge of player bounding box -X",
            "start": (1.0, 0.5, 0.5),
            "target": (0.51, 0.5, 0.5),  # Just outside bounding box
        },
        {
            "name": "Just inside player bounding box -X",
            "start": (1.0, 0.5, 0.5),
            "target": (0.49, 0.5, 0.5),  # Just inside bounding box
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   From: {test_case['start']}")
        print(f"   To:   {test_case['target']}")
        
        # Check if target position itself would be in collision
        target_collision = manager._is_position_in_block(test_case['target'])
        print(f"   Target position collision: {target_collision}")
        
        # Check collision resolution
        safe_pos, collision_info = manager.resolve_collision(
            test_case['start'], test_case['target']
        )
        
        print(f"   Result: {safe_pos}")
        print(f"   Collision: {collision_info}")
        
        # Check player bounding box at target position
        px, py, pz = test_case['target']
        player_half_width = 0.5  # PLAYER_WIDTH / 2
        
        player_min_x = px - player_half_width
        player_max_x = px + player_half_width
        print(f"   Player X range at target: [{player_min_x:.2f}, {player_max_x:.2f}]")
        print(f"   Block X range: [0.0, 1.0]")
        
        # Check if ranges overlap
        overlap = player_min_x < 1.0 and player_max_x > 0.0
        print(f"   Ranges overlap: {overlap}")

def test_specific_failing_case():
    """Test the specific case that was failing."""
    print(f"\n🎯 Testing Specific Failing Case")
    print("=" * 35)
    
    world = {(0, 0, 0): "stone"}
    manager = UnifiedCollisionManager(world)
    
    # The failing case
    start = (1.0, 0.5, 0.5)
    target = (-0.8, 0.5, 0.5)
    
    print(f"Movement: {start} → {target}")
    
    # Check what the _is_position_in_block method sees
    print(f"\nDebugging _is_position_in_block for target position {target}:")
    
    px, py, pz = target
    player_half_width = 0.5
    
    # Player bounding box
    player_min_x = px - player_half_width  # -0.8 - 0.5 = -1.3
    player_max_x = px + player_half_width  # -0.8 + 0.5 = -0.3
    player_min_y = py                      # 0.5
    player_max_y = py + 1.0               # 1.5
    player_min_z = pz - player_half_width  # 0.5 - 0.5 = 0.0
    player_max_z = pz + player_half_width  # 0.5 + 0.5 = 1.0
    
    print(f"Player bounding box:")
    print(f"  X: [{player_min_x:.1f}, {player_max_x:.1f}]")
    print(f"  Y: [{player_min_y:.1f}, {player_max_y:.1f}]")
    print(f"  Z: [{player_min_z:.1f}, {player_max_z:.1f}]")
    
    print(f"Block at (0,0,0) bounding box:")
    print(f"  X: [0.0, 1.0]")
    print(f"  Y: [0.0, 1.0]")
    print(f"  Z: [0.0, 1.0]")
    
    # Check overlaps
    x_overlap = player_min_x < 1.0 and player_max_x > 0.0
    y_overlap = player_min_y < 1.0 and player_max_y > 0.0
    z_overlap = player_min_z < 1.0 and player_max_z > 0.0
    
    print(f"Overlaps:")
    print(f"  X: {x_overlap} ({player_min_x:.1f} < 1.0 and {player_max_x:.1f} > 0.0)")
    print(f"  Y: {y_overlap} ({player_min_y:.1f} < 1.0 and {player_max_y:.1f} > 0.0)")
    print(f"  Z: {z_overlap} ({player_min_z:.1f} < 1.0 and {player_max_z:.1f} > 0.0)")
    
    should_collide = x_overlap and y_overlap and z_overlap
    print(f"Should collide: {should_collide}")
    
    # Test actual collision detection
    actual_collision = manager._is_position_in_block(target)
    print(f"Actual collision detected: {actual_collision}")
    
    if should_collide != actual_collision:
        print("❌ MISMATCH - Expected collision doesn't match actual!")
    else:
        print("✅ Collision detection working as expected")

if __name__ == "__main__":
    test_edge_cases()
    test_specific_failing_case()