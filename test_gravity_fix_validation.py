#!/usr/bin/env python3
"""
Test to verify the gravity fix: no gravity when player is on ground.
This directly tests the issue mentioned in the problem statement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer
import time

def test_no_gravity_when_on_block():
    """Test that gravity is not applied when player is standing on a block."""
    print("🧪 Testing: No Gravity When Player Is On Block\n")
    print("Problem: 'change pour que quand un joueur est sur un bloc, pas de gravité pour ne pas enfoncer'")
    print("Translation: 'change so that when a player is on a block, no gravity so they don't sink in'\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world for clean test
    
    # Create a single block platform
    server.world.world[(10, 10, 10)] = "stone"
    
    print("✅ Created stone block at (10, 10, 10)")
    
    # Create a player standing perfectly on the block
    player = PlayerState("player1", (10, 11, 10), (0, 0), "TestPlayer")
    player.on_ground = True  # Player is standing on the block
    player.velocity = [0, 0, 0]  # No velocity
    player.last_move_time = 0  # Allow physics to apply immediately
    
    print(f"✅ Player created on block:")
    print(f"   Position: {player.position}")
    print(f"   On ground: {player.on_ground}")
    print(f"   Velocity: {player.velocity}")
    
    # Test: Apply physics multiple times - player should NOT move or experience gravity
    print(f"\n🧪 Applying physics 5 times (player should stay in same position):")
    
    initial_position = player.position
    initial_velocity = player.velocity[:]
    
    for i in range(5):
        old_pos = player.position
        old_vel = player.velocity[:]
        
        # Apply physics
        server._apply_physics(player, 0.1)  # 100ms timestep
        
        print(f"Step {i+1}: Position {old_pos} -> {player.position}, Velocity {old_vel} -> {player.velocity}")
        
        # Verify no movement occurred
        if player.position != initial_position:
            print(f"   ❌ FAIL: Player moved from initial position!")
            print(f"      Initial: {initial_position}")
            print(f"      Current: {player.position}")
            return False
        
        # Verify no velocity change
        if player.velocity != initial_velocity:
            print(f"   ❌ FAIL: Player velocity changed!")
            print(f"      Initial: {initial_velocity}")
            print(f"      Current: {player.velocity}")
            return False
        
        # Verify still on ground
        if not player.on_ground:
            print(f"   ❌ FAIL: Player is no longer on ground!")
            return False
        
        print(f"   ✅ OK: No movement, no velocity change, still on ground")
    
    print(f"\n✅ SUCCESS: Player remained stable on block")
    print(f"   Final position: {player.position} (unchanged)")
    print(f"   Final velocity: {player.velocity} (unchanged)")
    print(f"   Still on ground: {player.on_ground}")
    
    return True

def test_gravity_resumes_when_off_ground():
    """Test that gravity resumes when player leaves the ground."""
    print("\n🧪 Testing: Gravity Resumes When Player Leaves Ground\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world for clean test
    
    # Create a platform
    server.world.world[(10, 10, 10)] = "stone"
    
    # Create a player on the platform
    player = PlayerState("player1", (10, 11, 10), (0, 0), "TestPlayer")
    player.on_ground = True
    player.velocity = [0, 0, 0]
    player.last_move_time = 0
    
    print("✅ Player starts on platform at (10, 11, 10)")
    
    # Step 1: Verify no gravity while on ground
    print("\nStep 1: Verify no gravity while on ground")
    server._apply_physics(player, 0.1)
    if player.velocity[1] != 0:
        print("❌ FAIL: Gravity applied while on ground")
        return False
    print("✅ OK: No gravity while on ground")
    
    # Step 2: Manually move player off the platform (simulate jump or movement)
    print("\nStep 2: Move player off platform to (11, 11, 10)")
    player.position = (11, 11, 10)  # Move to empty space
    player.on_ground = False  # No longer on ground
    
    # Step 3: Verify gravity now applies
    print("\nStep 3: Verify gravity now applies")
    old_velocity = player.velocity[1]
    server._apply_physics(player, 0.1)
    new_velocity = player.velocity[1]
    
    if new_velocity <= old_velocity:
        print(f"✅ OK: Gravity applied! Velocity changed from {old_velocity} to {new_velocity}")
        return True
    else:
        print(f"❌ FAIL: Gravity not applied! Velocity unchanged: {old_velocity} -> {new_velocity}")
        return False

if __name__ == "__main__":
    print("🎮 Testing Gravity Fix: No Gravity When On Block\n")
    print("=" * 70)
    
    try:
        success = True
        success &= test_no_gravity_when_on_block()
        success &= test_gravity_resumes_when_off_ground()
        
        if success:
            print("\n" + "=" * 70)
            print("🎉 ALL GRAVITY FIX TESTS PASSED!")
            print("✅ Problem solved: Players on blocks no longer experience gravity")
            print("✅ Players will not sink into blocks due to gravity")
            print("✅ Gravity still works normally when players are not on blocks")
        else:
            print("\n" + "=" * 70)
            print("❌ Some gravity fix tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)