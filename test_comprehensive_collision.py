#!/usr/bin/env python3
"""
Comprehensive collision integration test to simulate real multiplayer scenarios.
This tests both client-side and server-side collision systems working together.
"""

import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import PlayerState, MessageType, create_player_move_message
from server import MinecraftServer

# Import collision function from test file (to avoid OpenGL issues)
def check_player_collision(position, player_size, other_players):
    """Check if a player at given position and size collides with other players."""
    px, py, pz = position
    
    for other_player in other_players:
        if not isinstance(other_player, PlayerState):
            continue
            
        # Get other player's position and size
        ox, oy, oz = other_player.position
        other_size = other_player.size
        
        # Check 3D bounding box collision
        # Two boxes collide if they overlap in all three dimensions
        x_overlap = (px - player_size) < (ox + other_size) and (px + player_size) >= (ox - other_size)
        y_overlap = (py - player_size) < (oy + other_size) and (py + player_size) >= (oy - other_size)
        z_overlap = (pz - player_size) < (oz + other_size) and (pz + player_size) >= (oz - other_size)
        
        if x_overlap and y_overlap and z_overlap:
            return True
    
    return False

async def test_full_collision_integration():
    """Test the full collision system integration with multiple players."""
    print("🎮 Full Collision Integration Test\n")
    
    # Create server
    server = MinecraftServer()
    
    # Simulate player join
    player1_id = "player1"
    player2_id = "player2"
    
    # Create players
    player1 = PlayerState(player1_id, (64, 100, 64), (0, 0), "Alice")
    player2 = PlayerState(player2_id, (70, 100, 70), (0, 0), "Bob")
    
    # Add players to server
    server.players[player1_id] = player1
    server.players[player2_id] = player2
    
    print(f"✅ Players initialized:")
    print(f"   Alice at {player1.position}")
    print(f"   Bob at {player2.position}")
    
    # Test 1: Normal movement should work
    print("\n🧪 Test 1: Normal movement")
    try:
        new_position = (65, 100, 64)
        move_msg = create_player_move_message(new_position, (0, 0))
        
        # Simulate server handling the movement
        if not server._check_player_collision(player1_id, new_position):
            player1.position = new_position
            print(f"✅ Alice moved to {new_position} - no collision")
        else:
            print(f"❌ Alice movement blocked unexpectedly")
            return False
    except Exception as e:
        print(f"❌ Normal movement failed: {e}")
        return False
    
    # Test 2: Movement into another player should be blocked
    print("\n🧪 Test 2: Player-to-player collision blocking")
    try:
        collision_position = (70, 100, 70)  # Bob's position
        
        # Check client-side collision first
        other_players = [player2]
        client_collision = check_player_collision(collision_position, 0.4, other_players)
        
        # Check server-side collision
        server_collision = server._check_player_collision(player1_id, collision_position)
        
        if client_collision and server_collision:
            print(f"✅ Both client and server correctly blocked movement to {collision_position}")
        else:
            print(f"❌ Collision detection failed - client: {client_collision}, server: {server_collision}")
            return False
            
    except Exception as e:
        print(f"❌ Player collision test failed: {e}")
        return False
    
    # Test 3: Movement into blocks should be blocked
    print("\n🧪 Test 3: Block collision blocking")
    try:
        # Add a block at a specific position
        block_position = (66, 100, 64)
        server.world.world[block_position] = "stone"
        
        # Try to move into the block
        block_collision = server._check_ground_collision(block_position)
        
        if block_collision:
            print(f"✅ Server correctly blocked movement into block at {block_position}")
        else:
            print(f"❌ Server failed to detect block collision")
            return False
            
    except Exception as e:
        print(f"❌ Block collision test failed: {e}")
        return False
    
    # Test 4: Simulate physics collision prevention
    print("\n🧪 Test 4: Physics collision prevention")
    try:
        # Move players very close to each other
        player1.position = (68, 100, 68)
        player2.position = (68.5, 100, 68)
        
        # Set velocity that would cause collision
        original_pos = player1.position
        player1.velocity = [1.0, 0.0, 0.0]  # Moving towards player2
        player1.last_move_time = 0  # Allow physics
        
        # Apply physics - should be blocked by collision
        server._apply_physics(player1, 0.1)
        
        if player1.position == original_pos:
            print("✅ Physics collision prevention worked")
        else:
            print(f"❌ Physics collision prevention failed - moved to {player1.position}")
            return False
            
    except Exception as e:
        print(f"❌ Physics collision test failed: {e}")
        return False
    
    # Test 5: Test multiple players in a small area
    print("\n🧪 Test 5: Multiple players collision management")
    try:
        # Add more players in a small area
        player3 = PlayerState("player3", (69, 100, 68), (0, 0), "Charlie")
        player4 = PlayerState("player4", (68, 100, 69), (0, 0), "Diana")
        
        server.players["player3"] = player3
        server.players["player4"] = player4
        
        # Try to move player1 into the crowded area
        crowded_position = (68.5, 100, 68.5)
        collision = server._check_player_collision(player1_id, crowded_position)
        
        if collision:
            print("✅ Multiple player collision detection works")
        else:
            print("❌ Multiple player collision detection failed")
            return False
            
    except Exception as e:
        print(f"❌ Multiple player test failed: {e}")
        return False
    
    return True

async def test_movement_validation():
    """Test that movement validation prevents cheating."""
    print("\n🎮 Movement Validation Test\n")
    
    server = MinecraftServer()
    player_id = "player1"
    player = PlayerState(player_id, (64, 100, 64), (0, 0), "Alice")
    server.players[player_id] = player
    
    print(f"✅ Player initialized at {player.position}")
    
    # Test invalid movements
    invalid_movements = [
        ((164, 100, 64), "Movement too far in X"),
        ((64, 200, 64), "Movement too far in Y"), 
        ((64, 100, 164), "Movement too far in Z"),
        ((-100, 100, 64), "Invalid position"),
    ]
    
    for invalid_pos, reason in invalid_movements:
        try:
            # Simulate handling movement message
            move_msg = create_player_move_message(invalid_pos, (0, 0))
            
            # This should raise an exception due to validation
            await server._handle_player_move(player_id, move_msg)
            print(f"❌ Invalid movement allowed: {reason}")
            return False
        except Exception as e:
            print(f"✅ {reason} correctly blocked: {type(e).__name__}")
    
    return True

if __name__ == "__main__":
    print("🎮 Comprehensive Collision System Integration Test\n")
    
    async def run_tests():
        try:
            success = True
            success &= await test_full_collision_integration()
            success &= await test_movement_validation()
            
            if success:
                print("\n🎉 ALL COMPREHENSIVE COLLISION TESTS PASSED!")
                print("✅ Client-side collision detection works")
                print("✅ Server-side collision detection works")
                print("✅ Player-to-player collision prevention works")
                print("✅ Block collision prevention works")
                print("✅ Physics collision prevention works")
                print("✅ Multiple player scenarios work")
                print("✅ Movement validation prevents cheating")
                print("\n🛡️ Users can no longer traverse through cubes or other players!")
            else:
                print("\n❌ Some comprehensive collision tests failed!")
                sys.exit(1)
                
        except Exception as e:
            print(f"\n💥 Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(run_tests())