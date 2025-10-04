#!/usr/bin/env python3
"""
Test water collision configuration.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server
from server import get_block_collision, create_block_data
from protocol import BlockType
from minecraft_physics import UnifiedCollisionManager


def test_water_collision_enabled():
    """Test that water blocks have collision when WATER_COLLISION_ENABLED is True."""
    print("🧪 Testing water collision ENABLED...")
    
    # Set configuration
    server.WATER_COLLISION_ENABLED = True
    
    # Water should have collision
    assert get_block_collision(BlockType.WATER) == True, "Water should have collision when enabled"
    
    # Create water block data and verify
    water_data = create_block_data(BlockType.WATER)
    assert water_data["collision"] == True, "Water block data should have collision=True when enabled"
    
    print("  ✅ Water has collision when WATER_COLLISION_ENABLED = True")
    print("  ✅ Players will walk on top of water\n")


def test_water_collision_disabled():
    """Test that water blocks have NO collision when WATER_COLLISION_ENABLED is False."""
    print("🧪 Testing water collision DISABLED...")
    
    # Set configuration
    server.WATER_COLLISION_ENABLED = False
    
    # Water should NOT have collision
    assert get_block_collision(BlockType.WATER) == False, "Water should NOT have collision when disabled"
    
    # Create water block data and verify
    water_data = create_block_data(BlockType.WATER)
    assert water_data["collision"] == False, "Water block data should have collision=False when disabled"
    
    print("  ✅ Water has NO collision when WATER_COLLISION_ENABLED = False")
    print("  ✅ Players can pass through water\n")


def test_other_blocks_unaffected():
    """Test that other block types are unaffected by water collision config."""
    print("🧪 Testing other blocks are unaffected...")
    
    # Test with both configurations
    for water_enabled in [True, False]:
        server.WATER_COLLISION_ENABLED = water_enabled
        
        # Air should never have collision
        assert get_block_collision(BlockType.AIR) == False, "Air should never have collision"
        
        # Other blocks should always have collision
        assert get_block_collision(BlockType.GRASS) == True, "Grass should always have collision"
        assert get_block_collision(BlockType.STONE) == True, "Stone should always have collision"
        assert get_block_collision(BlockType.SAND) == True, "Sand should always have collision"
        assert get_block_collision(BlockType.BRICK) == True, "Brick should always have collision"
    
    print("  ✅ Other block types unaffected by WATER_COLLISION_ENABLED")
    print("  ✅ Air always passable, other blocks always solid\n")


def test_player_behavior_with_config():
    """Test that player behavior changes based on water collision configuration."""
    print("🧪 Testing player behavior with different water configurations...")
    
    # Create a world with water blocks at y=15
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    # Test 1: Water collision ENABLED - player should be blocked
    print("  🌊 Testing with WATER_COLLISION_ENABLED = True")
    server.WATER_COLLISION_ENABLED = True
    
    # Recreate block data with new config
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128, world_height=256)
    
    old_pos = (65.0, 20.0, 65.0)
    new_pos = (65.0, 14.0, 65.0)  # Trying to move through water at y=15
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should be blocked by water
    assert safe_pos[1] > new_pos[1], f"Player should be blocked by water, got y={safe_pos[1]}"
    assert collision_info['y'] == True, "Y collision should be detected when water has collision"
    print(f"     ✅ Player blocked by water at y={safe_pos[1]} (cannot sink)")
    
    # Test 2: Water collision DISABLED - player should pass through
    print("  🏊 Testing with WATER_COLLISION_ENABLED = False")
    server.WATER_COLLISION_ENABLED = False
    
    # Recreate block data with new config
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            world_blocks[(x, 15, z)] = create_block_data(BlockType.WATER)
    
    collision_manager = UnifiedCollisionManager(world_blocks, world_size=128, world_height=256)
    
    old_pos = (65.0, 20.0, 65.0)
    new_pos = (65.0, 14.0, 65.0)  # Trying to move through water at y=15
    
    safe_pos, collision_info = collision_manager.resolve_collision(old_pos, new_pos)
    
    # Player should pass through water
    assert safe_pos[1] == new_pos[1], f"Player should pass through water, expected y={new_pos[1]}, got y={safe_pos[1]}"
    assert collision_info['y'] == False, "Y collision should NOT be detected when water has no collision"
    print(f"     ✅ Player passed through water to y={safe_pos[1]} (can swim)")
    
    print("\n  ✅ Player behavior correctly changes based on configuration\n")
    
    # Reset to default
    server.WATER_COLLISION_ENABLED = True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WATER COLLISION CONFIGURATION TESTS")
    print("="*60 + "\n")
    
    try:
        test_water_collision_enabled()
        test_water_collision_disabled()
        test_other_blocks_unaffected()
        test_player_behavior_with_config()
        
        print("="*60)
        print("✅ ALL CONFIGURATION TESTS PASSED!")
        print("="*60 + "\n")
        
        print("💡 Configuration Usage:")
        print("   In server.py, set WATER_COLLISION_ENABLED = True/False")
        print("   - True:  Players walk on water (default)")
        print("   - False: Players can swim through water")
        print()
        
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
