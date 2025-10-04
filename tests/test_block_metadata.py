#!/usr/bin/env python3
"""
Test block metadata (collision and block_id) functionality.
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import GameWorld, create_block_data, get_block_collision
from protocol import BlockType

def test_block_data_creation():
    """Test that create_block_data creates correct structure."""
    print("🧪 Testing block data creation...")
    
    # Test without block_id
    block_data = create_block_data(BlockType.GRASS)
    assert block_data["type"] == BlockType.GRASS
    assert block_data["collision"] == True
    assert block_data["block_id"] is None
    print("  ✅ Grass block without block_id: OK")
    
    # Test with block_id (camera)
    block_data = create_block_data(BlockType.CAMERA, block_id="camera_1")
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["collision"] == True
    assert block_data["block_id"] == "camera_1"
    print("  ✅ Camera block with block_id: OK")
    
    # Test water (with collision - behaves like solid block)
    block_data = create_block_data(BlockType.WATER)
    assert block_data["type"] == BlockType.WATER
    assert block_data["collision"] == True
    assert block_data["block_id"] is None
    print("  ✅ Water block (with collision): OK")
    
    # Test user block
    block_data = create_block_data(BlockType.USER, block_id="player_123")
    assert block_data["type"] == BlockType.USER
    assert block_data["collision"] == True
    assert block_data["block_id"] == "player_123"
    print("  ✅ User block with block_id: OK")
    
    print("✅ Block data creation tests passed\n")

def test_block_collision_function():
    """Test get_block_collision function."""
    print("🧪 Testing get_block_collision function...")
    
    assert get_block_collision(BlockType.GRASS) == True
    assert get_block_collision(BlockType.STONE) == True
    assert get_block_collision(BlockType.CAMERA) == True
    assert get_block_collision(BlockType.USER) == True
    assert get_block_collision(BlockType.WATER) == True
    assert get_block_collision(BlockType.AIR) == False
    
    print("✅ Block collision function tests passed\n")

def test_world_block_management():
    """Test GameWorld block management with new metadata."""
    print("🧪 Testing GameWorld block management...")
    
    world = GameWorld()
    
    # Use a position high in the air that won't have a block
    test_pos = (10, 200, 10)
    
    # Test adding camera block with block_id
    result = world.add_block(test_pos, BlockType.CAMERA, block_id="cam_test")
    assert result == True
    print("  ✅ Added camera block with block_id")
    
    # Verify block_id is tracked
    assert "cam_test" in world.block_id_map
    assert world.block_id_map["cam_test"] == test_pos
    print("  ✅ block_id mapped correctly")
    
    # Verify block data
    block_data = world.world[test_pos]
    assert isinstance(block_data, dict)
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["collision"] == True
    assert block_data["block_id"] == "cam_test"
    print("  ✅ Block data stored correctly")
    
    # Test get_block (should return type string)
    block_type = world.get_block(test_pos)
    assert block_type == BlockType.CAMERA
    print("  ✅ get_block returns correct type")
    
    # Test removing block with block_id
    result = world.remove_block(test_pos)
    assert result == True
    assert "cam_test" not in world.block_id_map
    print("  ✅ Block removed and block_id cleaned up")
    
    print("✅ GameWorld block management tests passed\n")

def test_user_blocks():
    """Test user block management."""
    print("🧪 Testing user block management...")
    
    world = GameWorld()
    
    # Add user block
    result = world.add_user_block("player_1", (50.5, 100.5, 50.5))
    assert result == True
    print("  ✅ Added user block")
    
    # Verify user block is tracked
    assert "player_1" in world.block_id_map
    block_pos = world.block_id_map["player_1"]
    print(f"  ✅ User block position: {block_pos}")
    
    # Verify block data
    block_data = world.world[block_pos]
    assert block_data["type"] == BlockType.USER
    assert block_data["collision"] == True
    assert block_data["block_id"] == "player_1"
    print("  ✅ User block data correct")
    
    # Move user to different position
    result = world.add_user_block("player_1", (51.5, 100.5, 51.5))
    assert result == True
    new_pos = world.block_id_map["player_1"]
    # Position gets normalized (rounded to nearest int)
    print(f"  ✅ User block moved to: {new_pos}")
    
    # Old position should be cleaned up
    assert block_pos not in world.world or world.world[block_pos]["type"] != BlockType.USER
    print("  ✅ Old user block position cleaned up")
    
    # Remove user block
    result = world.remove_user_block("player_1")
    assert result == True
    assert "player_1" not in world.block_id_map
    print("  ✅ User block removed")
    
    print("✅ User block management tests passed\n")

def test_get_cameras_with_metadata():
    """Test get_cameras returns block_id and collision."""
    print("🧪 Testing get_cameras with metadata...")
    
    world = GameWorld()
    cameras = world.get_cameras()
    
    # Should have camera blocks from world initialization
    assert len(cameras) > 0
    print(f"  ✅ Found {len(cameras)} camera blocks")
    
    # Check first camera has required fields
    camera = cameras[0]
    assert "position" in camera
    assert "block_type" in camera
    assert "block_id" in camera
    assert "collision" in camera
    assert camera["block_type"] == BlockType.CAMERA
    assert camera["collision"] == True
    assert camera["block_id"] is not None
    print(f"  ✅ Camera metadata: position={camera['position']}, block_id={camera['block_id']}, collision={camera['collision']}")
    
    print("✅ get_cameras metadata tests passed\n")

def test_get_blocks_in_view_with_block_id():
    """Test querying blocks by block_id."""
    print("🧪 Testing get_blocks_in_view with block_id...")
    
    world = GameWorld()
    
    # Get a camera block_id
    cameras = world.get_cameras()
    if len(cameras) > 0:
        camera_block_id = cameras[0]["block_id"]
        camera_position = cameras[0]["position"]
        print(f"  Using camera block_id: {camera_block_id} at {camera_position}")
        
        # Query blocks from camera's perspective using block_id
        blocks = world.get_blocks_in_view(
            position=(0, 0, 0),  # Dummy, will be replaced
            rotation=(0, 0),
            view_distance=30.0,
            block_id=camera_block_id
        )
        
        assert len(blocks) > 0
        print(f"  ✅ Found {len(blocks)} blocks in view from camera {camera_block_id}")
        
        # Check that blocks have metadata
        block = blocks[0]
        assert "position" in block
        assert "block_type" in block
        assert "block_id" in block
        assert "collision" in block
        assert "distance" in block
        print(f"  ✅ Block metadata: type={block['block_type']}, collision={block['collision']}, distance={block['distance']:.1f}")
    else:
        print("  ⚠️  No camera blocks found (skipping)")
    
    print("✅ get_blocks_in_view with block_id tests passed\n")

def main():
    """Run all tests."""
    print("🚀 Testing Block Metadata System")
    print("=" * 60)
    
    try:
        test_block_data_creation()
        test_block_collision_function()
        test_world_block_management()
        test_user_blocks()
        test_get_cameras_with_metadata()
        test_get_blocks_in_view_with_block_id()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
