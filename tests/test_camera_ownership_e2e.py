#!/usr/bin/env python3
"""
End-to-end simulation test for camera ownership.
This test simulates the full client-server interaction including:
1. Player joins server
2. Server sends WORLD_INIT with player_id
3. Client extracts player_id
4. Player places camera
5. Server creates camera with owner
6. Server broadcasts WORLD_UPDATE
7. Client requests camera list
8. Server sends CAMERAS_LIST
9. Client updates owned_cameras
10. Client can start recording with F1
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

class MockClient:
    """Mock client to simulate client behavior."""
    
    def __init__(self):
        self.player_id = None
        self.owned_cameras = []
    
    def handle_world_init(self, message):
        """Handle WORLD_INIT message (simulating AdvancedNetworkClient)."""
        # Extract player_id from WORLD_INIT message
        player_id = message.data.get("player_id")
        if player_id:
            self.player_id = player_id
            print(f"  ✅ Client: Player ID extracted: {player_id}")
            return True
        else:
            print(f"  ❌ Client: No player_id in WORLD_INIT")
            return False
    
    def can_request_cameras(self):
        """Check if client can request cameras list."""
        if not self.player_id:
            print(f"  ⚠️  Client: Cannot request cameras (player_id not set)")
            return False
        return True
    
    def handle_cameras_list(self, message):
        """Handle CAMERAS_LIST message (simulating MinecraftWindow._update_owned_cameras)."""
        self.owned_cameras = []
        
        if not self.player_id:
            print(f"  ⚠️  Client: Cannot update owned cameras (player_id not set)")
            return False
        
        cameras = message.data.get("cameras", [])
        print(f"  🔍 Client: Checking {len(cameras)} cameras for owner {self.player_id}")
        
        for camera in cameras:
            if camera.get("owner") == self.player_id:
                camera_id = camera.get("block_id")
                if camera_id:
                    self.owned_cameras.append(camera_id)
                    print(f"    ✅ Client: Found owned camera: {camera_id}")
        
        if self.owned_cameras:
            print(f"  📹 Client: {len(self.owned_cameras)} caméra(s) possédée(s): {', '.join(self.owned_cameras)}")
            return True
        else:
            print(f"  ℹ️  Client: No owned cameras found")
            return False
    
    def can_start_recording(self, camera_index):
        """Check if client can start recording for a camera."""
        if len(self.owned_cameras) == 0:
            print(f"  ⚠️  Client: No owned cameras")
            return False
        
        if camera_index >= len(self.owned_cameras):
            print(f"  ⚠️  Client: Camera index {camera_index} out of range")
            return False
        
        camera_id = self.owned_cameras[camera_index]
        print(f"  🎬 Client: Can start recording for {camera_id}")
        return True

def test_end_to_end_camera_ownership():
    """Test complete end-to-end camera ownership flow."""
    print("=" * 70)
    print("END-TO-END CAMERA OWNERSHIP SIMULATION")
    print("=" * 70)
    
    # Setup
    world = GameWorld()
    client = MockClient()
    player_id = "player_abc123"
    camera_position = (50, 100, 50)
    camera_counter = 0
    
    # Step 1: Player joins server
    print("\n" + "=" * 70)
    print("STEP 1: Player joins server")
    print("=" * 70)
    print(f"  Player ID: {player_id}")
    
    # Step 2: Server sends WORLD_INIT with player_id
    print("\n" + "=" * 70)
    print("STEP 2: Server sends WORLD_INIT with player_id")
    print("=" * 70)
    world_data = {
        "world_size": 128,
        "spawn_position": [64, 100, 64],
        "player_id": player_id  # Server includes player_id
    }
    world_init_msg = create_world_init_message(world_data)
    print(f"  Server: Sending WORLD_INIT with player_id={player_id}")
    
    # Step 3: Client receives WORLD_INIT and extracts player_id
    print("\n" + "=" * 70)
    print("STEP 3: Client receives WORLD_INIT and extracts player_id")
    print("=" * 70)
    if not client.handle_world_init(world_init_msg):
        print("\n❌ FAILED: Client did not extract player_id")
        return False
    
    # Step 4: Client requests camera list (should work now)
    print("\n" + "=" * 70)
    print("STEP 4: Client requests initial camera list")
    print("=" * 70)
    if not client.can_request_cameras():
        print("\n❌ FAILED: Client cannot request cameras")
        return False
    print(f"  ✅ Client: Can request cameras")
    
    # Server sends empty camera list initially
    cameras_msg = create_cameras_list_message([])
    client.handle_cameras_list(cameras_msg)
    
    # Step 5: Player places camera block
    print("\n" + "=" * 70)
    print("STEP 5: Player places camera block")
    print("=" * 70)
    print(f"  Position: {camera_position}")
    
    # Server processes camera placement
    block_id = f"camera_{camera_counter}"
    camera_counter += 1
    owner = player_id
    
    result = world.add_block(camera_position, BlockType.CAMERA, block_id=block_id, owner=owner)
    print(f"  Server: Created camera {block_id} owned by {owner}")
    print(f"  Server: Camera added to world: {result}")
    
    # Step 6: Server broadcasts WORLD_UPDATE
    print("\n" + "=" * 70)
    print("STEP 6: Server broadcasts WORLD_UPDATE")
    print("=" * 70)
    update_msg = create_world_update_message([
        BlockUpdate(camera_position, BlockType.CAMERA, player_id)
    ])
    print(f"  Server: Broadcasting WORLD_UPDATE for camera at {camera_position}")
    
    # Step 7: Client detects camera placement and requests camera list
    print("\n" + "=" * 70)
    print("STEP 7: Client detects camera and requests camera list")
    print("=" * 70)
    
    # Check that camera was placed
    block_data = update_msg.data.get("blocks", [])[0]
    if BlockUpdate.from_dict(block_data).block_type == BlockType.CAMERA:
        print(f"  ✅ Client: Detected camera placement")
        
        if client.can_request_cameras():
            print(f"  ✅ Client: Requesting camera list")
        else:
            print(f"\n❌ FAILED: Client cannot request camera list")
            return False
    
    # Step 8: Server sends CAMERAS_LIST
    print("\n" + "=" * 70)
    print("STEP 8: Server sends CAMERAS_LIST")
    print("=" * 70)
    cameras = world.get_cameras()
    cameras_msg = create_cameras_list_message(cameras)
    print(f"  Server: Sending {len(cameras)} cameras")
    
    # Step 9: Client updates owned_cameras
    print("\n" + "=" * 70)
    print("STEP 9: Client processes CAMERAS_LIST and updates owned_cameras")
    print("=" * 70)
    if not client.handle_cameras_list(cameras_msg):
        print(f"\n❌ FAILED: Client has no owned cameras")
        return False
    
    # Step 10: Verify client can start recording
    print("\n" + "=" * 70)
    print("STEP 10: Verify client can start recording with F1")
    print("=" * 70)
    if not client.can_start_recording(0):
        print(f"\n❌ FAILED: Client cannot start recording")
        return False
    
    # Final verification
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)
    
    checks = [
        ("Player ID extracted", client.player_id == player_id),
        ("Camera created with owner", block_id in [c.get("block_id") for c in cameras]),
        ("Client has owned cameras", len(client.owned_cameras) > 0),
        ("Owned camera matches", block_id in client.owned_cameras),
        ("Can start recording", True),
    ]
    
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("\n")
    success = test_end_to_end_camera_ownership()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ END-TO-END TEST PASSED")
        print("=" * 70)
        print("\nAll steps completed successfully:")
        print("  1. ✅ Player ID extracted from WORLD_INIT")
        print("  2. ✅ Camera list request sent")
        print("  3. ✅ Camera created with owner")
        print("  4. ✅ Owned cameras detected")
        print("  5. ✅ Recording can be started with F1")
        sys.exit(0)
    else:
        print("❌ END-TO-END TEST FAILED")
        print("=" * 70)
        sys.exit(1)
