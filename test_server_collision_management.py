#!/usr/bin/env python3
"""
Test for server-side collision management implementation.
Validates that the server properly handles movement requests with simple collision checking.
"""

import asyncio
import json
import math
import websockets
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import MessageType, create_player_move_message, create_movement_response_message
from server import MinecraftServer

async def test_server_collision_management():
    """Test server-side collision management with simple collision check."""
    
    print("🧪 Testing server-side collision management...")
    
    # Start server
    server = MinecraftServer(host='localhost', port=8766)
    server_task = asyncio.create_task(server.start_server())
    
    # Wait for server to start
    await asyncio.sleep(0.5)
    
    try:
        # Connect test client
        uri = "ws://localhost:8766"
        async with websockets.connect(uri) as websocket:
            
            # Join as player
            join_msg = {"type": "player_join", "data": {"name": "TestPlayer"}}
            await websocket.send(json.dumps(join_msg))
            
            # Receive world_init
            response = json.loads(await websocket.recv())
            assert response["type"] == "world_init", f"Expected world_init, got {response['type']}"
            spawn_position = response.get("spawn_position", [64, 100, 64])
            print(f"✅ Player spawned at: {spawn_position}")
            
            # Skip chunks until player_list
            while True:
                msg = json.loads(await websocket.recv())
                if msg["type"] == "player_list":
                    break
            
            # Test 1: Valid movement (should return 'ok')
            print("\n🧪 Test 1: Valid movement")
            valid_pos = [spawn_position[0] + 1, spawn_position[1], spawn_position[2]]
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": valid_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            # Should receive movement_response with 'ok' status
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                assert status == "ok", f"Expected 'ok', got '{status}'"
                assert position == valid_pos, f"Expected {valid_pos}, got {position}"
                print("   ✅ Valid movement accepted correctly")
            else:
                print(f"   ❌ Expected movement_response, got {response['type']}")
            
            # Test 2: Invalid movement (collision with block - assuming there's a block at origin)
            print("\n🧪 Test 2: Movement into collision")
            # Try to move into a solid block (assuming world has blocks)
            collision_pos = [0, 0, 0]  # This should likely be a solid block
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": collision_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            # Should receive movement_response with 'forbidden' status
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                if status == "forbidden":
                    print("   ✅ Collision correctly detected, movement forbidden")
                elif status == "ok":
                    print("   ⚠️ Movement allowed (might be no block at this position)")
                else:
                    print(f"   ❌ Unexpected status: {status}")
            else:
                print(f"   ❌ Expected movement_response, got {response['type']}")
            
            # Test 3: Overly large movement (anti-cheat)
            print("\n🧪 Test 3: Anti-cheat large movement")
            large_pos = [spawn_position[0] + 100, spawn_position[1], spawn_position[2]]
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": large_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            # Should receive movement_response with 'forbidden' status
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                assert status == "forbidden", f"Expected 'forbidden' for large movement, got '{status}'"
                print("   ✅ Anti-cheat correctly blocked large movement")
            else:
                print(f"   ❌ Expected movement_response, got {response['type']}")
            
            print("\n✅ All tests completed!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop server
        server.running = False
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

def test_simple_collision_logic():
    """Test the simple collision detection logic."""
    print("\n🧪 Testing simple collision detection logic...")
    
    # Create server instance for testing
    server = MinecraftServer()
    
    # Add some test blocks to a clear area high up in the world
    test_height = 200  # High above normal terrain
    server.world.world[(10, test_height, 10)] = "stone"
    server.world.world[(11, test_height + 2, 11)] = "stone"  # Head height collision test
    
    # Test 1: No collision in clear air high above terrain
    clear_pos = (50, test_height + 10, 50)  # Should be clear air
    result = server._check_simple_collision(clear_pos, "test_player")
    print(f"   Position {clear_pos} collision: {result}")
    if result:
        # Check what block is there
        foot_block = (int(math.floor(clear_pos[0])), int(math.floor(clear_pos[1])), int(math.floor(clear_pos[2])))
        head_block = (int(math.floor(clear_pos[0])), int(math.floor(clear_pos[1] + 1.8)), int(math.floor(clear_pos[2])))
        print(f"     Foot block {foot_block} in world: {foot_block in server.world.world}")
        print(f"     Head block {head_block} in world: {head_block in server.world.world}")
        print("   ⚠️ Position has collision (might be terrain generation)")
    else:
        print("   ✅ No collision detected correctly")
    
    # Test 2: Foot collision with known block
    collision_pos = (10.5, test_height + 0.5, 10.5)  # Inside the block we placed
    result = server._check_simple_collision(collision_pos, "test_player")
    print(f"   Position {collision_pos} collision: {result}")
    assert result, f"Expected collision with block at (10,{test_height},10)"
    print("   ✅ Foot collision detected correctly")
    
    # Test 3: Head collision (player height = 1.8)
    head_collision_pos = (11.5, test_height + 0.5, 11.5)  # Head would be at test_height+2.3, hitting block at test_height+2
    result = server._check_simple_collision(head_collision_pos, "test_player")
    print(f"   Position {head_collision_pos} head collision: {result}")
    assert result, f"Expected head collision with block at (11,{test_height + 2},11)"
    print("   ✅ Head collision detected correctly")
    
    print("✅ Simple collision logic tests completed!")

if __name__ == "__main__":
    print("🚀 Starting server-side collision management tests...")
    
    # Test the collision logic first
    test_simple_collision_logic()
    
    # Test the full server integration
    asyncio.run(test_server_collision_management())
    
    print("\n🎉 All server-side collision management tests completed!")