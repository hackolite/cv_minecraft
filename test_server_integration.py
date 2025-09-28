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
    """Test that connecting to the server creates a cube with FastAPI endpoints."""
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
                cube_port = user_cube.port
                
                print(f"✅ User cube created on port: {cube_port}")
                
                # Test cube API endpoints
                try:
                    # Test cube info
                    response = requests.get(f"http://localhost:{cube_port}/", timeout=2)
                    if response.status_code == 200:
                        print("✅ Cube API accessible")
                        cube_info = response.json()
                        print(f"   Cube ID: {cube_info['cube_id']}")
                        print(f"   Position: {cube_info['position']}")
                    
                    # Test movement
                    response = requests.post(f"http://localhost:{cube_port}/move/forward?distance=3", timeout=2)
                    if response.status_code == 200:
                        print("✅ Cube movement working")
                        move_result = response.json()
                        print(f"   New position: {move_result['position']}")
                    
                    # Test child cube creation
                    response = requests.post(
                        f"http://localhost:{cube_port}/cubes/create?child_id=test_child&x=15&y=50&z=15", 
                        timeout=5
                    )
                    if response.status_code == 200:
                        print("✅ Child cube creation working")
                        child_info = response.json()
                        child_port = child_info['child_cube']['port']
                        print(f"   Child cube port: {child_port}")
                        
                        # Test child cube API
                        child_response = requests.get(f"http://localhost:{child_port}/", timeout=2)
                        if child_response.status_code == 200:
                            print("✅ Child cube API accessible")
                    
                except Exception as e:
                    print(f"❌ API test failed: {e}")
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