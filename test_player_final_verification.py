#!/usr/bin/env python3
"""
Test player colors, positions, and visibility in the unified cube system.
"""

import sys
import os
import unittest.mock as mock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_player_colors_positions_visibility():
    """Test that player colors, positions, and visibility work correctly."""
    
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
                    
                    # Test 1: Player colors are correctly assigned
                    local_player = model.create_local_player("local_123", (10, 20, 30))
                    assert local_player.color is not None, "Local player should have a color"
                    assert len(local_player.color) == 3, "Color should be RGB tuple"
                    for component in local_player.color:
                        assert 0.3 <= component <= 1.0, "Color components should be in valid range"
                    
                    # Add remote players and check colors
                    remote1 = PlayerState("remote_456", (50, 60, 70), (0, 0))
                    remote2 = PlayerState("remote_789", (80, 90, 100), (0, 0))
                    
                    model.add_cube(remote1)
                    model.add_cube(remote2)
                    
                    assert remote1.color is not None, "Remote player 1 should have a color"
                    assert remote2.color is not None, "Remote player 2 should have a color"
                    assert remote1.color != remote2.color, "Different players should have different colors"
                    assert local_player.color != remote1.color, "Local and remote players should have different colors"
                    
                    print("✅ Player colors are correctly assigned and unique")
                    
                    # Test 2: Player positions work correctly
                    assert local_player.position == (10, 20, 30), "Local player should have correct position"
                    assert remote1.position == (50, 60, 70), "Remote player 1 should have correct position"
                    assert remote2.position == (80, 90, 100), "Remote player 2 should have correct position"
                    
                    # Test position updates
                    local_player.update_position((15, 25, 35))
                    assert local_player.position == (15, 25, 35), "Local player position should update"
                    
                    remote1.update_position((55, 65, 75))
                    assert remote1.position == (55, 65, 75), "Remote player position should update"
                    
                    print("✅ Player positions work correctly")
                    
                    # Test 3: Render positions are elevated
                    local_render_pos = local_player.get_render_position()
                    assert local_render_pos == (15, 25.5, 35), "Local player render position should be elevated by size (0.5)"
                    
                    remote_render_pos = remote1.get_render_position()
                    assert remote_render_pos == (55, 65.5, 75), "Remote player render position should be elevated by size (0.5)"
                    
                    print("✅ Render positions are correctly elevated")
                    
                    # Test 4: Visibility - local player is not in other_players
                    other_players = model.other_players
                    assert len(other_players) == 2, "Should have 2 other players"
                    assert "local_123" not in other_players, "Local player should not be visible to self"
                    assert "remote_456" in other_players, "Remote player 1 should be visible"
                    assert "remote_789" in other_players, "Remote player 2 should be visible"
                    
                    print("✅ Player visibility works correctly (local player not visible to self)")
                    
                    # Test 5: All cubes includes everyone
                    all_cubes = model.get_all_cubes()
                    assert len(all_cubes) == 3, "Should have all 3 cubes"
                    cube_ids = {cube.id for cube in all_cubes}
                    assert "local_123" in cube_ids, "Local player should be in all cubes"
                    assert "remote_456" in cube_ids, "Remote player 1 should be in all cubes"
                    assert "remote_789" in cube_ids, "Remote player 2 should be in all cubes"
                    
                    print("✅ All cubes collection works correctly")
                    
                    # Test 6: Cube sizes are consistent
                    assert local_player.size == 0.5, "Local player should have correct cube size"
                    assert remote1.size == 0.5, "Remote player 1 should have correct cube size"
                    assert remote2.size == 0.5, "Remote player 2 should have correct cube size"
                    
                    print("✅ Cube sizes are consistent")
                    
                    # Test 7: Player removal works and cleans up properly
                    model.remove_cube("remote_456")
                    
                    assert len(model.get_all_cubes()) == 2, "Should have 2 cubes after removal"
                    assert len(model.other_players) == 1, "Should have 1 other player after removal"
                    assert "remote_456" not in model.cubes, "Removed player should not be in cubes"
                    assert "remote_456" not in model.other_players, "Removed player should not be in other_players"
                    
                    print("✅ Player removal works and cleans up properly")
                    
                    return True

def test_cube_rendering_data():
    """Test that cube rendering data is generated correctly."""
    
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
                    from client import cube_vertices
                    from protocol import PlayerState
                    
                    # Test cube vertices generation
                    player = PlayerState("test_player", (10, 20, 30), (0, 0))
                    player.size = 0.5  # Use standard 1x1x1 cube size
                    render_pos = player.get_render_position()  # (10, 20.5, 30)
                    
                    vertices = cube_vertices(render_pos[0], render_pos[1], render_pos[2], player.size)
                    
                    # Should generate 24 vertices * 3 coordinates = 72 values
                    assert len(vertices) == 72, f"Expected 72 vertices, got {len(vertices)}"
                    
                    # Check a few sample vertices for correct positioning
                    # First vertex should be at (x-size, y+size, z-size)
                    expected_x = render_pos[0] - player.size  # 10 - 0.5 = 9.5
                    expected_y = render_pos[1] + player.size  # 20.5 + 0.5 = 21.0
                    expected_z = render_pos[2] - player.size  # 30 - 0.5 = 29.5
                    
                    assert abs(vertices[0] - expected_x) < 0.01, "First vertex X should be correct"
                    assert abs(vertices[1] - expected_y) < 0.01, "First vertex Y should be correct"
                    assert abs(vertices[2] - expected_z) < 0.01, "First vertex Z should be correct"
                    
                    print("✅ Cube rendering data is generated correctly")
                    
                    return True

if __name__ == "__main__":
    print("🧪 Testing player colors, positions, and visibility...\n")
    
    try:
        success = True
        success &= test_player_colors_positions_visibility()
        success &= test_cube_rendering_data()
        
        if success:
            print("\n🎉 PLAYER COLORS, POSITIONS, AND VISIBILITY TESTS PASSED!")
            print("✅ Player colors are correctly assigned and unique")
            print("✅ Player positions work correctly for all cubes")
            print("✅ Render positions are properly elevated")
            print("✅ Local player is not visible to themselves")
            print("✅ Remote players are visible to local player")
            print("✅ All cubes collection includes everyone")
            print("✅ Cube sizes are consistent")
            print("✅ Player removal works and cleans up properly")
            print("✅ Cube rendering data is generated correctly")
        else:
            print("\n❌ Player colors, positions, and visibility tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)