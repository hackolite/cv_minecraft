#!/usr/bin/env python3
"""
Test to verify that player rotation is properly updated for the local player cube.

This test validates the fix for the issue:
"l'utilisateur tourne autour de la brick mais on ne vois pas cet utilisateur originel"
(the user rotates around the brick but we don't see this original user)

The fix ensures that:
1. When the player rotates their view (mouse motion), the local_player_cube rotation is updated
2. When receiving PLAYER_UPDATE from server, both position AND rotation are updated
3. The local player cube is visible with correct rotation in camera views
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_rotation_updated_on_mouse_motion():
    """Test that on_mouse_motion updates local_player_cube rotation."""
    print("\n🧪 Test: on_mouse_motion updates local_player_cube.rotation")
    
    minecraft_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(minecraft_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the on_mouse_motion method
    assert 'def on_mouse_motion(self, x, y, dx, dy):' in content, \
        "on_mouse_motion method should exist"
    
    mouse_motion_section = content.split('def on_mouse_motion(self, x, y, dx, dy):', 1)[1].split('\n    def ', 1)[0]
    
    # Verify rotation is updated
    assert 'self.rotation = (x_rot, y_rot)' in mouse_motion_section, \
        "on_mouse_motion should update self.rotation"
    print("  ✓ on_mouse_motion updates self.rotation")
    
    # Verify local_player_cube rotation is updated
    assert 'if self.local_player_cube:' in mouse_motion_section, \
        "on_mouse_motion should check for local_player_cube"
    assert 'self.local_player_cube.update_rotation(self.rotation)' in mouse_motion_section, \
        "on_mouse_motion should call update_rotation on local_player_cube"
    print("  ✓ on_mouse_motion updates local_player_cube.rotation")
    
    print("\n✅ PASS: on_mouse_motion properly updates rotation")


def test_rotation_updated_on_player_update():
    """Test that PLAYER_UPDATE handler updates local_player_cube rotation."""
    print("\n🧪 Test: PLAYER_UPDATE handler updates local_player_cube.rotation")
    
    minecraft_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(minecraft_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the PLAYER_UPDATE handling section
    assert 'MessageType.PLAYER_UPDATE' in content, \
        "PLAYER_UPDATE handling should exist"
    
    player_update_section = content.split('elif message.type == MessageType.PLAYER_UPDATE:', 1)[1].split('elif message.type ==', 1)[0]
    
    # Verify rotation from player_data is extracted
    assert 'player_data["rotation"]' in player_update_section, \
        "PLAYER_UPDATE handler should extract rotation from player_data"
    assert 'self.window.rotation = tuple(player_data["rotation"])' in player_update_section, \
        "PLAYER_UPDATE handler should update window rotation"
    print("  ✓ PLAYER_UPDATE updates window rotation from server data")
    
    # Verify local_player_cube rotation is updated
    assert 'self.window.local_player_cube.update_rotation(self.window.rotation)' in player_update_section, \
        "PLAYER_UPDATE handler should update local_player_cube rotation"
    print("  ✓ PLAYER_UPDATE updates local_player_cube.rotation")
    
    print("\n✅ PASS: PLAYER_UPDATE properly updates rotation")


def test_rotation_is_sent_to_server():
    """Test that rotation is sent in player move messages."""
    print("\n🧪 Test: Rotation is sent to server in PLAYER_MOVE messages")
    
    minecraft_file = Path(__file__).parent.parent / 'minecraft_client_fr.py'
    
    with open(minecraft_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find _send_position_update method
    assert 'def _send_position_update(self):' in content, \
        "_send_position_update method should exist"
    
    send_position_section = content.split('def _send_position_update(self):', 1)[1].split('\n    def ', 1)[0]
    
    # Verify it sends both position and rotation
    assert 'create_player_move_message(self.position, self.rotation)' in send_position_section, \
        "_send_position_update should send both position and rotation"
    print("  ✓ _send_position_update sends both position and rotation to server")
    
    print("\n✅ PASS: Rotation is properly sent to server")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PLAYER ROTATION UPDATE TEST SUITE")
    print("=" * 70)
    
    try:
        test_rotation_updated_on_mouse_motion()
        test_rotation_updated_on_player_update()
        test_rotation_is_sent_to_server()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Player rotation updates are working!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
