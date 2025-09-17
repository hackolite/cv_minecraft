#!/usr/bin/env python3
"""
Test for player-to-player collision functionality.
Verifies that players cannot overlap and are properly pushed apart.
"""

import sys
import os
import unittest.mock as mock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_player_collision():
    """Test that players collide with each other and are properly separated."""
    
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
                    with mock.patch('asyncio.get_event_loop') as mock_loop:
                        mock_loop.return_value = mock.MagicMock()
                        
                        from client import ClientModel, Window
                        from protocol import PlayerState
                        
                        # Create a window and model for collision testing
                        window = Window(640, 480, "Test", resizable=True)
                        window.model = ClientModel()
                        window.position = (0, 20, 0)  # Local player position
                        window.dy = 0
                        
                        # Create local player
                        local_player = window.model.create_local_player("local", (0, 20, 0))
                        
                        # Create a remote player very close to local player
                        remote_player = PlayerState("remote", (0.5, 20, 0), (0, 0))
                        window.model.add_cube(remote_player)
                        
                        print("🧪 Testing player collision...")
                        print(f"Local player initial position: {window.position}")
                        print(f"Remote player position: {remote_player.position}")
                        
                        # Test collision when local player tries to move into remote player
                        new_position = window.collide((0.5, 20, 0), 2)  # Try to move to same spot as remote
                        
                        print(f"Position after collision check: {new_position}")
                        
                        # The collision system should have pushed the player away
                        assert new_position[0] != 0.5, "Player should be pushed away from collision"
                        
                        # Test that players are separated by at least the collision distance
                        distance_x = abs(new_position[0] - remote_player.position[0])
                        distance_z = abs(new_position[2] - remote_player.position[2])
                        min_distance = 0.4 * 2 + 0.25  # Two player radii plus padding
                        
                        print(f"Distance X: {distance_x}, Distance Z: {distance_z}, Min required: {min_distance}")
                        
                        assert distance_x >= min_distance or distance_z >= min_distance, \
                            "Players should be separated by minimum collision distance"
                        
                        print("✅ Player collision detection works correctly")
                        
                        return True


def test_multiple_player_collision():
    """Test collision with multiple players."""
    
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
                    with mock.patch('asyncio.get_event_loop') as mock_loop:
                        mock_loop.return_value = mock.MagicMock()
                        
                        from client import ClientModel, Window
                        from protocol import PlayerState
                        
                        # Create a window and model for collision testing
                        window = Window(640, 480, "Test", resizable=True)
                        window.model = ClientModel()
                        window.position = (0, 20, 0)  # Local player position
                        window.dy = 0
                        
                        # Create local player
                        local_player = window.model.create_local_player("local", (0, 20, 0))
                        
                        # Create multiple remote players around the local player
                        remote_player1 = PlayerState("remote1", (0.4, 20, 0.4), (0, 0))
                        remote_player2 = PlayerState("remote2", (-0.4, 20, -0.4), (0, 0))
                        window.model.add_cube(remote_player1)
                        window.model.add_cube(remote_player2)
                        
                        print("🧪 Testing multiple player collision...")
                        print(f"Local player initial position: {window.position}")
                        print(f"Remote player 1 position: {remote_player1.position}")
                        print(f"Remote player 2 position: {remote_player2.position}")
                        
                        # Test collision when local player tries to move into area with multiple players
                        new_position = window.collide((0.1, 20, 0.1), 2)
                        
                        print(f"Position after collision check: {new_position}")
                        
                        # Check that local player is not overlapping with either remote player
                        distance1_x = abs(new_position[0] - remote_player1.position[0])
                        distance1_z = abs(new_position[2] - remote_player1.position[2])
                        distance2_x = abs(new_position[0] - remote_player2.position[0])
                        distance2_z = abs(new_position[2] - remote_player2.position[2])
                        
                        min_distance = 0.4 * 2 + 0.25  # Two player radii plus padding
                        
                        collision1 = distance1_x < min_distance and distance1_z < min_distance
                        collision2 = distance2_x < min_distance and distance2_z < min_distance
                        
                        assert not collision1, "Local player should not collide with remote player 1"
                        assert not collision2, "Local player should not collide with remote player 2"
                        
                        print("✅ Multiple player collision detection works correctly")
                        
                        return True


if __name__ == "__main__":
    print("🧪 Testing player collision system...\n")
    
    try:
        success = True
        success &= test_player_collision()
        success &= test_multiple_player_collision()
        
        if success:
            print("\n🎉 PLAYER COLLISION TESTS PASSED!")
            print("✅ Players cannot overlap each other")
            print("✅ Players are properly pushed apart when colliding")
            print("✅ Multiple player collision handling works")
            print("✅ Collision detection maintains proper distances")
        else:
            print("\n❌ Player collision tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)