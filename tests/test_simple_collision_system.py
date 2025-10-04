#!/usr/bin/env python3
"""
Test for the new simple collision system inspired by fogleman/Minecraft.

This test verifies that the collision system now uses simple center position + height
checking instead of complex bounding box collision detection.
"""

import sys
import os
import math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from minecraft_physics import UnifiedCollisionManager, PLAYER_HEIGHT, PLAYER_WIDTH

def test_simple_collision_behavior():
    """Test that the new simple collision system works as expected."""
    print("🎮 Testing Simple Collision System (inspired by fogleman/Minecraft)")
    print("=" * 70)
    
    # Create test world with a single block
    world = {
        (10, 10, 10): 'stone'  # Single block at (10, 10, 10)
    }
    
    manager = UnifiedCollisionManager(world)
    
    print("🧪 Test 1: Simple Center Position Check")
    print("-" * 50)
    
    # Test player at same position as block (center collision)
    player_in_block = (10.0, 10.0, 10.0)
    collision = manager.simple_collision_check(player_in_block)
    print(f"Player at block center (10.0, 10.0, 10.0): collision = {collision}")
    assert collision == True, "Player center in block should collide"
    
    # Test player next to block (no center collision) 
    player_next_to_block = (11.0, 10.0, 10.0)
    collision = manager.simple_collision_check(player_next_to_block)
    print(f"Player next to block (11.0, 10.0, 10.0): collision = {collision}")
    assert collision == False, "Player next to block should not collide (simple check)"
    
    print("\n🧪 Test 2: Height-based Collision")
    print("-" * 50)
    
    # Test player with head in block  
    player_head_in_block = (10.0, 9.5, 10.0)  # Head would be at 10.5, in the block (Y=10-11)
    collision = manager.simple_collision_check(player_head_in_block)
    print(f"Player head in block (10.0, 9.5, 10.0, head at 10.5): collision = {collision}")
    assert collision == True, "Player head in block should collide"
    
    # Test player under block (no collision)
    player_under_block = (10.0, 8.0, 10.0)  # Head would be at 9.0, under the block (Y=10-11)
    collision = manager.simple_collision_check(player_under_block)
    print(f"Player under block (10.0, 8.0, 10.0, head at 9.0): collision = {collision}")
    assert collision == False, "Player under block should not collide"
    
    print("\n🧪 Test 3: Simple Collision Resolution")
    print("-" * 50)
    
    # Test simple collision resolution (no sweeping AABB)
    old_pos = (9.0, 10.0, 10.0)  # Safe position
    new_pos = (10.0, 10.0, 10.0)  # Would collide with block
    
    safe_pos, collision_info = manager.resolve_collision(old_pos, new_pos)
    print(f"Move from {old_pos} to {new_pos}")
    print(f"Result: safe_pos = {safe_pos}, collision_info = {collision_info}")
    
    # Should stay at old position due to collision
    assert safe_pos[0] == 9.0, "X should stay at safe position"
    assert collision_info['x'] == True, "X collision should be detected"
    
    print("\n🧪 Test 4: Comparison with Old Complex System")
    print("-" * 50)
    
    # Test a position that would show the difference between simple and complex systems
    # Player at position where center is not in block but bounding box might overlap
    player_outside_block = (11.1, 10.0, 10.0)  # Center clearly outside block
    simple_collision = manager.simple_collision_check(player_outside_block)
    
    print(f"Player outside block (11.1, 10.0, 10.0):")
    print(f"  Simple collision check: {simple_collision}")
    print(f"  Simple system only checks center position and height")
    
    # Test that complex AABB collision still works as before
    complex_collision = manager.check_block_collision(player_outside_block)
    print(f"  Complex AABB collision check: {complex_collision}")
    
    # Show the real difference with a position where the old system would use bounding box
    print(f"\n🔍 Key difference:")
    print(f"  Simple system: Only checks if center point (floor({player_outside_block[0]}), floor({player_outside_block[1]}), floor({player_outside_block[2]})) = ({int(math.floor(player_outside_block[0]))}, {int(math.floor(player_outside_block[1]))}, {int(math.floor(player_outside_block[2]))}) is in world")
    print(f"  Complex system: Uses full bounding box with width {PLAYER_WIDTH} and height {PLAYER_HEIGHT}")
    
    # Test different collision - where simple is truly different
    # Position where complex system might detect collision but simple doesn't
    edge_case = (10.7, 11.0, 10.0)  # Near block but not center-overlapping
    simple_edge = manager.simple_collision_check(edge_case)
    complex_edge = manager.check_block_collision(edge_case)
    
    print(f"\n🎯 Edge case comparison at (10.7, 11.0, 10.0):")
    print(f"  Block position check: floor(10.7) = {int(math.floor(10.7))}, so checking block ({int(math.floor(10.7))}, {int(math.floor(11.0))}, {int(math.floor(10.0))})")
    print(f"  Simple collision: {simple_edge}")
    print(f"  Complex collision: {complex_edge}")
    
    assert simple_collision == False, "Simple system should not detect collision outside block center"
    
    print("\n✅ All simple collision system tests passed!")
    print("🎯 The system now uses simple center position + height checking")
    print("🎯 This matches the fogleman/Minecraft approach for simplicity")
    print("🎯 Key improvement: Much simpler logic without complex bounding box calculations")
    
    return True

if __name__ == "__main__":
    success = test_simple_collision_behavior()
    sys.exit(0 if success else 1)