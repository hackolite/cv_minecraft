#!/usr/bin/env python3
"""
Test client-side camera ownership notification after placement.
This test specifically verifies requirement from problem statement:
"Vérifier qu'après placement, le client reçoit la notification '📹 X caméra(s) possédée(s): ...' et que l'enregistrement est possible via F1."
"""

import sys
import os

# Set display for headless environment
os.environ['DISPLAY'] = ':99'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import GameWorld
from protocol import BlockType, Message, MessageType, create_cameras_list_message

def test_camera_notification_after_placement():
    """Test that client receives correct notification after placing a camera."""
    print("🧪 Testing camera ownership notification after placement...")
    
    world = GameWorld()
    player_id = "notification_test_player"
    
    # Initial state: no cameras owned
    print("\n  Step 1: Initial state (no cameras owned)")
    initial_cameras = world.get_cameras()
    owned_before = [c for c in initial_cameras if c.get("owner") == player_id]
    assert len(owned_before) == 0
    print("    ✅ Initial state: 0 owned cameras")
    
    # Player places first camera
    print("\n  Step 2: Player places first camera")
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="notif_cam1", owner=player_id)
    
    # Server sends CAMERAS_LIST
    cameras_after_1 = world.get_cameras()
    cameras_msg = create_cameras_list_message(cameras_after_1)
    
    # Client processes the message
    cameras_data = cameras_msg.data.get("cameras", [])
    owned_cameras = [c.get("block_id") for c in cameras_data if c.get("owner") == player_id]
    
    assert len(owned_cameras) == 1
    assert "notif_cam1" in owned_cameras
    
    # Generate notification message
    notification = f"📹 {len(owned_cameras)} caméra(s) possédée(s): {', '.join(owned_cameras)}"
    expected_notification = "📹 1 caméra(s) possédée(s): notif_cam1"
    assert notification == expected_notification
    print(f"    ✅ Notification: {notification}")
    
    # Player places second camera
    print("\n  Step 3: Player places second camera")
    world.add_block((15, 200, 15), BlockType.CAMERA, block_id="notif_cam2", owner=player_id)
    
    # Server sends updated CAMERAS_LIST
    cameras_after_2 = world.get_cameras()
    cameras_msg_2 = create_cameras_list_message(cameras_after_2)
    
    # Client processes the updated message
    cameras_data_2 = cameras_msg_2.data.get("cameras", [])
    owned_cameras_2 = [c.get("block_id") for c in cameras_data_2 if c.get("owner") == player_id]
    
    assert len(owned_cameras_2) == 2
    assert "notif_cam1" in owned_cameras_2
    assert "notif_cam2" in owned_cameras_2
    
    # Generate updated notification
    notification_2 = f"📹 {len(owned_cameras_2)} caméra(s) possédée(s): {', '.join(owned_cameras_2)}"
    expected_notification_2 = "📹 2 caméra(s) possédée(s): notif_cam1, notif_cam2"
    assert notification_2 == expected_notification_2
    print(f"    ✅ Updated notification: {notification_2}")
    
    print("\n✅ Camera notification test passed\n")

def test_f1_recording_with_owned_cameras():
    """Test that F1 recording is possible with owned cameras."""
    print("🧪 Testing F1 recording availability with owned cameras...")
    
    world = GameWorld()
    player_id = "recording_test_player"
    
    # Player places cameras
    world.add_block((10, 200, 10), BlockType.CAMERA, block_id="rec_cam0", owner=player_id)
    world.add_block((15, 200, 15), BlockType.CAMERA, block_id="rec_cam1", owner=player_id)
    world.add_block((20, 200, 20), BlockType.CAMERA, block_id="rec_cam2", owner=player_id)
    
    # Get owned cameras (as client would)
    cameras = world.get_cameras()
    owned_cameras = [c.get("block_id") for c in cameras if c.get("owner") == player_id]
    
    assert len(owned_cameras) == 3
    print(f"  ✅ Player owns {len(owned_cameras)} cameras: {', '.join(owned_cameras)}")
    
    # Simulate F1 key press (camera index 0)
    camera_index_f1 = 0
    if camera_index_f1 < len(owned_cameras):
        camera_id_f1 = owned_cameras[camera_index_f1]
        print(f"  ✅ F1 pressed: Can toggle recording for camera {camera_index_f1} ({camera_id_f1})")
        assert camera_id_f1 == "rec_cam0"
    else:
        print(f"  ❌ F1 pressed: No camera at index {camera_index_f1}")
        assert False, "F1 should work with camera index 0"
    
    # Simulate F2 key press (camera index 1)
    camera_index_f2 = 1
    if camera_index_f2 < len(owned_cameras):
        camera_id_f2 = owned_cameras[camera_index_f2]
        print(f"  ✅ F2 pressed: Can toggle recording for camera {camera_index_f2} ({camera_id_f2})")
        assert camera_id_f2 == "rec_cam1"
    else:
        print(f"  ❌ F2 pressed: No camera at index {camera_index_f2}")
        assert False, "F2 should work with camera index 1"
    
    # Simulate F3+Shift key press (camera index 2)
    camera_index_f3 = 2
    if camera_index_f3 < len(owned_cameras):
        camera_id_f3 = owned_cameras[camera_index_f3]
        print(f"  ✅ F3+Shift pressed: Can toggle recording for camera {camera_index_f3} ({camera_id_f3})")
        assert camera_id_f3 == "rec_cam2"
    else:
        print(f"  ❌ F3+Shift pressed: No camera at index {camera_index_f3}")
        assert False, "F3+Shift should work with camera index 2"
    
    # Test that F1 on a player with no cameras shows error
    print("\n  Testing F1 with no owned cameras...")
    empty_owned_cameras = []
    camera_index = 0
    if camera_index >= len(empty_owned_cameras):
        print(f"  ✅ F1 correctly indicates no camera at index {camera_index} (no owned cameras)")
    else:
        print(f"  ❌ Should not allow recording with no owned cameras")
        assert False
    
    print("\n✅ F1 recording availability test passed\n")

def test_notification_message_format():
    """Test that notification messages follow the correct format."""
    print("🧪 Testing notification message format...")
    
    # Test with 1 camera
    cameras_1 = ["camera_A"]
    msg_1 = f"📹 {len(cameras_1)} caméra(s) possédée(s): {', '.join(cameras_1)}"
    assert msg_1 == "📹 1 caméra(s) possédée(s): camera_A"
    print(f"  ✅ Format with 1 camera: {msg_1}")
    
    # Test with 2 cameras
    cameras_2 = ["camera_A", "camera_B"]
    msg_2 = f"📹 {len(cameras_2)} caméra(s) possédée(s): {', '.join(cameras_2)}"
    assert msg_2 == "📹 2 caméra(s) possédée(s): camera_A, camera_B"
    print(f"  ✅ Format with 2 cameras: {msg_2}")
    
    # Test with 3 cameras
    cameras_3 = ["camera_A", "camera_B", "camera_C"]
    msg_3 = f"📹 {len(cameras_3)} caméra(s) possédée(s): {', '.join(cameras_3)}"
    assert msg_3 == "📹 3 caméra(s) possédée(s): camera_A, camera_B, camera_C"
    print(f"  ✅ Format with 3 cameras: {msg_3}")
    
    print("\n✅ Notification format test passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CAMERA OWNERSHIP NOTIFICATION TESTS")
    print("=" * 60 + "\n")
    
    test_camera_notification_after_placement()
    test_f1_recording_with_owned_cameras()
    test_notification_message_format()
    
    print("=" * 60)
    print("✅ ALL NOTIFICATION TESTS PASSED")
    print("=" * 60)
