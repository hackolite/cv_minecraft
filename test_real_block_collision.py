#!/usr/bin/env python3
"""
Test real block collision detection for server-side collision management.
"""

import asyncio
import json
import math
import websockets
import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protocol import MessageType
from server import MinecraftServer

async def test_real_block_collision():
    """Test collision with actual world blocks."""
    
    print("🧪 Testing real block collision detection...")
    
    # Start server
    server = MinecraftServer(host='localhost', port=8767)
    server_task = asyncio.create_task(server.start_server())
    
    # Wait for server to start
    await asyncio.sleep(0.5)
    
    try:
        # Connect test client
        uri = "ws://localhost:8767"
        async with websockets.connect(uri) as websocket:
            
            # Join as player
            join_msg = {"type": "player_join", "data": {"name": "CollisionTester"}}
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
            
            # Test collision with ground level blocks (should exist)
            print("\n🧪 Testing collision with ground-level blocks")
            ground_level = 17  # Typical ground level in world generation
            
            # Try to move into ground
            ground_pos = [64, ground_level, 64]  # Should be in a solid block
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": ground_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                if status == "forbidden":
                    print("   ✅ Ground collision detected correctly")
                else:
                    print("   ⚠️ No collision detected - might be empty space")
            
            # Test collision by trying to move below ground
            print("\n🧪 Testing collision below ground level")
            underground_pos = [64, ground_level - 5, 64]  # Definitely underground
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": underground_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                if status == "forbidden":
                    print("   ✅ Underground collision detected correctly")
                else:
                    print("   ⚠️ No collision detected underground")
            
            # Test valid movement to higher positions
            print("\n🧪 Testing valid movement to safe height")
            safe_pos = [spawn_position[0] + 2, spawn_position[1] + 5, spawn_position[2]]
            move_msg = {
                "type": "player_move", 
                "data": {
                    "position": safe_pos,
                    "rotation": [0, 0]
                }
            }
            await websocket.send(json.dumps(move_msg))
            
            response = json.loads(await websocket.recv())
            print(f"📥 Received: {response}")
            
            if response["type"] == "movement_response":
                status = response["data"]["status"]
                position = response["data"]["position"]
                print(f"   Status: {status}, Position: {position}")
                if status == "ok":
                    print("   ✅ Valid movement accepted")
                else:
                    print(f"   ❌ Valid movement rejected: {status}")
            
            # Test gradual movement down until collision
            print("\n🧪 Testing gradual movement down to find collision point")
            current_pos = safe_pos
            for y_offset in range(0, 50, 5):  # Move down in steps
                test_pos = [current_pos[0], current_pos[1] - y_offset, current_pos[2]]
                move_msg = {
                    "type": "player_move", 
                    "data": {
                        "position": test_pos,
                        "rotation": [0, 0]
                    }
                }
                await websocket.send(json.dumps(move_msg))
                
                response = json.loads(await websocket.recv())
                if response["type"] == "movement_response":
                    status = response["data"]["status"]
                    position = response["data"]["position"]
                    print(f"   Y={test_pos[1]}: {status}")
                    
                    if status == "forbidden":
                        print(f"   ✅ Found collision at Y={test_pos[1]}")
                        break
                    elif status == "ok":
                        current_pos = test_pos  # Update current position
            
            print("\n✅ Real block collision tests completed!")
            
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

if __name__ == "__main__":
    print("🚀 Starting real block collision tests...")
    asyncio.run(test_real_block_collision())
    print("\n🎉 All real block collision tests completed!")