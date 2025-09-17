#!/usr/bin/env python3
"""
Test to verify the player sinking fix is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState
from server import MinecraftServer

def test_sinking_fix():
    """Test that the sinking issue is fixed."""
    print("🧪 Testing Player Sinking Fix\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world for clean test
    
    # Create a simple platform
    for x in range(9, 12):
        for z in range(9, 12):
            server.world.world[(x, 10, z)] = "stone"
    
    print("✅ Created 3x3 stone platform at Y=10")
    print("   Blocks: (9,10,9) to (11,10,11)")
    
    # Test cases that should work (no sinking)
    valid_positions = [
        (10, 11, 10, "Standing on center of platform"),
        (9, 11, 9, "Standing on corner of platform"),
        (11, 11, 11, "Standing on opposite corner"),
        (10, 11.5, 10, "Standing above platform"),
        (10, 12, 10, "Well above platform"),
    ]
    
    print("\n🧪 Testing valid positions (should NOT collide):")
    for x, y, z, description in valid_positions:
        collision = server._check_ground_collision((x, y, z))
        status = "✅" if not collision else "❌"
        print(f"   {status} {description}: ({x}, {y}, {z}) - {'CLEAR' if not collision else 'COLLISION'}")
        
        if collision:
            print(f"      ❌ SINKING BUG: Player should be able to stand at ({x}, {y}, {z})")
            return False
    
    # Test cases that should fail (inside blocks)
    invalid_positions = [
        (10, 10.5, 10, "Inside the platform block"),
        (10, 10, 10, "At platform level"),
        (10, 9.5, 10, "Below platform"),
    ]
    
    print("\n🧪 Testing invalid positions (should collide):")
    for x, y, z, description in invalid_positions:
        collision = server._check_ground_collision((x, y, z))
        status = "✅" if collision else "❌"
        print(f"   {status} {description}: ({x}, {y}, {z}) - {'COLLISION' if collision else 'CLEAR'}")
        
        if not collision:
            print(f"      ❌ COLLISION DETECTION FAILED: Should detect collision at ({x}, {y}, {z})")
            return False
    
    # Test edge cases around the platform
    edge_positions = [
        (8.9, 11, 10, "Just outside platform (X-)", False),
        (11.1, 11, 10, "Just outside platform (X+)", False),
        (10, 11, 8.9, "Just outside platform (Z-)", False),
        (10, 11, 11.1, "Just outside platform (Z+)", False),
        (9.1, 11, 9.1, "Near edge but on platform", False),
        (10.9, 11, 10.9, "Near opposite edge but on platform", False),
    ]
    
    print("\n🧪 Testing edge cases:")
    for x, y, z, description, should_collide in edge_positions:
        collision = server._check_ground_collision((x, y, z))
        expected = "COLLISION" if should_collide else "CLEAR"
        actual = "COLLISION" if collision else "CLEAR"
        status = "✅" if (collision == should_collide) else "❌"
        print(f"   {status} {description}: ({x}, {y}, {z}) - expected {expected}, got {actual}")
        
        if collision != should_collide:
            return False
    
    print("\n✅ All sinking fix tests passed!")
    return True

def test_physics_landing():
    """Test that physics places players correctly on platforms."""
    print("\n🧪 Testing Physics Landing on Platform\n")
    
    # Create a server instance
    server = MinecraftServer()
    server.world.world = {}  # Clear generated world
    
    # Create a platform at Y=5
    server.world.world[(10, 5, 10)] = "stone"
    
    print("✅ Created single stone block at (10, 5, 10)")
    
    # Create a player high above the platform
    player = PlayerState("player1", (10, 20, 10), (0, 0), "TestPlayer")
    player.velocity = [0, -10, 0]  # Falling down
    player.on_ground = False
    player.last_move_time = 0  # Allow physics to apply
    
    print(f"Player starting position: {player.position}")
    print(f"Player velocity: {player.velocity}")
    
    # Apply physics multiple times to simulate falling
    for i in range(10):
        old_pos = player.position
        server._apply_physics(player, 0.1)
        new_pos = player.position
        
        print(f"Step {i+1}: {old_pos} -> {new_pos}, on_ground: {player.on_ground}")
        
        if player.on_ground:
            print(f"Player landed at Y={new_pos[1]}")
            
            # Player should land at Y=6 (on top of block at Y=5)
            if abs(new_pos[1] - 6) < 0.1:
                print("✅ Player correctly landed on top of block!")
                return True
            else:
                print(f"❌ Player landed at wrong height: {new_pos[1]} (expected ~6)")
                return False
    
    print("❌ Player never landed - physics may not be working")
    return False

if __name__ == "__main__":
    print("🎮 Testing Player Sinking Fix\n")
    
    try:
        success = True
        success &= test_sinking_fix()
        success &= test_physics_landing()
        
        if success:
            print("\n🎉 ALL SINKING FIX TESTS PASSED!")
            print("✅ Players can no longer sink into blocks")
            print("✅ Collision detection works correctly")
            print("✅ Physics places players correctly on platforms")
        else:
            print("\n❌ Some sinking fix tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)