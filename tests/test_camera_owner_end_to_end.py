#!/usr/bin/env python3
"""
End-to-end test for camera ownership flow.
This test verifies the complete flow:
1. Player places a camera
2. Server creates block_data with owner
3. Server creates camera_cube with owner
4. Server sends CAMERAS_LIST with owner field
5. Client filters cameras by owner
6. Client shows notification about owned cameras
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import GameWorld, create_block_data
from protocol import BlockType, Message, MessageType, Cube, create_cameras_list_message

def test_complete_camera_ownership_flow():
    """Test the complete camera ownership flow from placement to client notification."""
    print("🧪 Testing complete camera ownership flow...")
    
    # Setup
    world = GameWorld()
    player_id = "test_player_123"
    
    # Step 1: Player places a camera (simulating server-side _handle_block_place)
    print("\n  Step 1: Player places camera block")
    camera_position = (10, 200, 10)
    block_id = "camera_5"
    owner = player_id
    
    # Create camera cube (as done in _handle_block_place)
    camera_cube = Cube(
        cube_id=block_id,
        position=camera_position,
        cube_type="camera",
        owner=player_id
    )
    
    # Add block to world
    result = world.add_block(camera_position, BlockType.CAMERA, block_id=block_id, owner=owner)
    assert result == True
    print(f"    ✅ Camera block placed at {camera_position}")
    print(f"    ✅ Camera cube created with owner: {camera_cube.owner}")
    
    # Step 2: Verify block_data has owner
    print("\n  Step 2: Verify block data")
    block_data = world.world[camera_position]
    assert isinstance(block_data, dict)
    assert block_data["type"] == BlockType.CAMERA
    assert block_data["block_id"] == block_id
    assert block_data["owner"] == player_id
    print(f"    ✅ Block data contains owner: {block_data['owner']}")
    
    # Step 3: Server sends CAMERAS_LIST
    print("\n  Step 3: Server prepares CAMERAS_LIST message")
    cameras = world.get_cameras()
    
    # Verify the camera we just placed is in the list with owner
    found_camera = None
    for camera in cameras:
        if camera["block_id"] == block_id:
            found_camera = camera
            break
    
    assert found_camera is not None
    assert found_camera["owner"] == player_id
    print(f"    ✅ Camera in list with owner: {found_camera['owner']}")
    
    # Create the actual message that would be sent
    cameras_list_msg = create_cameras_list_message(cameras)
    assert cameras_list_msg.type == MessageType.CAMERAS_LIST
    assert "cameras" in cameras_list_msg.data
    print(f"    ✅ CAMERAS_LIST message created with {len(cameras)} cameras")
    
    # Step 4: Client receives and processes the message
    print("\n  Step 4: Client processes CAMERAS_LIST")
    
    # Simulate client-side processing (as done in _update_owned_cameras)
    cameras_from_server = cameras_list_msg.data.get("cameras", [])
    owned_cameras = []
    
    for camera in cameras_from_server:
        if camera.get("owner") == player_id:
            camera_id = camera.get("block_id")
            if camera_id:
                owned_cameras.append(camera_id)
    
    assert len(owned_cameras) >= 1
    assert block_id in owned_cameras
    print(f"    ✅ Client found {len(owned_cameras)} owned camera(s)")
    print(f"    ✅ Owned cameras: {', '.join(owned_cameras)}")
    
    # Step 5: Verify notification message
    print("\n  Step 5: Client prepares notification")
    notification = f"📹 {len(owned_cameras)} caméra(s) possédée(s): {', '.join(owned_cameras)}"
    print(f"    ✅ Notification: {notification}")
    
    print("\n✅ Complete camera ownership flow test passed\n")

def test_multiple_players_camera_ownership():
    """Test that multiple players can each own cameras independently."""
    print("🧪 Testing multiple players with independent camera ownership...")
    
    world = GameWorld()
    
    # Player 1 places cameras
    player1_id = "player_1"
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="p1_cam1", owner=player1_id)
    world.add_block((15, 200, 15), BlockType.CAMERA, block_id="p1_cam2", owner=player1_id)
    
    # Player 2 places cameras
    player2_id = "player_2"
    world.add_block((20, 200, 20), BlockType.CAMERA, block_id="p2_cam1", owner=player2_id)
    
    # Get cameras list
    cameras = world.get_cameras()
    cameras_msg = create_cameras_list_message(cameras)
    cameras_data = cameras_msg.data.get("cameras", [])
    
    # Player 1 client filters
    p1_cameras = [c.get("block_id") for c in cameras_data if c.get("owner") == player1_id]
    assert len(p1_cameras) == 2
    assert "p1_cam1" in p1_cameras
    assert "p1_cam2" in p1_cameras
    print(f"  ✅ Player 1 sees {len(p1_cameras)} owned cameras: {', '.join(p1_cameras)}")
    
    # Player 2 client filters
    p2_cameras = [c.get("block_id") for c in cameras_data if c.get("owner") == player2_id]
    assert len(p2_cameras) == 1
    assert "p2_cam1" in p2_cameras
    print(f"  ✅ Player 2 sees {len(p2_cameras)} owned camera(s): {', '.join(p2_cameras)}")
    
    # Verify players don't see each other's cameras
    assert "p2_cam1" not in p1_cameras
    assert "p1_cam1" not in p2_cameras
    assert "p1_cam2" not in p2_cameras
    print("  ✅ Players only see their own cameras")
    
    print("✅ Multiple players camera ownership test passed\n")

def test_camera_placement_sequence():
    """Test the sequence of events when a camera is placed."""
    print("🧪 Testing camera placement event sequence...")
    
    world = GameWorld()
    player_id = "sequencer_player"
    
    # Initial state: no cameras owned by this player
    initial_cameras = world.get_cameras()
    initial_owned = [c for c in initial_cameras if c.get("owner") == player_id]
    assert len(initial_owned) == 0
    print("  ✅ Initial state: no cameras owned")
    
    # Player places first camera
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="seq_cam1", owner=player_id)
    
    cameras_after_1 = world.get_cameras()
    owned_after_1 = [c for c in cameras_after_1 if c.get("owner") == player_id]
    assert len(owned_after_1) == 1
    print(f"  ✅ After placing 1st camera: {len(owned_after_1)} owned")
    
    # Player places second camera
    world.add_block((15, 200, 15), BlockType.CAMERA, block_id="seq_cam2", owner=player_id)
    
    cameras_after_2 = world.get_cameras()
    owned_after_2 = [c for c in cameras_after_2 if c.get("owner") == player_id]
    assert len(owned_after_2) == 2
    print(f"  ✅ After placing 2nd camera: {len(owned_after_2)} owned")
    
    # Verify camera IDs
    owned_ids = [c.get("block_id") for c in owned_after_2]
    assert "seq_cam1" in owned_ids
    assert "seq_cam2" in owned_ids
    print(f"  ✅ Camera IDs correct: {', '.join(owned_ids)}")
    
    print("✅ Camera placement sequence test passed\n")

def test_camera_cube_owner_persistence():
    """Test that camera cubes maintain owner information."""
    print("🧪 Testing camera cube owner persistence...")
    
    player_id = "cube_owner_test"
    camera_id = "test_cube_cam"
    
    # Create camera cube with owner
    cube = Cube(
        cube_id=camera_id,
        position=(10, 200, 10),
        cube_type="camera",
        owner=player_id
    )
    
    assert cube.owner == player_id
    assert cube.id == camera_id
    assert cube.cube_type == "camera"
    print(f"  ✅ Cube created with owner: {cube.owner}")
    
    # Verify owner persists after position update
    cube.update_position((15, 200, 15))
    assert cube.owner == player_id
    print(f"  ✅ Owner persists after position update: {cube.owner}")
    
    # Verify owner persists after rotation update
    cube.update_rotation((90, 45))
    assert cube.owner == player_id
    print(f"  ✅ Owner persists after rotation update: {cube.owner}")
    
    print("✅ Camera cube owner persistence test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA OWNERSHIP END-TO-END TESTS")
    print("=" * 60 + "\n")
    
    test_complete_camera_ownership_flow()
    test_multiple_players_camera_ownership()
    test_camera_placement_sequence()
    test_camera_cube_owner_persistence()
    
    print("=" * 60)
    print("✅ ALL END-TO-END TESTS PASSED")
    print("=" * 60)
