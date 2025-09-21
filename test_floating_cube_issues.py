#!/usr/bin/env python3
"""
Comprehensive test to identify potential floating cube issues.
This test examines various scenarios where cubes might appear to float.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, Cube
from client import ClientModel
from minecraft_physics import MinecraftPhysics, MinecraftCollisionDetector, UnifiedCollisionManager, PLAYER_HEIGHT, PLAYER_WIDTH

def test_render_position_consistency():
    """Test that render positions are consistent across different scenarios."""
    print("🧪 Testing render position consistency...")
    
    test_cases = [
        ("Ground level", (0, 0, 0)),
        ("Single block height", (0, 1, 0)),
        ("Multiple blocks", (0, 3, 0)),
        ("Floating position", (0, 2.5, 0)),
        ("Negative Y", (0, -1, 0)),
    ]
    
    for name, position in test_cases:
        player = PlayerState(f"test_{name.lower().replace(' ', '_')}", position, (0, 0))
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        cube_top = render_pos[1] + player.size
        
        print(f"\n📍 {name}:")
        print(f"   Player position: {position}")
        print(f"   Player size: {player.size}")
        print(f"   Render position: {render_pos}")
        print(f"   Cube bottom Y: {cube_bottom}")
        print(f"   Cube top Y: {cube_top}")
        
        # Verify cube bottom matches player Y position
        expected_bottom = position[1]
        if abs(cube_bottom - expected_bottom) < 0.001:
            print(f"   ✅ Cube sits correctly at Y={expected_bottom}")
        else:
            print(f"   ❌ Cube floating! Expected bottom: {expected_bottom}, got: {cube_bottom}")
            return False
    
    return True

def test_physics_position_interpretation():
    """Test how physics system interprets player positions."""
    print("\n🧪 Testing physics position interpretation...")
    
    # Create a simple world with ground blocks
    world_blocks = {}
    for x in range(-2, 3):
        for z in range(-2, 3):
            world_blocks[(x, 0, z)] = "grass"  # Ground at Y=0
            world_blocks[(x, 1, z)] = "stone"  # Blocks at Y=1
    
    collision_detector = MinecraftCollisionDetector(world_blocks)
    physics = MinecraftPhysics(collision_detector)
    
    test_cases = [
        ("Standing on ground", (0, 1, 0), "Should be on top of Y=0 block"),
        ("Standing on block", (0, 2, 0), "Should be on top of Y=1 block"),
        ("Floating above", (0, 3, 0), "Should fall due to gravity"),
    ]
    
    for name, position, description in test_cases:
        print(f"\n📍 {name} - {description}")
        print(f"   Initial position: {position}")
        
        # Check collision at this position
        has_collision = collision_detector.manager.check_block_collision(position)
        print(f"   Collision detected: {has_collision}")
        
        # Simulate one physics step
        velocity = (0, 0, 0)  # No initial velocity
        dt = 1.0/20.0  # Standard tick rate
        on_ground = not has_collision  # Assume on ground if no collision
        
        new_pos, new_vel, new_on_ground = physics.update_position(
            position, velocity, dt, on_ground, False
        )
        
        print(f"   New position: {new_pos}")
        print(f"   New velocity: {new_vel}")
        print(f"   On ground: {new_on_ground}")
        
        # For physics interpretation, player Y should be feet position
        player_feet_y = new_pos[1]
        player_head_y = new_pos[1] + PLAYER_HEIGHT
        
        print(f"   Player feet Y: {player_feet_y}")
        print(f"   Player head Y: {player_head_y}")
        
        # Create a player state and check render position
        player = PlayerState("physics_test", new_pos, (0, 0))
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"   Render position: {render_pos}")
        print(f"   Cube bottom Y: {cube_bottom}")
        
        # Verify cube bottom matches physics feet position
        if abs(cube_bottom - player_feet_y) < 0.001:
            print(f"   ✅ Physics and render positions consistent")
        else:
            print(f"   ❌ Inconsistency! Physics feet: {player_feet_y}, cube bottom: {cube_bottom}")
            return False
    
    return True

def test_client_server_position_sync():
    """Test client-server position synchronization scenarios."""
    print("\n🧪 Testing client-server position synchronization...")
    
    model = ClientModel()
    
    # Simulate server sending player updates
    server_positions = [
        (0, 0, 0),
        (1, 1, 1),
        (2, 2.5, 2),  # Fractional Y position
        (3, 5, 3),
    ]
    
    for i, pos in enumerate(server_positions):
        player_id = f"player_{i}"
        
        # Simulate receiving update from server
        player = PlayerState(player_id, pos, (0, 0), f"Player{i}")
        model.add_cube(player)
        
        # Check how client renders this
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"\n📍 Player {i}:")
        print(f"   Server position: {pos}")
        print(f"   Render position: {render_pos}")
        print(f"   Cube bottom Y: {cube_bottom}")
        print(f"   Expected bottom: {pos[1]}")
        
        if abs(cube_bottom - pos[1]) < 0.001:
            print(f"   ✅ Client correctly renders server position")
        else:
            print(f"   ❌ Client misinterprets server position!")
            return False
    
    return True

def test_spawn_positioning():
    """Test spawn positioning scenarios."""
    print("\n🧪 Testing spawn positioning scenarios...")
    
    model = ClientModel()
    
    # Test different spawn scenarios
    spawn_cases = [
        ("Ground spawn", (0, 0, 0)),
        ("Elevated spawn", (0, 10, 0)),
        ("Block spawn", (0, 1, 0)),
        ("Fractional spawn", (0, 1.5, 0)),
    ]
    
    for name, spawn_pos in spawn_cases:
        print(f"\n📍 {name}:")
        print(f"   Spawn position: {spawn_pos}")
        
        # Create local player at spawn
        local_player = model.create_local_player(f"local_{name}", spawn_pos, (0, 0))
        render_pos = local_player.get_render_position()
        cube_bottom = render_pos[1] - local_player.size
        
        print(f"   Local player render position: {render_pos}")
        print(f"   Cube bottom Y: {cube_bottom}")
        
        # Verify cube sits on spawn surface
        expected_bottom = spawn_pos[1]
        if abs(cube_bottom - expected_bottom) < 0.001:
            print(f"   ✅ Spawned correctly on surface at Y={expected_bottom}")
        else:
            print(f"   ❌ Floating spawn! Expected: {expected_bottom}, got: {cube_bottom}")
            return False
    
    return True

def test_movement_positioning():
    """Test positioning during movement."""
    print("\n🧪 Testing movement positioning...")
    
    player = PlayerState("moving_player", (0, 0, 0), (0, 0))
    
    # Simulate movement to different positions
    movement_path = [
        (0, 0, 0),
        (1, 0, 1),
        (2, 1, 2),  # Step up
        (3, 1, 3),  # Same level
        (4, 2, 4),  # Another step up
        (5, 1.5, 5), # Fractional position
    ]
    
    for i, new_pos in enumerate(movement_path):
        player.update_position(new_pos)
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"\n📍 Movement step {i}:")
        print(f"   New position: {new_pos}")
        print(f"   Render position: {render_pos}")
        print(f"   Cube bottom Y: {cube_bottom}")
        
        # Verify cube follows player movement correctly
        expected_bottom = new_pos[1]
        if abs(cube_bottom - expected_bottom) < 0.001:
            print(f"   ✅ Moved correctly to Y={expected_bottom}")
        else:
            print(f"   ❌ Movement error! Expected: {expected_bottom}, got: {cube_bottom}")
            return False
    
    return True

if __name__ == "__main__":
    print("🎮 COMPREHENSIVE FLOATING CUBE ISSUE TESTING")
    print("=" * 60)
    print("Testing various scenarios where cubes might appear to float...")
    print()
    
    try:
        success = True
        success &= test_render_position_consistency()
        success &= test_physics_position_interpretation()
        success &= test_client_server_position_sync()
        success &= test_spawn_positioning()
        success &= test_movement_positioning()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 ALL FLOATING CUBE TESTS PASSED!")
            print("✅ Render positions are consistent")
            print("✅ Physics and render systems are aligned")
            print("✅ Client-server synchronization works correctly")
            print("✅ Spawn positioning is correct")
            print("✅ Movement positioning is correct")
            print()
            print("🔍 NO FLOATING CUBE ISSUES DETECTED!")
            print("📝 The cube positioning system appears to be working correctly.")
            print("=" * 60)
        else:
            print("\n❌ FLOATING CUBE ISSUES DETECTED!")
            print("Check the failed tests above for specific problems.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)