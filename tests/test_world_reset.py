#!/usr/bin/env python3
"""
Test world reset functionality.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress pyglet/websocket imports for testing
import logging
logging.basicConfig(level=logging.INFO)

from server import GameWorld, create_block_data
from protocol import BlockType

def test_world_reset_basic():
    """Test basic world reset functionality."""
    print("🧪 Testing basic world reset...")
    
    # Create world without reset
    world = GameWorld(reset_to_natural=False)
    
    # Count initial blocks
    initial_count = len(world.world)
    print(f"  Initial block count: {initial_count}")
    
    # Count camera blocks (should have 5 from world init)
    camera_blocks = [pos for pos, data in world.world.items() 
                     if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    print(f"  Initial camera blocks: {len(camera_blocks)}")
    assert len(camera_blocks) == 5, f"Expected 5 camera blocks, got {len(camera_blocks)}"
    
    # Add some player blocks
    test_positions = [
        ((10, 200, 10), BlockType.CAMERA, "cam_test", "player_123"),
        ((11, 200, 11), BlockType.BRICK, None, None),
        ((12, 200, 12), BlockType.CAT, None, None),
    ]
    
    for pos, block_type, block_id, owner in test_positions:
        result = world.add_block(pos, block_type, block_id=block_id, owner=owner)
        assert result == True, f"Failed to add block at {pos}"
    
    after_add_count = len(world.world)
    print(f"  After adding blocks: {after_add_count}")
    assert after_add_count == initial_count + 3
    
    # Test reset
    removed_count = world.reset_to_natural_terrain()
    print(f"  Blocks removed by reset: {removed_count}")
    
    # Should have removed: 5 initial cameras + 3 added blocks = 8 blocks
    assert removed_count == 8, f"Expected 8 blocks removed, got {removed_count}"
    
    # Verify all cameras are gone
    camera_blocks_after = [pos for pos, data in world.world.items() 
                           if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    assert len(camera_blocks_after) == 0, f"Expected 0 camera blocks after reset, got {len(camera_blocks_after)}"
    
    # Verify only natural blocks remain
    for pos, block_data in world.world.items():
        if isinstance(block_data, dict):
            block_type = block_data.get("type")
        else:
            block_type = block_data
        
        assert block_type in {BlockType.GRASS, BlockType.SAND, BlockType.STONE, 
                              BlockType.WATER, BlockType.WOOD, BlockType.LEAF}, \
            f"Non-natural block {block_type} found after reset at {pos}"
    
    print("  ✅ Basic world reset test passed\n")

def test_world_reset_on_init():
    """Test world reset on initialization."""
    print("🧪 Testing world reset on initialization...")
    
    # Create world with reset flag
    world = GameWorld(reset_to_natural=True)
    
    # Count blocks
    block_count = len(world.world)
    print(f"  Block count after init with reset: {block_count}")
    
    # Verify no cameras exist
    camera_blocks = [pos for pos, data in world.world.items() 
                     if isinstance(data, dict) and data.get("type") == BlockType.CAMERA]
    assert len(camera_blocks) == 0, f"Expected 0 camera blocks after reset on init, got {len(camera_blocks)}"
    
    # Verify only natural blocks
    for pos, block_data in world.world.items():
        if isinstance(block_data, dict):
            block_type = block_data.get("type")
        else:
            block_type = block_data
        
        assert block_type in {BlockType.GRASS, BlockType.SAND, BlockType.STONE, 
                              BlockType.WATER, BlockType.WOOD, BlockType.LEAF}, \
            f"Non-natural block {block_type} found after reset on init at {pos}"
    
    print("  ✅ World reset on init test passed\n")

def test_block_id_map_cleanup():
    """Test that block_id_map is properly cleaned up during reset."""
    print("🧪 Testing block_id_map cleanup...")
    
    world = GameWorld(reset_to_natural=False)
    
    # Initial block_id_map should have 5 camera entries
    initial_map_size = len(world.block_id_map)
    print(f"  Initial block_id_map size: {initial_map_size}")
    assert initial_map_size == 5, f"Expected 5 entries in block_id_map, got {initial_map_size}"
    
    # Add blocks with block_ids
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="cam_test1", owner="player_1")
    world.add_block((11, 200, 11), BlockType.USER, block_id="user_test1")
    
    assert len(world.block_id_map) == 7, f"Expected 7 entries after adding, got {len(world.block_id_map)}"
    
    # Reset
    world.reset_to_natural_terrain()
    
    # block_id_map should be empty
    assert len(world.block_id_map) == 0, f"Expected empty block_id_map after reset, got {len(world.block_id_map)}"
    
    print("  ✅ block_id_map cleanup test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("WORLD RESET FUNCTIONALITY TESTS")
    print("=" * 60 + "\n")
    
    test_world_reset_basic()
    test_world_reset_on_init()
    test_block_id_map_cleanup()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
