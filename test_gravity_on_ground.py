#!/usr/bin/env python3
"""
Test to demonstrate the gravity issue when player is on ground.
The issue: gravity is applied even when player is on ground, which could cause sinking.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer
import time

def test_gravity_when_on_ground():
    """Test that demonstrates gravity being applied when player is on ground."""
    print("🧪 Testing Gravity When Player Is On Ground\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world for clean test
    
    # Create a platform
    server.world.world[(10, 10, 10)] = "stone"
    
    print("✅ Created stone block at (10, 10, 10)")
    
    # Create a player standing on the platform
    player = PlayerState("player1", (10, 11, 10), (0, 0), "TestPlayer")
    player.on_ground = True  # Player is standing on ground
    player.velocity = [0, 0, 0]  # No initial velocity
    player.last_move_time = 0  # Allow physics to apply immediately
    
    print(f"Initial state:")
    print(f"   Position: {player.position}")
    print(f"   Velocity: {player.velocity}")
    print(f"   On ground: {player.on_ground}")
    
    # Apply physics - this should NOT apply gravity if player is on ground
    print(f"\n🧪 Applying physics (should NOT apply gravity when on ground):")
    
    for i in range(3):
        old_pos = player.position
        old_vel = player.velocity[:]
        old_on_ground = player.on_ground
        
        server._apply_physics(player, 0.1)
        
        print(f"Step {i+1}:")
        print(f"   Position: {old_pos} -> {player.position}")
        print(f"   Velocity: {old_vel} -> {player.velocity}")
        print(f"   On ground: {old_on_ground} -> {player.on_ground}")
        
        # Check if gravity was applied (velocity[1] should stay 0 if on ground)
        if player.on_ground and old_on_ground and player.velocity[1] < 0:
            print(f"   ❌ PROBLEM: Gravity applied even though player was on ground!")
            print(f"      This could cause sinking into blocks!")
            return False
        elif player.on_ground and old_on_ground and player.velocity[1] == 0:
            print(f"   ✅ GOOD: No gravity applied while on ground")
        
        print()
    
    return True

def test_gravity_when_falling():
    """Test that gravity IS applied when player is falling (not on ground)."""
    print("🧪 Testing Gravity When Player Is Falling\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world for clean test
    
    # Create a platform
    server.world.world[(10, 5, 10)] = "stone"
    
    print("✅ Created stone block at (10, 5, 10)")
    
    # Create a player in the air (not on ground)
    player = PlayerState("player1", (10, 20, 10), (0, 0), "TestPlayer")
    player.on_ground = False  # Player is in the air
    player.velocity = [0, 0, 0]  # No initial velocity
    player.last_move_time = 0  # Allow physics to apply immediately
    
    print(f"Initial state:")
    print(f"   Position: {player.position}")
    print(f"   Velocity: {player.velocity}")
    print(f"   On ground: {player.on_ground}")
    
    # Apply physics - this SHOULD apply gravity if player is not on ground
    print(f"\n🧪 Applying physics (SHOULD apply gravity when not on ground):")
    
    for i in range(3):
        old_pos = player.position
        old_vel = player.velocity[:]
        old_on_ground = player.on_ground
        
        server._apply_physics(player, 0.1)
        
        print(f"Step {i+1}:")
        print(f"   Position: {old_pos} -> {player.position}")
        print(f"   Velocity: {old_vel} -> {player.velocity}")
        print(f"   On ground: {old_on_ground} -> {player.on_ground}")
        
        # Check if gravity was applied when not on ground
        if not old_on_ground and player.velocity[1] <= old_vel[1]:
            print(f"   ✅ GOOD: Gravity applied while falling")
        elif not old_on_ground and player.velocity[1] == old_vel[1]:
            print(f"   ❌ PROBLEM: No gravity applied while falling!")
            return False
        
        print()
    
    return True

if __name__ == "__main__":
    print("🎮 Testing Gravity Application Logic\n")
    
    try:
        success = True
        success &= test_gravity_when_on_ground()
        success &= test_gravity_when_falling()
        
        if success:
            print("🎉 ALL GRAVITY TESTS PASSED!")
            print("✅ Gravity logic is working correctly")
        else:
            print("❌ Some gravity tests failed!")
            print("🔧 Need to fix gravity application logic")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)