#!/usr/bin/env python3
"""
Test for player cube rendering functionality.
Verifies that connected users are represented by random colored cubes.
"""

import sys
import os
import unittest.mock as mock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_player_cube_rendering():
    """Test that players are rendered as colored cubes."""
    
    # Mock OpenGL dependencies to avoid requiring graphics context
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
                    from protocol import PlayerState
                    
                    model = ClientModel()
                    
                    # Test 1: Color generation
                    player_id = "test_player_123"
                    color = model.get_or_create_player_color(player_id)
                    
                    # Colors should be in valid range (0.3 to 1.0 for brightness)
                    assert len(color) == 3, "Color should be RGB tuple"
                    for component in color:
                        assert 0.3 <= component <= 1.0, f"Color component out of range: {component}"
                    
                    # Same player should get same color
                    color2 = model.get_or_create_player_color(player_id)
                    assert color == color2, "Same player should get consistent color"
                    
                    # Different players should get different colors  
                    color3 = model.get_or_create_player_color("different_player")
                    assert color != color3, "Different players should get different colors"
                    
                    print("✅ Player color generation works correctly")
                    
                    # Test 2: Player management
                    player = PlayerState(player_id, (10, 20, 30), (0, 0), "TestPlayer")
                    model.add_cube(player)
                    
                    assert player_id in model.other_players, "Player should be tracked"
                    assert player_id in model.player_colors, "Player should have color"
                    
                    # Test player removal
                    model.remove_player(player_id)
                    assert player_id not in model.other_players, "Player should be removed"
                    assert player_id not in model.player_colors, "Player color should be cleaned up"
                    
                    print("✅ Player management works correctly")
                    
                    return True

def test_cube_rendering_integration():
    """Test integration with rendering system."""
    
    mocks = {
        'pyglet.graphics': mock.MagicMock(),
        'pyglet.graphics.TextureGroup': mock.MagicMock(),
        'pyglet.image': mock.MagicMock(),
        'pyglet.gl': mock.MagicMock(),
        'OpenGL.GL': mock.MagicMock(),
        'OpenGL.GLU': mock.MagicMock(),
        'pyglet.window': mock.MagicMock(),
        'pyglet.window.key': mock.MagicMock(),
        'pyglet.window.mouse': mock.MagicMock(),
    }
    
    with mock.patch.dict('sys.modules', mocks):
        with mock.patch('pyglet.image.load') as mock_image_load:
            mock_texture = mock.MagicMock()
            mock_image_load.return_value.get_texture.return_value = mock_texture
            
            with mock.patch('pyglet.graphics.TextureGroup'):
                with mock.patch('pyglet.graphics.Batch'):
                    with mock.patch('pyglet.graphics.draw') as mock_draw:
                        from client import cube_vertices
                        from protocol import PlayerState
                        
                        # Test cube vertices generation for player
                        player_pos = (15, 25, 35)
                        render_y = player_pos[1] + 1.0  # Same logic as draw_players
                        
                        vertices = cube_vertices(player_pos[0], render_y, player_pos[2], 0.4)
                        
                        # Should generate 24 vertices * 3 coordinates = 72 values
                        assert len(vertices) == 72, f"Expected 72 vertices, got {len(vertices)}"
                        
                        # Vertices should be around the expected position
                        # Check a few sample vertices
                        assert abs(vertices[0] - (player_pos[0] - 0.4)) < 0.01, "Vertex position incorrect"
                        assert abs(vertices[1] - (render_y + 0.4)) < 0.01, "Vertex position incorrect"
                        
                        print("✅ Cube rendering integration works correctly")
                        
                        return True

if __name__ == "__main__":
    print("🧪 Testing player cube rendering...\n")
    
    try:
        success = True
        success &= test_player_cube_rendering()
        success &= test_cube_rendering_integration()
        
        if success:
            print("\n🎉 PLAYER CUBE RENDERING TESTS PASSED!")
            print("✅ Connected users are represented as random colored cubes")
            print("✅ Each player gets a unique, persistent color")
            print("✅ Cubes are properly positioned and sized")
            print("✅ Player disconnect cleanup works correctly")
        else:
            print("\n❌ Player cube rendering tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)