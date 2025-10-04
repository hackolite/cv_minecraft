#!/usr/bin/env python3
"""
Test camera placement with owner tracking - Integration test.
This test verifies that when a player places a camera block:
1. The owner field is set correctly in block_data
2. The owner field is set correctly in camera_cube
3. The camera appears in the cameras list with correct owner
4. The client would be notified about their owned cameras
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import GameWorld, MinecraftServer, create_block_data
from protocol import BlockType, Message, MessageType, Cube
from typing import Tuple

def test_camera_placement_creates_owner():
    """Test that placing a camera block creates proper owner metadata."""
    print("🧪 Testing camera placement with owner...")
    
    world = GameWorld()
    
    # Simulate a player placing a camera
    player_id = "test_player_123"
    camera_position = (10, 200, 10)
    
    # Simulate what happens in _handle_block_place
    block_id = f"camera_5"  # Auto-generated
    owner = player_id  # Should be set to player_id
    
    # Add the camera block
    result = world.add_block(camera_position, BlockType.CAMERA, block_id=block_id, owner=owner)
    assert result == True
    print("  ✅ Camera block added successfully")
    
    # Verify block data has owner
    block_data = world.world[camera_position]
    assert isinstance(block_data, dict)
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["block_id"] == block_id
    assert block_data["owner"] == player_id
    print(f"  ✅ Block data has correct owner: {block_data['owner']}")
    
    # Verify cameras list includes owner
    cameras = world.get_cameras()
    found_camera = None
    for camera in cameras:
        if camera["block_id"] == block_id:
            found_camera = camera
            break
    
    assert found_camera is not None
    assert found_camera["owner"] == player_id
    print(f"  ✅ get_cameras() returns correct owner: {found_camera['owner']}")
    
    # Verify block_id_map is updated
    assert block_id in world.block_id_map
    assert world.block_id_map[block_id] == camera_position
    print(f"  ✅ block_id_map updated correctly")
    
    print("✅ Camera placement with owner test passed\n")

def test_camera_cube_has_owner():
    """Test that camera Cube instances store owner information."""
    print("🧪 Testing camera Cube owner field...")
    
    player_id = "test_player_456"
    camera_position = (20, 200, 20)
    camera_id = "camera_test"
    
    # Create a camera cube with owner
    camera_cube = Cube(
        cube_id=camera_id,
        position=camera_position,
        cube_type="camera",
        owner=player_id
    )
    
    assert camera_cube.owner == player_id
    print(f"  ✅ Camera cube has correct owner: {camera_cube.owner}")
    
    # Test backward compatibility (cube without owner)
    normal_cube = Cube(
        cube_id="normal_cube",
        position=(0, 0, 0),
        cube_type="normal"
    )
    
    assert normal_cube.owner is None
    print("  ✅ Normal cube without owner has None owner (backward compatible)")
    
    print("✅ Camera Cube owner field test passed\n")

def test_multiple_cameras_different_owners():
    """Test that multiple cameras can have different owners."""
    print("🧪 Testing multiple cameras with different owners...")
    
    world = GameWorld()
    
    # Player 1 places two cameras
    player1_id = "player_1"
    cam1_pos = (10, 200, 10)
    cam2_pos = (15, 200, 15)
    
    world.add_block(cam1_pos, BlockType.CAMERA, block_id="camera_p1_1", owner=player1_id)
    world.add_block(cam2_pos, BlockType.CAMERA, block_id="camera_p1_2", owner=player1_id)
    
    # Player 2 places one camera
    player2_id = "player_2"
    cam3_pos = (20, 200, 20)
    world.add_block(cam3_pos, BlockType.CAMERA, block_id="camera_p2_1", owner=player2_id)
    
    # Get all cameras
    cameras = world.get_cameras()
    
    # Filter cameras by owner
    player1_cameras = [c for c in cameras if c.get("owner") == player1_id]
    player2_cameras = [c for c in cameras if c.get("owner") == player2_id]
    
    # The world was initialized with 5 cameras without owners, so we should have:
    # - 5 cameras with owner=None (from world init)
    # - 2 cameras with owner=player1_id
    # - 1 camera with owner=player2_id
    
    assert len(player1_cameras) == 2
    print(f"  ✅ Player 1 owns {len(player1_cameras)} cameras")
    
    assert len(player2_cameras) == 1
    print(f"  ✅ Player 2 owns {len(player2_cameras)} cameras")
    
    # Verify specific cameras
    assert any(c["block_id"] == "camera_p1_1" for c in player1_cameras)
    assert any(c["block_id"] == "camera_p1_2" for c in player1_cameras)
    assert any(c["block_id"] == "camera_p2_1" for c in player2_cameras)
    print("  ✅ All camera IDs found correctly")
    
    print("✅ Multiple cameras with different owners test passed\n")

def test_camera_list_filtering():
    """Test that a client can filter cameras by owner."""
    print("🧪 Testing camera list filtering by owner...")
    
    world = GameWorld()
    
    # Create cameras with different owners
    player_id = "client_player"
    other_player_id = "other_player"
    
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="my_cam_1", owner=player_id)
    world.add_block((15, 200, 15), BlockType.CAMERA, block_id="my_cam_2", owner=player_id)
    world.add_block((20, 200, 20), BlockType.CAMERA, block_id="other_cam", owner=other_player_id)
    
    # Get all cameras
    all_cameras = world.get_cameras()
    
    # Simulate client-side filtering (as done in _update_owned_cameras)
    owned_cameras = []
    for camera in all_cameras:
        if camera.get("owner") == player_id:
            camera_id = camera.get("block_id")
            if camera_id:
                owned_cameras.append(camera_id)
    
    assert len(owned_cameras) == 2
    assert "my_cam_1" in owned_cameras
    assert "my_cam_2" in owned_cameras
    assert "other_cam" not in owned_cameras
    print(f"  ✅ Client correctly filtered {len(owned_cameras)} owned cameras")
    print(f"  ✅ Owned cameras: {', '.join(owned_cameras)}")
    
    print("✅ Camera list filtering test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA PLACEMENT WITH OWNER - INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    test_camera_placement_creates_owner()
    test_camera_cube_has_owner()
    test_multiple_cameras_different_owners()
    test_camera_list_filtering()
    
    print("=" * 60)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
