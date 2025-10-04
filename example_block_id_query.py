#!/usr/bin/env python3
"""
Example usage of block_id query feature.

This demonstrates querying blocks from a camera or user's perspective
using their block_id instead of having to provide explicit coordinates.
"""

import asyncio
import websockets
import json

async def example_block_id_query():
    """Example: Query blocks from camera perspective using block_id."""
    
    SERVER_URI = "ws://localhost:8765"
    
    async with websockets.connect(SERVER_URI) as ws:
        # 1. Join the game
        await ws.send(json.dumps({
            "type": "player_join",
            "data": {"name": "ExampleUser"}
        }))
        
        # 2. Receive initial messages
        data = json.loads(await ws.recv())  # world_init
        
        # Skip world chunks
        while True:
            data = json.loads(await ws.recv())
            if data["type"] == "player_list":
                break
        
        # 3. Get list of cameras to find their block_ids
        await ws.send(json.dumps({
            "type": "get_cameras_list",
            "data": {}
        }))
        
        data = json.loads(await ws.recv())
        cameras = data["data"]["cameras"]
        
        print(f"Found {len(cameras)} camera blocks:")
        for camera in cameras:
            print(f"  - Camera at {camera['position']}")
            print(f"    block_id: {camera['block_id']}")
            print(f"    collision: {camera['collision']}")
        
        # 4. Query blocks from first camera's perspective using block_id
        if cameras:
            camera_block_id = cameras[0]["block_id"]
            
            print(f"\nQuerying blocks from camera '{camera_block_id}'...")
            
            # THIS IS THE KEY FEATURE: Use block_id instead of position
            await ws.send(json.dumps({
                "type": "get_blocks_list",
                "data": {
                    "query_type": "view",
                    "block_id": camera_block_id,  # ← Use block_id here!
                    "rotation": [0, 0],            # Viewing direction
                    "view_distance": 30.0          # Distance to see
                }
            }))
            
            data = json.loads(await ws.recv())
            blocks = data["data"]["blocks"]
            
            print(f"Found {len(blocks)} blocks in camera's view:")
            for block in blocks[:5]:  # Show first 5
                print(f"  - {block['block_type']} at {block['position']}")
                print(f"    block_id: {block['block_id']}")
                print(f"    collision: {block['collision']}")
                print(f"    distance: {block['distance']:.1f}")
        
        # 5. You can also query from user's perspective
        print("\n" + "="*60)
        print("Getting users list to find user block_ids...")
        
        await ws.send(json.dumps({
            "type": "get_users_list",
            "data": {}
        }))
        
        data = json.loads(await ws.recv())
        users = data["data"]["users"]
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - {user['name']} (id: {user['id']})")
            print(f"    position: {user['position']}")
        
        # Query blocks from user's perspective (if there are other users)
        if len(users) > 0:
            user_id = users[0]["id"]  # User's ID is their block_id
            
            print(f"\nQuerying blocks from user's perspective...")
            
            await ws.send(json.dumps({
                "type": "get_blocks_list",
                "data": {
                    "query_type": "view",
                    "block_id": user_id,  # ← User's ID is their block_id!
                    "rotation": [45, 0],   # Looking at 45 degrees
                    "view_distance": 20.0
                }
            }))
            
            data = json.loads(await ws.recv())
            blocks = data["data"]["blocks"]
            
            print(f"Found {len(blocks)} blocks in user's view")

async def main():
    """Run the example."""
    print("Block ID Query Example")
    print("="*60)
    print()
    
    try:
        await example_block_id_query()
        print("\n" + "="*60)
        print("✅ Example completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Make sure server is running: python3 server.py
    asyncio.run(main())
