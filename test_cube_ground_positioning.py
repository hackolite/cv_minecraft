#!/usr/bin/env python3
"""
Test cube ground positioning to verify cubes don't float.
This test verifies the fix for the issue: "la le cube de l'utilisateur flotte"
(the user cube floats).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, Cube
from client import ClientModel

def test_cubes_on_ground():
    """Test that cubes are properly positioned on the ground (not floating)."""
    print("🧪 Testing cube ground positioning...")
    
    # Test case 1: Player standing on ground level (Y=0)
    print("\n📍 Test Case 1: Player on ground level")
    player = PlayerState("ground_player", (0, 0, 0), (0, 0))
    render_pos = player.get_render_position()
    cube_bottom = render_pos[1] - player.size
    cube_top = render_pos[1] + player.size
    
    print(f"  Player position: {player.position}")
    print(f"  Player size (half-size): {player.size}")
    print(f"  Render position: {render_pos}")
    print(f"  Cube bottom Y: {cube_bottom}")
    print(f"  Cube top Y: {cube_top}")
    
    # Cube should sit on ground (bottom at Y=0)
    assert abs(cube_bottom - 0.0) < 0.001, "Cube bottom should be at ground level (Y=0)"
    assert abs(cube_top - 1.0) < 0.001, "Cube top should be at Y=1 for 1x1x1 cube"
    print("  ✅ Cube sits properly on ground")
    
    # Test case 2: Player standing on a block (Y=1)
    print("\n📍 Test Case 2: Player on block at Y=1")
    player_on_block = PlayerState("block_player", (0, 1, 0), (0, 0))
    render_pos_block = player_on_block.get_render_position()
    cube_bottom_block = render_pos_block[1] - player_on_block.size
    cube_top_block = render_pos_block[1] + player_on_block.size
    
    print(f"  Player position: {player_on_block.position}")
    print(f"  Player size (half-size): {player_on_block.size}")
    print(f"  Render position: {render_pos_block}")
    print(f"  Cube bottom Y: {cube_bottom_block}")
    print(f"  Cube top Y: {cube_top_block}")
    
    # Cube should sit on block (bottom at Y=1)
    assert abs(cube_bottom_block - 1.0) < 0.001, "Cube bottom should be at block level (Y=1)"
    assert abs(cube_top_block - 2.0) < 0.001, "Cube top should be at Y=2 for 1x1x1 cube"
    print("  ✅ Cube sits properly on block")
    
    return True

def test_client_model_cubes_on_ground():
    """Test that client model cubes are positioned correctly on ground."""
    print("\n🧪 Testing client model cube positioning...")
    
    model = ClientModel()
    
    # Create local player on ground
    local_player = model.create_local_player("local", (5, 2, 5), (0, 0), "LocalPlayer")
    render_pos = local_player.get_render_position()
    cube_bottom = render_pos[1] - local_player.size
    
    print(f"  Local player position: {local_player.position}")
    print(f"  Local player size: {local_player.size}")
    print(f"  Render position: {render_pos}")
    print(f"  Cube bottom Y: {cube_bottom}")
    
    # Player at Y=2 should have cube bottom at Y=2
    assert abs(cube_bottom - 2.0) < 0.001, "Local player cube should sit on ground at Y=2"
    print("  ✅ Local player cube positioned correctly")
    
    # Add remote player
    remote_player = PlayerState("remote", (10, 3, 10), (0, 0), "RemotePlayer")
    model.add_cube(remote_player)
    
    render_pos_remote = remote_player.get_render_position()
    cube_bottom_remote = render_pos_remote[1] - remote_player.size
    
    print(f"  Remote player position: {remote_player.position}")
    print(f"  Remote player size: {remote_player.size}")
    print(f"  Render position: {render_pos_remote}")
    print(f"  Cube bottom Y: {cube_bottom_remote}")
    
    # Player at Y=3 should have cube bottom at Y=3
    assert abs(cube_bottom_remote - 3.0) < 0.001, "Remote player cube should sit on ground at Y=3"
    print("  ✅ Remote player cube positioned correctly")
    
    return True

def test_standard_cube_size():
    """Test that all cubes are standardized to 1x1x1 size."""
    print("\n🧪 Testing standard cube sizes...")
    
    model = ClientModel()
    
    # Create various cubes
    local_player = model.create_local_player("local", (0, 0, 0), (0, 0))
    remote1 = PlayerState("remote1", (1, 0, 1), (0, 0))
    remote2 = PlayerState("remote2", (2, 0, 2), (0, 0))
    
    model.add_cube(remote1)
    model.add_cube(remote2)
    
    # All cubes should have size 0.5 (representing 1x1x1 cubes)
    expected_size = 0.5
    
    print(f"  Local player size: {local_player.size} (expected {expected_size})")
    print(f"  Remote player 1 size: {remote1.size} (expected {expected_size})")
    print(f"  Remote player 2 size: {remote2.size} (expected {expected_size})")
    
    assert local_player.size == expected_size, "Local player should have standard size"
    assert remote1.size == expected_size, "Remote player 1 should have standard size"
    assert remote2.size == expected_size, "Remote player 2 should have standard size"
    
    print("  ✅ All cubes have standard 1x1x1 size (0.5 half-size)")
    
    return True

if __name__ == "__main__":
    print("🎮 TESTING: Cube Ground Positioning Fix")
    print("=" * 50)
    print("This test verifies that cubes don't float and are properly positioned.")
    print()
    
    try:
        success = True
        success &= test_cubes_on_ground()
        success &= test_client_model_cubes_on_ground()
        success &= test_standard_cube_size()
        
        if success:
            print("\n🎉 ALL CUBE POSITIONING TESTS PASSED!")
            print("✅ Cubes are properly positioned on ground (not floating)")
            print("✅ All cubes are standardized to 1x1x1 size")
            print("✅ Client model handles cube positioning correctly")
            print("🎯 The 'cube de l'utilisateur flotte' issue has been FIXED!")
        else:
            print("\n❌ Some cube positioning tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)