#!/usr/bin/env python3
"""
Test to reproduce and fix the player sinking into cubes issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer

def test_player_sinking_issue():
    """Test that reproduces the player sinking into cubes issue."""
    print("🧪 Testing Player Sinking Into Cubes Issue\n")
    
    # Create a server instance
    server = MinecraftServer()
    
    # Create a simple world with a block at ground level
    server.world.world[(10, 10, 10)] = "grass"
    server.world.world[(10, 9, 10)] = "stone"
    server.world.world[(10, 8, 10)] = "stone"
    
    print("✅ Created test world:")
    print(f"   Grass block at (10, 10, 10)")
    print(f"   Stone block at (10, 9, 10)")  
    print(f"   Stone block at (10, 8, 10)")
    
    # Create a player
    player = PlayerState("player1", (10, 11, 10), (0, 0), "TestPlayer")
    server.players["player1"] = player
    
    print(f"✅ Player created at position: {player.position}")
    print(f"   Player should be standing on grass block at y=10")
    
    # Test 1: Check if player position y=11 has collision with blocks
    collision = server._check_ground_collision((10, 11, 10))
    print(f"🔍 Ground collision at (10, 11, 10): {collision}")
    
    # Test 2: Check collision at y=10.5 (half-way into the grass block)
    collision = server._check_ground_collision((10, 10.5, 10))
    print(f"🔍 Ground collision at (10, 10.5, 10): {collision}")
    
    # Test 3: Check collision at y=10.1 (just above the grass block)
    collision = server._check_ground_collision((10, 10.1, 10))
    print(f"🔍 Ground collision at (10, 10.1, 10): {collision}")
    
    # Test 4: Check what happens when we try to place player at y=10.5
    try:
        # Simulate player movement to y=10.5 (sinking into the block)
        new_position = (10, 10.5, 10)
        if server._check_ground_collision(new_position):
            print(f"✅ Collision correctly detected at {new_position} - movement should be blocked")
        else:
            print(f"❌ No collision detected at {new_position} - this is the sinking bug!")
            
        # Test if physics would place the player correctly on top
        player.position = (10, 15, 10)  # High above the block
        player.velocity = [0, -10, 0]  # Falling down
        player.on_ground = False
        
        print(f"🧪 Testing physics landing:")
        print(f"   Player at: {player.position}")
        print(f"   Velocity: {player.velocity}")
        
        # Apply physics
        server._apply_physics(player, 0.1)
        
        print(f"   After physics: {player.position}")
        print(f"   On ground: {player.on_ground}")
        
        # Check if player ended up at the correct height
        if abs(player.position[1] - 11) < 0.1:  # Should be at y=11 (on top of y=10 block)
            print("✅ Physics correctly placed player on top of block")
        else:
            print(f"❌ Physics placed player at incorrect height: {player.position[1]} (expected ~11)")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    return True

def test_detailed_collision_bounds():
    """Test the detailed collision detection bounds."""
    print("\n🔍 Testing Detailed Collision Bounds\n")
    
    server = MinecraftServer()
    
    # Place a block at (0, 0, 0)
    server.world.world[(0, 0, 0)] = "stone"
    
    # Test various positions around the block
    test_positions = [
        (0.0, 1.0, 0.0),   # Directly above
        (0.0, 0.5, 0.0),   # Inside the block  
        (0.0, 1.5, 0.0),   # Above with player height
        (0.4, 1.0, 0.0),   # Edge of player collision box
        (0.5, 1.0, 0.0),   # Just outside player collision box
        (0.0, 1.8, 0.0),   # At player height limit
        (0.0, 2.0, 0.0),   # Above player height
    ]
    
    print("Testing collision at various positions:")
    for pos in test_positions:
        collision = server._check_ground_collision(pos)
        x, y, z = pos
        print(f"   Position ({x:3.1f}, {y:3.1f}, {z:3.1f}): {'COLLISION' if collision else 'CLEAR'}")
    
    return True

if __name__ == "__main__":
    print("🎮 Testing Player Sinking Issue\n")
    
    try:
        success = True
        success &= test_player_sinking_issue()
        success &= test_detailed_collision_bounds()
        
        if success:
            print("\n🎉 ALL SINKING TESTS COMPLETED!")
        else:
            print("\n❌ Some tests revealed issues!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)