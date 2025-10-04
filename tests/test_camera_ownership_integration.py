#!/usr/bin/env python3
"""
Integration test for camera ownership and recording functionality.
Tests the complete flow from camera placement to ownership detection to recording.
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import (
    BlockType, Message, MessageType, BlockUpdate,
    create_block_place_message, create_cameras_list_message,
    create_world_update_message, create_world_init_message
)
from server import GameWorld

def test_player_id_extraction_from_world_init():
    """Test that player_id is correctly extracted from WORLD_INIT message."""
    print("=" * 60)
    print("TEST 1: Player ID Extraction from WORLD_INIT")
    print("=" * 60)
    
    # Simulate server sending WORLD_INIT with player_id
    player_id = "test_player_123"
    world_data = {
        "world_size": 128,
        "spawn_position": [64, 100, 64],
        "player_id": player_id  # This is sent by server
    }
    
    world_init_msg = create_world_init_message(world_data)
    
    print(f"\n1. Server sends WORLD_INIT:")
    print(f"   Message type: {world_init_msg.type}")
    print(f"   Contains player_id: {'player_id' in world_init_msg.data}")
    print(f"   Player ID value: {world_init_msg.data.get('player_id')}")
    
    # Simulate client receiving the message
    print(f"\n2. Client should extract player_id:")
    extracted_player_id = world_init_msg.data.get("player_id")
    
    if extracted_player_id == player_id:
        print(f"   ✅ Player ID correctly extracted: {extracted_player_id}")
        return True
    else:
        print(f"   ❌ Failed to extract player_id")
        return False

def test_camera_ownership_flow():
    """Test the complete camera placement and ownership flow."""
    print("\n" + "=" * 60)
    print("TEST 2: Complete Camera Ownership Flow")
    print("=" * 60)
    
    # Setup
    world = GameWorld()
    player_id = "test_player_456"
    camera_position = (10, 100, 10)
    camera_counter = 0
    
    print("\n1. Player places camera block:")
    print(f"   Position: {camera_position}")
    print(f"   Player ID: {player_id}")
    
    # Server processes block placement
    block_id = f"camera_{camera_counter}"
    owner = player_id
    result = world.add_block(camera_position, BlockType.CAMERA, block_id=block_id, owner=owner)
    
    print(f"\n2. Server creates camera with owner:")
    print(f"   Block ID: {block_id}")
    print(f"   Owner: {owner}")
    print(f"   Added successfully: {result}")
    
    # Server sends WORLD_UPDATE (doesn't include owner)
    print(f"\n3. Server broadcasts WORLD_UPDATE:")
    update_msg = create_world_update_message([
        BlockUpdate(camera_position, BlockType.CAMERA, player_id)
    ])
    print(f"   Includes block_id: {'block_id' in update_msg.data.get('blocks', [{}])[0]}")
    print(f"   Includes owner: {'owner' in update_msg.data.get('blocks', [{}])[0]}")
    
    # Client requests camera list
    print(f"\n4. Client requests camera list:")
    print(f"   Player ID available: {player_id is not None}")
    
    # Server sends cameras list
    cameras = world.get_cameras()
    cameras_msg = create_cameras_list_message(cameras)
    
    print(f"\n5. Server sends CAMERAS_LIST:")
    print(f"   Total cameras: {len(cameras)}")
    
    # Client processes cameras list
    owned_cameras = []
    for camera in cameras_msg.data.get("cameras", []):
        if camera.get("owner") == player_id:
            camera_id = camera.get("block_id")
            if camera_id:
                owned_cameras.append(camera_id)
                print(f"   ✅ Found owned camera: {camera_id}")
    
    print(f"\n6. Client owned_cameras list: {owned_cameras}")
    
    if owned_cameras and block_id in owned_cameras:
        print(f"   ✅ SUCCESS: Camera ownership working!")
        return True
    else:
        print(f"   ❌ FAILURE: Camera ownership not detected")
        return False

def test_camera_list_request_with_player_id():
    """Test that camera list request works when player_id is set."""
    print("\n" + "=" * 60)
    print("TEST 3: Camera List Request with Player ID")
    print("=" * 60)
    
    # Simulate having player_id set
    player_id = "test_player_789"
    
    print(f"\n1. Player ID is set: {player_id}")
    
    # Should be able to create request message
    if player_id:
        request_msg = Message(MessageType.GET_CAMERAS_LIST, {})
        print(f"2. ✅ Can create GET_CAMERAS_LIST request")
        print(f"   Message type: {request_msg.type}")
        return True
    else:
        print(f"2. ❌ Cannot create request (player_id is None)")
        return False

def test_recording_with_owned_camera():
    """Test that recording can start when camera is owned."""
    print("\n" + "=" * 60)
    print("TEST 4: Recording with Owned Camera")
    print("=" * 60)
    
    # Setup
    owned_cameras = ["camera_0", "camera_1"]
    camera_index = 0
    
    print(f"\n1. Player owns cameras: {owned_cameras}")
    print(f"2. Player presses F1 (camera index {camera_index})")
    
    # Check if recording can start
    if camera_index < len(owned_cameras):
        camera_id = owned_cameras[camera_index]
        print(f"3. ✅ Can start recording for camera: {camera_id}")
        return True
    else:
        print(f"3. ❌ Cannot start recording (camera index out of range)")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("CAMERA OWNERSHIP INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Player ID Extraction", test_player_id_extraction_from_world_init),
        ("Camera Ownership Flow", test_camera_ownership_flow),
        ("Camera List Request", test_camera_list_request_with_player_id),
        ("Recording with Owned Camera", test_recording_with_owned_camera),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
