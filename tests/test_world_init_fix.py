#!/usr/bin/env python3
"""
Test to verify the fix for 'EnhancedClientModel' object has no attribute 'create_local_player' error.

This test validates that:
1. EnhancedClientModel has the create_local_player method
2. EnhancedClientModel has local_player and cubes attributes
3. The method can be called successfully in the WORLD_INIT message handler context
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_enhanced_client_model_has_create_local_player():
    """Test that EnhancedClientModel has create_local_player method."""
    print("\n🧪 Test: EnhancedClientModel has create_local_player method")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Check method exists
    assert hasattr(model, 'create_local_player'), \
        "EnhancedClientModel should have create_local_player method"
    print("  ✓ create_local_player method exists")
    
    # Check it's callable
    assert callable(model.create_local_player), \
        "create_local_player should be callable"
    print("  ✓ create_local_player is callable")
    
    print("✅ PASS: EnhancedClientModel has create_local_player method")


def test_enhanced_client_model_has_player_attributes():
    """Test that EnhancedClientModel has local_player and cubes attributes."""
    print("\n🧪 Test: EnhancedClientModel has player attributes")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Check local_player attribute
    assert hasattr(model, 'local_player'), \
        "EnhancedClientModel should have local_player attribute"
    print("  ✓ local_player attribute exists")
    
    # Check cubes attribute
    assert hasattr(model, 'cubes'), \
        "EnhancedClientModel should have cubes attribute"
    print("  ✓ cubes attribute exists")
    
    # Verify initial values
    assert model.local_player is None, \
        "local_player should be None initially"
    print("  ✓ local_player is None initially")
    
    assert isinstance(model.cubes, dict), \
        "cubes should be a dictionary"
    print("  ✓ cubes is a dictionary")
    
    assert len(model.cubes) == 0, \
        "cubes should be empty initially"
    print("  ✓ cubes is empty initially")
    
    print("✅ PASS: EnhancedClientModel has correct player attributes")


def test_create_local_player_functionality():
    """Test that create_local_player works correctly."""
    print("\n🧪 Test: create_local_player functionality")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Create a local player
    player_id = "test_player_123"
    position = (10.0, 20.0, 30.0)
    rotation = (45.0, -15.0)
    name = "Test Player"
    
    player = model.create_local_player(player_id, position, rotation, name)
    
    # Verify player was created
    assert player is not None, \
        "create_local_player should return a player object"
    print("  ✓ Player object created")
    
    # Verify player attributes
    assert player.id == player_id, \
        f"Player ID should be {player_id}"
    print(f"  ✓ Player ID is correct: {player_id}")
    
    assert player.position == position, \
        f"Player position should be {position}"
    print(f"  ✓ Player position is correct: {position}")
    
    assert player.rotation == rotation, \
        f"Player rotation should be {rotation}"
    print(f"  ✓ Player rotation is correct: {rotation}")
    
    # Verify is_local flag
    assert hasattr(player, 'is_local') and player.is_local, \
        "Player should have is_local=True"
    print("  ✓ Player is_local flag is True")
    
    # Verify player size
    assert hasattr(player, 'size') and player.size == 0.5, \
        "Player should have size=0.5"
    print("  ✓ Player size is 0.5")
    
    # Verify player color was assigned
    assert hasattr(player, 'color') and player.color is not None, \
        "Player should have a color assigned"
    print("  ✓ Player color was assigned")
    
    # Verify player was added to model
    assert model.local_player is player, \
        "model.local_player should be set to the created player"
    print("  ✓ model.local_player is set")
    
    assert player_id in model.cubes, \
        "Player should be added to model.cubes"
    print("  ✓ Player added to model.cubes")
    
    assert model.cubes[player_id] is player, \
        "model.cubes should contain the player"
    print("  ✓ model.cubes contains the player")
    
    print("✅ PASS: create_local_player functionality works correctly")


def test_world_init_context_simulation():
    """Simulate the WORLD_INIT message handler context."""
    print("\n🧪 Test: WORLD_INIT context simulation")
    
    from minecraft_client_fr import EnhancedClientModel
    from client_config import config
    
    # Simulate the WORLD_INIT message handler code
    model = EnhancedClientModel()
    
    # Simulate what happens in _handle_server_message for WORLD_INIT
    player_id = "server_assigned_player_id_456"
    position = (30.0, 50.0, 80.0)  # Typical spawn position
    rotation = (0.0, 0.0)
    player_name = config.get("player", "name", "Joueur")
    
    # This is the line that was failing before the fix (line 289 in minecraft_client_fr.py)
    try:
        local_player_cube = model.create_local_player(
            player_id, position, rotation, player_name
        )
        print("  ✓ create_local_player call succeeded in WORLD_INIT context")
    except AttributeError as e:
        if "'EnhancedClientModel' object has no attribute 'create_local_player'" in str(e):
            raise AssertionError("WORLD_INIT context failed: EnhancedClientModel still missing create_local_player")
        raise
    
    # Verify the player was created correctly
    assert local_player_cube is not None, \
        "local_player_cube should not be None"
    print("  ✓ local_player_cube is not None")
    
    assert local_player_cube.id == player_id, \
        "Player ID should match server-assigned ID"
    print(f"  ✓ Player ID matches: {player_id}")
    
    assert model.local_player is local_player_cube, \
        "model.local_player should be set"
    print("  ✓ model.local_player is set correctly")
    
    print("✅ PASS: WORLD_INIT context simulation successful")


def test_helper_methods_exist():
    """Test that all required helper methods exist."""
    print("\n🧪 Test: Helper methods exist")
    
    from minecraft_client_fr import EnhancedClientModel
    
    model = EnhancedClientModel()
    
    # Check add_cube method
    assert hasattr(model, 'add_cube') and callable(model.add_cube), \
        "EnhancedClientModel should have add_cube method"
    print("  ✓ add_cube method exists")
    
    # Check remove_cube method
    assert hasattr(model, 'remove_cube') and callable(model.remove_cube), \
        "EnhancedClientModel should have remove_cube method"
    print("  ✓ remove_cube method exists")
    
    # Check get_all_cubes method
    assert hasattr(model, 'get_all_cubes') and callable(model.get_all_cubes), \
        "EnhancedClientModel should have get_all_cubes method"
    print("  ✓ get_all_cubes method exists")
    
    # Check _generate_player_color method
    assert hasattr(model, '_generate_player_color') and callable(model._generate_player_color), \
        "EnhancedClientModel should have _generate_player_color method"
    print("  ✓ _generate_player_color method exists")
    
    print("✅ PASS: All helper methods exist")


def test_camera_cube_integration():
    """Test that camera cubes can use the same model infrastructure."""
    print("\n🧪 Test: Camera cube integration with model")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube
    
    model = EnhancedClientModel()
    
    # Create a camera cube
    camera_id = "camera_block_123"
    camera_position = (15.0, 25.0, 35.0)
    camera_rotation = (90.0, 0.0)
    owner_id = "player_owner_789"
    
    # Camera cubes should be able to access the model
    camera_cube = Cube(
        cube_id=camera_id,
        position=camera_position,
        rotation=camera_rotation,
        cube_type="camera",
        owner=owner_id,
        model=model  # Pass the model to the camera cube
    )
    
    assert camera_cube is not None, \
        "Camera cube should be created successfully"
    print("  ✓ Camera cube created with model reference")
    
    # Verify camera cube has access to model
    if hasattr(camera_cube, 'window') and camera_cube.window:
        assert camera_cube.window.model is model, \
            "Camera cube window should have reference to model"
        print("  ✓ Camera cube window has model reference")
    else:
        print("  ℹ️  Camera cube window not created (expected in headless mode)")
    
    # Verify camera can access other_players through model
    assert hasattr(model, 'other_players'), \
        "Model should have other_players attribute"
    print("  ✓ Model has other_players for camera to render")
    
    # Verify camera can access local_player_cube through model
    assert hasattr(model, 'local_player'), \
        "Model should have local_player attribute for camera to render"
    print("  ✓ Model has local_player for camera to render")
    
    print("✅ PASS: Camera cube integration works correctly")


if __name__ == "__main__":
    print("=" * 70)
    print("WORLD_INIT FIX VERIFICATION TEST SUITE")
    print("=" * 70)
    
    try:
        test_enhanced_client_model_has_create_local_player()
        test_enhanced_client_model_has_player_attributes()
        test_create_local_player_functionality()
        test_world_init_context_simulation()
        test_helper_methods_exist()
        test_camera_cube_integration()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - WORLD_INIT error is fixed!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
