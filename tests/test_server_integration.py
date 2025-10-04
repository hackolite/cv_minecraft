#!/usr/bin/env python3
"""
Test the complete server integration with cube creation on user connection
"""

import asyncio
import websockets
import json
import requests
import time
from protocol import MessageType

async def test_user_connection_creates_cube():
    """Test that connecting to the server creates a cube."""
    print("🧪 Testing User Connection -> Cube Creation Flow")
    print("=" * 60)
    
    # Start the server in background
    from server import MinecraftServer
    server = MinecraftServer()
    
    server_task = asyncio.create_task(server.start_server())
    
    # Give server time to start
    await asyncio.sleep(2)
    
    try:
        # Connect as a client
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("✅ Connected to server")
            
            # Send player join message
            join_message = {
                "type": "player_join",
                "data": {"name": "TestPlayer"},
                "player_id": None
            }
            await websocket.send(json.dumps(join_message))
            print("✅ Sent player join message")
            
            # Wait for server response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ Received response: {response_data['type']}")
            
            # Give time for cube creation
            await asyncio.sleep(2)
            
            # Check server logs for cube creation
            if server.user_cubes:
                player_id = list(server.user_cubes.keys())[0]
                user_cube = server.user_cubes[player_id]
                
                print(f"✅ User cube created")
                print(f"   Cube ID: {user_cube.id}")
                print(f"   Position: {user_cube.position}")
                print(f"   Rotation: {user_cube.rotation}")
                
                # Test cube programmatically
                try:
                    # Test position update
                    user_cube.update_position((10, 50, 10))
                    print(f"✅ Cube position updated: {user_cube.position}")
                    
                    # Test rotation update
                    user_cube.update_rotation((45, 10))
                    print(f"✅ Cube rotation updated: {user_cube.rotation}")
                    
                    # Test child cube creation
                    child_cube = user_cube.create_child_cube("test_child", (15, 50, 15))
                    print(f"✅ Child cube created: {child_cube.id}")
                    print(f"   Child position: {child_cube.position}")
                    
                except Exception as e:
                    print(f"❌ Cube manipulation test failed: {e}")
            else:
                print("❌ No user cubes created")
    
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    finally:
        # Stop the server
        server.stop_server()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        print("✅ Server stopped")

async def main():
    """Main test function."""
    print("🚀 Starting Server Integration Test")
    print("=" * 60)
    
    try:
        await test_user_connection_creates_cube()
        print("\n🎉 Integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())