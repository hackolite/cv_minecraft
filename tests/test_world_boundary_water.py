#!/usr/bin/env python3
"""
Test world boundary collision and water block behavior.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minecraft_physics import UnifiedCollisionManager, PLAYER_WIDTH, PLAYER_HEIGHT
from server import get_block_collision, create_block_data
from protocol import BlockType


def test_water_has_no_collision():
    """Test that water blocks don't have collision."""
    print("🧪 Testing water block collision...")
    
    # Water should not have collision
    assert get_block_collision(BlockType.WATER) == False, "Water should not have collision"
    
    # Create water block data and verify
    water_data = create_block_data(BlockType.WATER)
    assert water_data["collision"] == False, "Water block data should have collision=False"
    
    print("✅ Water blocks correctly have no collision\n")


def test_world_boundary_prevents_falling():
    """Test that world boundaries prevent players from falling off the edge."""
    print("🧪 Testing world boundary collision...")
    
    # Create a collision manager with empty world
    world_blocks = {}
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128, world_height=256)
    
    # Test moving beyond X boundary (positive)
    old_pos = (64.0, 50.0, 64.0)
    new_pos = (130.0, 50.0, 64.0)  # Beyond world boundary at x=128
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should be clamped within world bounds
    player_half_width = PLAYER_WIDTH / 2
    max_x = 128 - player_half_width  # 127.5
    assert safe_pos[0] <= max_x, f"Player X should be clamped to {max_x}, got {safe_pos[0]}"
    assert collision_info['x'] == True, "X collision should be detected at world boundary"
    print(f"  ✅ X boundary (positive): clamped from {new_pos[0]} to {safe_pos[0]}")
    
    # Test moving beyond X boundary (negative)
    old_pos = (5.0, 50.0, 64.0)
    new_pos = (-2.0, 50.0, 64.0)  # Beyond world boundary at x=0
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should be clamped within world bounds
    min_x = player_half_width  # 0.5
    assert safe_pos[0] >= min_x, f"Player X should be clamped to {min_x}, got {safe_pos[0]}"
    assert collision_info['x'] == True, "X collision should be detected at world boundary"
    print(f"  ✅ X boundary (negative): clamped from {new_pos[0]} to {safe_pos[0]}")
    
    # Test moving beyond Z boundary (positive)
    old_pos = (64.0, 50.0, 64.0)
    new_pos = (64.0, 50.0, 130.0)  # Beyond world boundary at z=128
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should be clamped within world bounds
    max_z = 128 - player_half_width  # 127.5
    assert safe_pos[2] <= max_z, f"Player Z should be clamped to {max_z}, got {safe_pos[2]}"
    assert collision_info['z'] == True, "Z collision should be detected at world boundary"
    print(f"  ✅ Z boundary (positive): clamped from {new_pos[2]} to {safe_pos[2]}")
    
    # Test moving beyond Z boundary (negative)
    old_pos = (64.0, 50.0, 5.0)
    new_pos = (64.0, 50.0, -2.0)  # Beyond world boundary at z=0
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should be clamped within world bounds
    min_z = player_half_width  # 0.5
    assert safe_pos[2] >= min_z, f"Player Z should be clamped to {min_z}, got {safe_pos[2]}"
    assert collision_info['z'] == True, "Z collision should be detected at world boundary"
    print(f"  ✅ Z boundary (negative): clamped from {new_pos[2]} to {safe_pos[2]}")
    
    print("✅ World boundary collision tests passed\n")


def test_player_on_water_does_not_sink():
    """Test that players don't sink into water blocks."""
    print("🧪 Testing player on water block...")
    
    # Create a world with water blocks at y=15
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            # Add water block with no collision
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128, world_height=256)
    
    # Player starting above water
    old_pos = (65.0, 20.0, 65.0)
    new_pos = (65.0, 15.5, 65.0)  # Moving down onto water level
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should pass through water (no collision)
    # Water is at y=15, so player should be able to move to y=15.5
    assert safe_pos[1] == new_pos[1], f"Player should move freely through water, expected y={new_pos[1]}, got y={safe_pos[1]}"
    assert collision_info['y'] == False, "Y collision should not be detected for water"
    print(f"  ✅ Player moved through water from y={old_pos[1]} to y={safe_pos[1]}")
    
    # Player should be able to fall through water
    old_pos = (65.0, 16.0, 65.0)
    new_pos = (65.0, 14.5, 65.0)  # Falling through water block at y=15
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should pass through water
    assert safe_pos[1] == new_pos[1], f"Player should fall through water, expected y={new_pos[1]}, got y={safe_pos[1]}"
    assert collision_info['y'] == False, "Y collision should not be detected when falling through water"
    print(f"  ✅ Player fell through water from y={old_pos[1]} to y={safe_pos[1]}")
    
    print("✅ Water collision tests passed\n")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WORLD BOUNDARY AND WATER COLLISION TESTS")
    print("="*60 + "\n")
    
    try:
        test_water_has_no_collision()
        test_world_boundary_prevents_falling()
        test_player_on_water_does_not_sink()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
