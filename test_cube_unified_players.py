#!/usr/bin/env python3
"""
Test unified cube-based player system.
Verifies that both local and remote players are represented as cubes with unified logic.
"""

import sys
import os
import unittest.mock as mock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_unified_cube_system():
    """Test that all players (local and remote) are handled as cubes."""
    
    # Mock OpenGL dependencies 
    mocks = {
        'pyglet.graphics': mock.MagicMock(),
        'pyglet.graphics.TextureGroup': mock.MagicMock(),
        'pyglet.image': mock.MagicMock(),
        'pyglet.gl': mock.MagicMock(),
        'OpenGL.GL': mock.MagicMock(),
        'OpenGL.GLU': mock.MagicMock(),
    }
    
    with mock.patch.dict('sys.modules', mocks):
        with mock.patch('pyglet.image.load') as mock_image_load:
            mock_texture = mock.MagicMock()
            mock_image_load.return_value.get_texture.return_value = mock_texture
            
            with mock.patch('pyglet.graphics.TextureGroup'):
                with mock.patch('pyglet.graphics.Batch'):
                    from client import ClientModel
                    from protocol import PlayerState, Cube
                    
                    model = ClientModel()
                    
                    # Test 1: Local player is created as a cube
                    local_player = model.create_local_player("local_123", (10, 20, 30), (45, -10), "LocalPlayer")
                    
                    assert local_player is not None, "Local player should be created"
                    assert isinstance(local_player, PlayerState), "Local player should be a PlayerState (which is a Cube)"
                    assert isinstance(local_player, Cube), "Local player should be a Cube"
                    assert local_player.is_local == True, "Local player should be marked as local"
                    assert local_player.id == "local_123", "Local player should have correct ID"
                    assert local_player.position == (10, 20, 30), "Local player should have correct position"
                    assert local_player.rotation == (45, -10), "Local player should have correct rotation"
                    assert local_player.size == 0.5, "Local player should have standard 1x1x1 cube size"
                    
                    print("✅ Local player is properly created as a cube")
                    
                    # Test 2: Remote players are added as cubes
                    remote_player = PlayerState("remote_456", (50, 60, 70), (90, 15), "RemotePlayer")
                    model.add_cube(remote_player)
                    
                    assert remote_player.id in model.cubes, "Remote player should be in cubes dict"
                    assert isinstance(model.cubes[remote_player.id], PlayerState), "Remote player should be PlayerState"
                    assert isinstance(model.cubes[remote_player.id], Cube), "Remote player should be Cube"
                    assert model.cubes[remote_player.id].is_local == False, "Remote player should not be local"
                    
                    print("✅ Remote players are properly added as cubes")
                    
                    # Test 3: All cubes can be retrieved uniformly
                    all_cubes = model.get_all_cubes()
                    assert len(all_cubes) == 2, "Should have both local and remote cubes"
                    
                    cube_ids = {cube.id for cube in all_cubes}
                    assert "local_123" in cube_ids, "Local player should be in all cubes"
                    assert "remote_456" in cube_ids, "Remote player should be in all cubes"
                    
                    print("✅ All cubes can be retrieved uniformly")
                    
                    # Test 4: Other cubes excludes local player
                    other_cubes = model.get_other_cubes()
                    assert len(other_cubes) == 1, "Should have only remote cube"
                    assert other_cubes[0].id == "remote_456", "Should be the remote player only"
                    
                    print("✅ Other cubes correctly excludes local player")
                    
                    # Test 5: Cube render positions work
                    local_render_pos = local_player.get_render_position()
                    assert local_render_pos == (10, 20.5, 30), "Local player render position should be elevated by size (0.5)"
                    
                    remote_render_pos = remote_player.get_render_position()
                    assert remote_render_pos == (50, 60.5, 70), "Remote player render position should be elevated by size (0.5)"
                    
                    print("✅ Cube render positions work correctly")
                    
                    # Test 6: Backward compatibility with other_players property
                    other_players = model.other_players
                    assert len(other_players) == 1, "Should have one other player"
                    assert "remote_456" in other_players, "Remote player should be in other_players"
                    assert "local_123" not in other_players, "Local player should not be in other_players"
                    
                    print("✅ Backward compatibility with other_players works")
                    
                    # Test 7: Cube removal works
                    removed_cube = model.remove_cube("remote_456")
                    assert removed_cube is not None, "Should return the removed cube"
                    assert removed_cube.id == "remote_456", "Should be the correct cube"
                    assert len(model.get_all_cubes()) == 1, "Should only have local player left"
                    assert len(model.get_other_cubes()) == 0, "Should have no other cubes"
                    
                    print("✅ Cube removal works correctly")
                    
                    return True

def test_cube_updates():
    """Test that cube position and rotation updates work."""
    
    # Mock OpenGL dependencies 
    mocks = {
        'pyglet.graphics': mock.MagicMock(),
        'pyglet.graphics.TextureGroup': mock.MagicMock(),
        'pyglet.image': mock.MagicMock(),
        'pyglet.gl': mock.MagicMock(),
        'OpenGL.GL': mock.MagicMock(),
        'OpenGL.GLU': mock.MagicMock(),
    }
    
    with mock.patch.dict('sys.modules', mocks):
        with mock.patch('pyglet.image.load') as mock_image_load:
            mock_texture = mock.MagicMock()
            mock_image_load.return_value.get_texture.return_value = mock_texture
            
            with mock.patch('pyglet.graphics.TextureGroup'):
                with mock.patch('pyglet.graphics.Batch'):
                    from protocol import PlayerState, Cube
                    
                    # Test cube position/rotation updates
                    cube = PlayerState("test_player", (0, 0, 0), (0, 0), "TestPlayer")
                    
                    # Test position update
                    cube.update_position((10, 20, 30))
                    assert cube.position == (10, 20, 30), "Position should be updated"
                    
                    # Test rotation update
                    cube.update_rotation((45, -30))
                    assert cube.rotation == (45, -30), "Rotation should be updated"
                    
                    print("✅ Cube position and rotation updates work")
                    
                    return True

if __name__ == "__main__":
    print("🧪 Testing unified cube-based player system...\n")
    
    try:
        success = True
        success &= test_unified_cube_system()
        success &= test_cube_updates()
        
        if success:
            print("\n🎉 UNIFIED CUBE SYSTEM TESTS PASSED!")
            print("✅ Local player is represented as a cube")
            print("✅ Remote players are represented as cubes")
            print("✅ All players use the same cube data structures")
            print("✅ Universe can handle all cubes uniformly")
            print("✅ No special cases needed for local vs remote players")
        else:
            print("\n❌ Unified cube system tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)