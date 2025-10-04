#!/usr/bin/env python3
"""
Test camera block owner metadata functionality.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import GameWorld, create_block_data
from protocol import BlockType

def test_camera_block_with_owner():
    """Test that camera blocks can have owner metadata."""
    print("🧪 Testing camera block with owner metadata...")
    
    # Test camera block with owner
    block_data = create_block_data(BlockType.CAMERA, block_id="camera_5", owner="player_123")
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["collision"] == True
    assert block_data["block_id"] == "camera_5"
    assert block_data["owner"] == "player_123"
    print("  ✅ Camera block with owner: OK")
    
    # Test camera block without owner (backward compatibility)
    block_data = create_block_data(BlockType.CAMERA, block_id="camera_6")
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["owner"] is None
    print("  ✅ Camera block without owner (backward compatible): OK")
    
    print("✅ Camera owner metadata tests passed\n")

def test_world_camera_management_with_owner():
    """Test GameWorld camera management with owner tracking."""
    print("🧪 Testing GameWorld camera management with owner...")
    
    world = GameWorld()
    
    # Use a position high in the air that won't have a block
    test_pos = (10, 200, 10)
    
    # Test adding camera block with block_id and owner
    result = world.add_block(test_pos, BlockType.CAMERA, block_id="cam_test", owner="player_456")
    assert result == True
    print("  ✅ Added camera block with owner")
    
    # Verify block data
    block_data = world.world[test_pos]
    assert isinstance(block_data, dict)
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["block_id"] == "cam_test"
    assert block_data["owner"] == "player_456"
    print("  ✅ Block data includes owner")
    
    # Verify cameras list includes owner
    cameras = world.get_cameras()
    found_camera = None
    for camera in cameras:
        if camera["block_id"] == "cam_test":
            found_camera = camera
            break
    
    assert found_camera is not None
    assert found_camera["owner"] == "player_456"
    print("  ✅ get_cameras() returns owner field")
    
    print("✅ Camera owner management tests passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA OWNER METADATA TESTS")
    print("=" * 60 + "\n")
    
    test_camera_block_with_owner()
    test_world_camera_management_with_owner()
    # test_server_camera_cubes()  # Skip in headless environment
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
