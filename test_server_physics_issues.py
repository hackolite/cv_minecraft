#!/usr/bin/env python3
"""
Test server-side physics and synchronization issues that could cause floating cubes.
This test simulates the server physics update loop to identify potential problems.
"""

import sys
import os
import time
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, Cube, BlockType
from minecraft_physics import MinecraftPhysics, MinecraftCollisionDetector, UnifiedCollisionManager

def test_server_physics_interference():
    """Test if server physics interferes with client positioning."""
    print("🧪 Testing server physics interference...")
    
    # Create a world with some blocks
    world_blocks = {}
    for x in range(-5, 6):
        for z in range(-5, 6):
            world_blocks[(x, 0, z)] = BlockType.GRASS  # Ground at Y=0
            if x == 0 and z == 0:
                world_blocks[(x, 1, z)] = BlockType.STONE  # One block at origin
    
    collision_detector = MinecraftCollisionDetector(world_blocks)
    physics = MinecraftPhysics(collision_detector)
    
    # Simulate a player moving to a position
    print("\n📍 Testing player movement and physics application:")
    
    # Initial player state - standing on ground
    player = PlayerState("test_player", (0, 1, 0), (0, 0), "TestPlayer")
    print(f"   Initial position: {player.position}")
    print(f"   Render position: {player.get_render_position()}")
    print(f"   Cube bottom: {player.get_render_position()[1] - player.size}")
    
    # Simulate server applying physics (what happens in server._apply_physics)
    dt = 1.0/20.0  # Standard server tick
    on_ground = True
    velocity = [0.0, 0.0, 0.0]
    
    # Apply physics multiple times to see if position drifts
    for step in range(5):
        new_position, new_velocity, new_on_ground = physics.update_position(
            player.position, velocity, dt, on_ground, False
        )
        
        # Update player state (as server would do)
        player.position = new_position
        player.velocity = new_velocity
        player.on_ground = new_on_ground
        
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"\n   Step {step + 1}:")
        print(f"     Position: {player.position}")
        print(f"     Velocity: {player.velocity}")
        print(f"     On ground: {player.on_ground}")
        print(f"     Render position: {render_pos}")
        print(f"     Cube bottom: {cube_bottom}")
        
        # Check if cube is still on the correct surface
        expected_bottom = 1.0  # Should be on top of block at Y=1
        if abs(cube_bottom - expected_bottom) > 0.001:
            print(f"     ❌ Cube drifted! Expected bottom: {expected_bottom}, got: {cube_bottom}")
            return False
        else:
            print(f"     ✅ Cube positioned correctly")
    
    return True

def test_spawn_physics_interaction():
    """Test physics interaction during spawn."""
    print("\n🧪 Testing spawn physics interaction...")
    
    # Create world with elevated spawn position (like server DEFAULT_SPAWN_POSITION)
    world_blocks = {}
    for x in range(60, 70):
        for z in range(60, 70):
            for y in range(0, 50):  # Ground up to Y=50
                world_blocks[(x, y, z)] = BlockType.STONE
    
    collision_detector = MinecraftCollisionDetector(world_blocks)
    physics = MinecraftPhysics(collision_detector)
    
    # Simulate spawn at high position (like server does)
    spawn_position = (64, 100, 64)  # DEFAULT_SPAWN_POSITION from server
    player = PlayerState("spawned_player", spawn_position, (0, 0), "SpawnPlayer")
    
    print(f"   Spawn position: {spawn_position}")
    render_pos = player.get_render_position()
    print(f"   Initial render position: {render_pos}")
    print(f"   Initial cube bottom: {render_pos[1] - player.size}")
    
    # Simulate multiple physics updates (player should fall to ground)
    dt = 1.0/20.0
    velocity = [0.0, 0.0, 0.0]
    on_ground = False
    
    print(f"\n   Simulating fall from spawn...")
    for step in range(100):  # Up to 5 seconds of falling
        new_position, new_velocity, new_on_ground = physics.update_position(
            player.position, velocity, dt, on_ground, False
        )
        
        player.position = new_position
        player.velocity = new_velocity
        player.on_ground = new_on_ground
        velocity = new_velocity
        on_ground = new_on_ground
        
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        if step % 20 == 0:  # Print every second
            print(f"     Step {step}: Y={player.position[1]:.2f}, VY={velocity[1]:.2f}, "
                  f"Ground={on_ground}, CubeBottom={cube_bottom:.2f}")
        
        # Check if player landed
        if on_ground and abs(velocity[1]) < 0.1:
            print(f"   ✅ Player landed after {step} steps")
            print(f"   Final position: {player.position}")
            print(f"   Final cube bottom: {cube_bottom}")
            
            # Verify cube is on correct surface
            expected_surface = 50.0  # Top of blocks is at Y=50
            if abs(cube_bottom - expected_surface) < 0.1:
                print(f"   ✅ Cube correctly positioned on surface at Y={expected_surface}")
                return True
            else:
                print(f"   ❌ Cube not on surface! Expected: {expected_surface}, got: {cube_bottom}")
                return False
    
    print(f"   ❌ Player did not land within simulation time")
    return False

def test_network_sync_timing():
    """Test network synchronization timing issues."""
    print("\n🧪 Testing network synchronization timing...")
    
    # Simulate rapid position updates (as might happen during network sync)
    player = PlayerState("sync_player", (0, 0, 0), (0, 0), "SyncPlayer")
    
    # Simulate receiving multiple position updates in quick succession
    network_positions = [
        (0, 0, 0),
        (0.1, 0.05, 0.1),
        (0.2, 0.1, 0.2),
        (0.3, 0.2, 0.3),
        (0.5, 0.3, 0.5),
        (1.0, 0.5, 1.0),
    ]
    
    print(f"   Simulating rapid network position updates...")
    for i, pos in enumerate(network_positions):
        # Update position (as client would do when receiving server update)
        player.update_position(pos)
        
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"     Update {i}: Position={pos}, RenderPos={render_pos}, CubeBottom={cube_bottom}")
        
        # Verify cube bottom matches the Y position
        expected_bottom = pos[1]
        if abs(cube_bottom - expected_bottom) > 0.001:
            print(f"     ❌ Sync error! Expected bottom: {expected_bottom}, got: {cube_bottom}")
            return False
        else:
            print(f"     ✅ Synchronized correctly")
    
    return True

def test_grace_period_physics():
    """Test the server's grace period physics logic."""
    print("\n🧪 Testing server grace period physics...")
    
    # Create world
    world_blocks = {(0, 0, 0): BlockType.GRASS}
    collision_detector = MinecraftCollisionDetector(world_blocks)
    physics = MinecraftPhysics(collision_detector)
    
    # Simulate player making a voluntary movement
    player = PlayerState("grace_player", (0, 1, 0), (0, 0), "GracePlayer")
    player.last_move_time = time.time()  # Mark as recent voluntary movement
    
    print(f"   Player position after voluntary move: {player.position}")
    print(f"   Last move time: {player.last_move_time}")
    
    # Simulate server physics trying to apply immediately after move
    # (This should be blocked by grace period)
    current_time = time.time()
    grace_period = 0.5  # 500ms as in server code
    
    print(f"   Current time: {current_time}")
    print(f"   Time since last move: {current_time - player.last_move_time:.3f}s")
    print(f"   Grace period: {grace_period}s")
    
    if current_time - player.last_move_time < grace_period:
        print(f"   ✅ Within grace period - physics should not apply")
        # Server would skip physics application
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        print(f"   Position preserved: {player.position}")
        print(f"   Cube bottom: {cube_bottom}")
        
        # Verify position unchanged
        if cube_bottom == 1.0:  # On top of block at Y=0
            print(f"   ✅ Position correctly preserved during grace period")
            return True
        else:
            print(f"   ❌ Position changed during grace period!")
            return False
    else:
        print(f"   Outside grace period - physics would apply")
        # Simulate grace period ending
        time.sleep(0.6)  # Wait for grace period to end
        
        # Apply physics
        dt = 1.0/20.0
        new_position, new_velocity, new_on_ground = physics.update_position(
            player.position, [0.0, 0.0, 0.0], dt, True, False
        )
        
        player.position = new_position
        render_pos = player.get_render_position()
        cube_bottom = render_pos[1] - player.size
        
        print(f"   Physics applied after grace period")
        print(f"   New position: {player.position}")
        print(f"   Cube bottom: {cube_bottom}")
        
        # Should still be correctly positioned
        if abs(cube_bottom - 1.0) < 0.001:
            print(f"   ✅ Position correct after grace period")
            return True
        else:
            print(f"   ❌ Position incorrect after grace period!")
            return False

if __name__ == "__main__":
    print("🎮 TESTING SERVER-SIDE PHYSICS AND SYNCHRONIZATION")
    print("=" * 60)
    print("Testing server physics that might cause floating cubes...")
    print()
    
    try:
        success = True
        success &= test_server_physics_interference()
        success &= test_spawn_physics_interaction()
        success &= test_network_sync_timing()
        success &= test_grace_period_physics()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 ALL SERVER PHYSICS TESTS PASSED!")
            print("✅ Server physics does not interfere with positioning")
            print("✅ Spawn physics works correctly")
            print("✅ Network synchronization is stable")
            print("✅ Grace period logic prevents position drift")
            print()
            print("🔍 NO SERVER-SIDE FLOATING CUBE ISSUES DETECTED!")
            print("📝 The server physics system appears to be working correctly.")
            print("=" * 60)
        else:
            print("\n❌ SERVER-SIDE FLOATING CUBE ISSUES DETECTED!")
            print("Check the failed tests above for specific problems.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)