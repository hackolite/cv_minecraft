#!/usr/bin/env python3
"""
Simple test client to verify server connection.
"""

import asyncio
import websockets
import json
from protocol import *

async def test_connection():
    """Test basic connection to the server."""
    try:
        uri = "ws://localhost:8765"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("Connected to server!")
            
            # Send join message
            join_msg = create_player_join_message("TestPlayer")
            await websocket.send(join_msg.to_json())
            print("Sent join message")
            
            # Wait for initial messages
            for i in range(3):
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = Message.from_json(message_str)
                    print(f"Received message: {message.type.value}")
                    
                    if message.type == MessageType.WORLD_INIT:
                        world_data = message.data
                        blocks_count = len(world_data.get("blocks", {}))
                        print(f"World initialized with {blocks_count} blocks")
                    
                except asyncio.TimeoutError:
                    print("No more messages received")
                    break
            
            print("Test completed successfully!")
    
    except Exception as e:
        print(f"Connection test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())