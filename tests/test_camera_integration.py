#!/usr/bin/env python3
"""
Integration test to verify that camera cubes can see blocks and users.

This test simulates a complete scenario where:
1. A user joins the world
2. Other users are present
3. A camera cube is created
4. The camera cube can see both blocks and users through the shared model
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_camera_sees_blocks():
    """Test that a camera cube can see blocks in the world."""
    print("\n🧪 Test: Camera cube can see blocks")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube, BlockType
    
    # Create a model and add some blocks
    model = EnhancedClientModel()
    
    # Add blocks to the world
    model.add_block((0, 0, 0), BlockType.GRASS, immediate=False)
    model.add_block((1, 0, 0), BlockType.STONE, immediate=False)
    model.add_block((0, 1, 0), BlockType.BRICK, immediate=False)
    
    print(f"  ✓ Added 3 blocks to the world")
    
    # Create a camera cube with the model
    camera_cube = Cube(
        cube_id="test_camera_1",
        position=(5.0, 5.0, 5.0),
        rotation=(0.0, 0.0),
        cube_type="camera",
        owner="player_123",
        model=model
    )
    
    print(f"  ✓ Created camera cube with model reference")
    
    # Verify the camera cube has access to the model
    assert camera_cube.window is not None, \
        "Camera cube should have a window"
    assert camera_cube.window.model is model, \
        "Camera window should have reference to the model"
    print(f"  ✓ Camera window has model reference")
    
    # Verify the camera can access world blocks through the model
    world_blocks = camera_cube.window.model.world
    assert len(world_blocks) == 3, \
        f"Camera should see 3 blocks, found {len(world_blocks)}"
    print(f"  ✓ Camera can see {len(world_blocks)} blocks")
    
    # Verify specific blocks
    assert (0, 0, 0) in world_blocks, \
        "Camera should see block at (0, 0, 0)"
    assert world_blocks[(0, 0, 0)] == BlockType.GRASS, \
        "Block at (0, 0, 0) should be GRASS"
    print(f"  ✓ Camera can identify block types correctly")
    
    print("✅ PASS: Camera cube can see blocks")


def test_camera_sees_other_players():
    """Test that a camera cube can see other players."""
    print("\n🧪 Test: Camera cube can see other players")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube, PlayerState
    
    # Create a model
    model = EnhancedClientModel()
    
    # Create local player
    local_player = model.create_local_player(
        "local_player_123",
        (10.0, 20.0, 30.0),
        (0.0, 0.0),
        "Local Player"
    )
    print(f"  ✓ Created local player: {local_player.id}")
    
    # Add other players
    other_player_1 = PlayerState("remote_player_1", (15.0, 20.0, 35.0), (45.0, 0.0), "Player 1")
    other_player_2 = PlayerState("remote_player_2", (5.0, 20.0, 25.0), (-45.0, 0.0), "Player 2")
    
    model.other_players["remote_player_1"] = other_player_1
    model.other_players["remote_player_2"] = other_player_2
    
    print(f"  ✓ Added 2 other players to the model")
    
    # Create a camera cube
    camera_cube = Cube(
        cube_id="test_camera_2",
        position=(10.0, 25.0, 30.0),
        rotation=(0.0, -30.0),
        cube_type="camera",
        owner="local_player_123",
        model=model
    )
    
    print(f"  ✓ Created camera cube owned by local player")
    
    # Verify the camera can access players through the model
    camera_model = camera_cube.window.model
    
    # Check local player
    assert camera_model.local_player is not None, \
        "Camera should see the local player"
    assert camera_model.local_player.id == "local_player_123", \
        "Camera should see the correct local player"
    print(f"  ✓ Camera can see local player: {camera_model.local_player.id}")
    
    # Check other players
    assert len(camera_model.other_players) == 2, \
        f"Camera should see 2 other players, found {len(camera_model.other_players)}"
    print(f"  ✓ Camera can see {len(camera_model.other_players)} other players")
    
    assert "remote_player_1" in camera_model.other_players, \
        "Camera should see remote_player_1"
    assert "remote_player_2" in camera_model.other_players, \
        "Camera should see remote_player_2"
    print(f"  ✓ Camera can identify all remote players")
    
    # Check player positions
    player1 = camera_model.other_players["remote_player_1"]
    assert player1.position == (15.0, 20.0, 35.0), \
        "Camera should see correct position for player 1"
    print(f"  ✓ Camera sees correct player positions")
    
    print("✅ PASS: Camera cube can see other players")


def test_camera_sees_owner():
    """Test that a camera cube can see its owner (the original user)."""
    print("\n🧪 Test: Camera cube can see its owner")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube
    
    # Create a model
    model = EnhancedClientModel()
    
    # Create local player (the owner)
    owner_player = model.create_local_player(
        "owner_123",
        (10.0, 20.0, 30.0),
        (90.0, 0.0),
        "Camera Owner"
    )
    print(f"  ✓ Created owner player: {owner_player.id}")
    
    # Create a camera cube owned by this player
    camera_cube = Cube(
        cube_id="camera_owned_by_owner",
        position=(10.0, 25.0, 30.0),  # Positioned above the owner
        rotation=(0.0, -90.0),  # Looking down
        cube_type="camera",
        owner="owner_123",
        model=model
    )
    
    print(f"  ✓ Created camera cube at position {camera_cube.position}")
    
    # Verify the camera can see its owner through local_player
    camera_model = camera_cube.window.model
    
    assert camera_model.local_player is not None, \
        "Camera should have access to local_player (the owner)"
    print(f"  ✓ Camera has access to local_player")
    
    assert camera_model.local_player.id == "owner_123", \
        "Camera should see the owner as local_player"
    print(f"  ✓ Camera sees owner: {camera_model.local_player.id}")
    
    assert camera_model.local_player.is_local == True, \
        "Owner should be marked as local"
    print(f"  ✓ Owner is marked as local player")
    
    # Verify position
    assert camera_model.local_player.position == (10.0, 20.0, 30.0), \
        "Camera should see correct owner position"
    print(f"  ✓ Camera sees correct owner position: {camera_model.local_player.position}")
    
    print("✅ PASS: Camera cube can see its owner")


def test_camera_updates_with_model():
    """Test that camera sees updates when model is updated."""
    print("\n🧪 Test: Camera sees real-time updates")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube, BlockType, PlayerState
    
    # Create a model
    model = EnhancedClientModel()
    
    # Create a camera cube
    camera_cube = Cube(
        cube_id="test_camera_updates",
        position=(0.0, 10.0, 0.0),
        rotation=(0.0, 0.0),
        cube_type="camera",
        owner="player_xyz",
        model=model
    )
    
    camera_model = camera_cube.window.model
    
    # Initially, no blocks
    assert len(camera_model.world) == 0, \
        "Initially should have no blocks"
    print(f"  ✓ Initial state: 0 blocks")
    
    # Add a block to the model
    model.add_block((5, 0, 5), BlockType.STONE, immediate=False)
    
    # Camera should see the new block
    assert len(camera_model.world) == 1, \
        "Camera should see new block"
    assert (5, 0, 5) in camera_model.world, \
        "Camera should see block at (5, 0, 5)"
    print(f"  ✓ After block added: camera sees 1 block")
    
    # Add a player
    model.other_players["new_player"] = PlayerState(
        "new_player", (20.0, 0.0, 20.0), (0.0, 0.0), "New Player"
    )
    
    # Camera should see the new player
    assert "new_player" in camera_model.other_players, \
        "Camera should see new player"
    print(f"  ✓ After player added: camera sees the player")
    
    # Remove the block
    model.remove_block((5, 0, 5), immediate=False)
    
    # Camera should not see the removed block
    assert (5, 0, 5) not in camera_model.world, \
        "Camera should not see removed block"
    print(f"  ✓ After block removed: camera doesn't see it")
    
    print("✅ PASS: Camera sees real-time updates")


def test_multiple_cameras_share_model():
    """Test that multiple camera cubes share the same model data."""
    print("\n🧪 Test: Multiple cameras share model")
    
    from minecraft_client_fr import EnhancedClientModel
    from protocol import Cube, BlockType
    
    # Create a model
    model = EnhancedClientModel()
    
    # Add some blocks
    model.add_block((0, 0, 0), BlockType.GRASS, immediate=False)
    model.add_block((1, 0, 0), BlockType.STONE, immediate=False)
    
    # Create local player
    model.create_local_player("player_multi", (10.0, 10.0, 10.0), (0.0, 0.0), "Multi Player")
    
    # Create multiple camera cubes
    camera1 = Cube(
        cube_id="camera_1",
        position=(5.0, 5.0, 5.0),
        cube_type="camera",
        owner="player_multi",
        model=model
    )
    
    camera2 = Cube(
        cube_id="camera_2",
        position=(15.0, 5.0, 5.0),
        cube_type="camera",
        owner="player_multi",
        model=model
    )
    
    camera3 = Cube(
        cube_id="camera_3",
        position=(5.0, 15.0, 5.0),
        cube_type="camera",
        owner="player_multi",
        model=model
    )
    
    print(f"  ✓ Created 3 camera cubes")
    
    # All cameras should see the same data
    camera1_blocks = len(camera1.window.model.world)
    camera2_blocks = len(camera2.window.model.world)
    camera3_blocks = len(camera3.window.model.world)
    
    assert camera1_blocks == camera2_blocks == camera3_blocks == 2, \
        f"All cameras should see 2 blocks, got {camera1_blocks}, {camera2_blocks}, {camera3_blocks}"
    print(f"  ✓ All 3 cameras see the same {camera1_blocks} blocks")
    
    # All cameras should see the same local player
    assert camera1.window.model.local_player.id == "player_multi", \
        "Camera 1 should see the player"
    assert camera2.window.model.local_player.id == "player_multi", \
        "Camera 2 should see the player"
    assert camera3.window.model.local_player.id == "player_multi", \
        "Camera 3 should see the player"
    print(f"  ✓ All 3 cameras see the same local player")
    
    # Verify they're all referencing the same model object
    assert camera1.window.model is camera2.window.model is camera3.window.model is model, \
        "All cameras should reference the same model object"
    print(f"  ✓ All 3 cameras reference the same model instance")
    
    print("✅ PASS: Multiple cameras share model correctly")


if __name__ == "__main__":
    print("=" * 70)
    print("CAMERA CUBE INTEGRATION TEST SUITE")
    print("Testing that camera cubes can see blocks and users")
    print("=" * 70)
    
    try:
        test_camera_sees_blocks()
        test_camera_sees_other_players()
        test_camera_sees_owner()
        test_camera_updates_with_model()
        test_multiple_cameras_share_model()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)
        print("\nSummary:")
        print("  • Camera cubes can see all blocks in the world")
        print("  • Camera cubes can see all other players")
        print("  • Camera cubes can see their owner (original user)")
        print("  • Camera cubes see real-time updates to the model")
        print("  • Multiple cameras share the same model data")
        print("\nConclusion:")
        print("  ✅ Les cubes caméra se comportent exactement comme un utilisateur")
        print("  ✅ Ils voient les autres blocs et les autres utilisateurs")
        print("  ✅ Ils sont synchronisés en temps réel via le modèle partagé")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
