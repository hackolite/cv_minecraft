#!/usr/bin/env python3
"""
Test to verify that the model has local_player_cube attribute.

This test validates the fix for the issue:
"l'utilisateur tourne autour de la brick camera mais depuis la brick camera, 
on ne voit pas cet utilisateur originel"

The fix ensures that:
1. EnhancedClientModel has a local_player_cube attribute
2. create_local_player() method sets model.local_player_cube
3. The local player is accessible from camera cube windows
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_enhanced_client_model_has_local_player_cube():
    """Test that EnhancedClientModel has local_player_cube attribute."""
    print("\n🧪 Test: EnhancedClientModel has local_player_cube attribute")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Check that the attribute exists
    assert hasattr(model, 'local_player_cube'), \
        "EnhancedClientModel should have local_player_cube attribute"
    print("  ✓ EnhancedClientModel has local_player_cube attribute")
    
    # Check that it's initialized to None
    assert model.local_player_cube is None, \
        "local_player_cube should be initialized to None"
    print("  ✓ local_player_cube is initialized to None")
    
    print("\n✅ PASS: EnhancedClientModel has local_player_cube")


def test_create_local_player_sets_local_player_cube():
    """Test that create_local_player() sets model.local_player_cube."""
    print("\n🧪 Test: create_local_player() sets model.local_player_cube")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Create a local player
    player = model.create_local_player(
        player_id="test_player_123",
        position=(10, 20, 30),
        rotation=(0, 0),
        name="Test Player"
    )
    
    # Check that local_player_cube is set
    assert model.local_player_cube is not None, \
        "create_local_player() should set model.local_player_cube"
    print("  ✓ create_local_player() sets model.local_player_cube")
    
    # Check that it's the same object as returned
    assert model.local_player_cube is player, \
        "model.local_player_cube should be the same object as returned by create_local_player()"
    print("  ✓ model.local_player_cube is the same object as returned")
    
    # Check that the player has the correct attributes
    assert hasattr(model.local_player_cube, 'get_render_position'), \
        "local_player_cube should have get_render_position method"
    print("  ✓ local_player_cube has get_render_position method")
    
    assert hasattr(model.local_player_cube, 'size'), \
        "local_player_cube should have size attribute"
    print("  ✓ local_player_cube has size attribute")
    
    assert hasattr(model.local_player_cube, 'color'), \
        "local_player_cube should have color attribute"
    print("  ✓ local_player_cube has color attribute")
    
    print("\n✅ PASS: create_local_player() correctly sets local_player_cube")


def test_client_model_create_local_player():
    """Test that ClientModel's create_local_player() also sets local_player_cube."""
    print("\n🧪 Test: ClientModel.create_local_player() sets local_player_cube")
    
    from client import ClientModel
    
    model = ClientModel()
    
    # Check that the attribute exists
    assert hasattr(model, 'local_player_cube'), \
        "ClientModel should have local_player_cube attribute"
    print("  ✓ ClientModel has local_player_cube attribute")
    
    # Create a local player
    player = model.create_local_player(
        player_id="test_player_456",
        position=(15, 25, 35),
        rotation=(45, -10),
        name="Test Player 2"
    )
    
    # Check that local_player_cube is set
    assert model.local_player_cube is not None, \
        "ClientModel.create_local_player() should set model.local_player_cube"
    print("  ✓ ClientModel.create_local_player() sets model.local_player_cube")
    
    # Check that it's the same as local_player
    assert model.local_player_cube is model.local_player, \
        "local_player_cube should be the same as local_player"
    print("  ✓ local_player_cube is the same as local_player")
    
    print("\n✅ PASS: ClientModel correctly sets local_player_cube")


def test_camera_window_can_access_local_player_cube():
    """Test that camera window can access model.local_player_cube."""
    print("\n🧪 Test: Camera window can access model.local_player_cube")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube
    
    # Create a model with local player
    model = EnhancedClientModel()
    player = model.create_local_player(
        player_id="test_player_789",
        position=(20, 30, 40),
        rotation=(90, 0),
        name="Test Player 3"
    )
    
    # Create a camera cube with the model
    camera_cube = Cube(
        cube_id="camera_test_1",
        position=(25, 35, 45),
        cube_type="camera",
        model=model
    )
    
    # Check that the camera window has access to the model
    assert camera_cube.window is not None, \
        "Camera cube should have a window"
    print("  ✓ Camera cube has a window")
    
    # Check that the window has access to the model
    assert camera_cube.window.model is model, \
        "Camera window should have access to the model"
    print("  ✓ Camera window has access to the model")
    
    # Check that the model has the local player cube
    assert camera_cube.window.model.local_player_cube is not None, \
        "Model accessed from camera window should have local_player_cube"
    print("  ✓ Model accessed from camera window has local_player_cube")
    
    # Check that it's the same player we created
    assert camera_cube.window.model.local_player_cube is player, \
        "local_player_cube should be the player we created"
    print("  ✓ local_player_cube is the player we created")
    
    print("\n✅ PASS: Camera window can access model.local_player_cube")


if __name__ == '__main__':
    print("=" * 70)
    print("LOCAL PLAYER CUBE MODEL TEST SUITE")
    print("=" * 70)
    
    try:
        test_enhanced_client_model_has_local_player_cube()
        test_create_local_player_sets_local_player_cube()
        test_client_model_create_local_player()
        test_camera_window_can_access_local_player_cube()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Local player cube is accessible from cameras!")
        print("=" * 70)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
