#!/usr/bin/env python3
"""
Multi-client test to verify multiplayer functionality.
"""

import asyncio
import websockets
import json
import random
from protocol import *

async def test_client(client_id, duration=10):
    """Test client that connects and simulates player actions."""
    try:
        uri = "ws://localhost:8765"
        print(f"Client {client_id}: Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print(f"Client {client_id}: Connected!")
            
            # Send join message
            join_msg = create_player_join_message(f"TestPlayer{client_id}")
            await websocket.send(join_msg.to_json())
            
            # Listen for initial messages
            message_count = 0
            start_time = asyncio.get_event_loop().time()
            
            # Set up a task to receive messages
            async def receive_messages():
                nonlocal message_count
                try:
                    async for message_str in websocket:
                        message = Message.from_json(message_str)
                        message_count += 1
                        
                        if message.type == MessageType.WORLD_INIT:
                            print(f"Client {client_id}: Received world init")
                        elif message.type == MessageType.WORLD_CHUNK:
                            print(f"Client {client_id}: Received world chunk")
                        elif message.type == MessageType.PLAYER_LIST:
                            players = message.data.get("players", [])
                            print(f"Client {client_id}: Player list updated, {len(players)} players online")
                        elif message.type == MessageType.PLAYER_UPDATE:
                            player_data = message.data
                            print(f"Client {client_id}: Player {player_data.get('name', 'Unknown')} moved")
                            
                except websockets.exceptions.ConnectionClosed:
                    print(f"Client {client_id}: Connection closed")
            
            # Set up a task to send periodic updates
            async def send_updates():
                while True:
                    await asyncio.sleep(2)
                    
                    # Send a random movement
                    x = 30 + random.randint(-10, 10)
                    y = 50 + random.randint(-5, 5)
                    z = 80 + random.randint(-10, 10)
                    
                    move_msg = create_player_move_message((x, y, z), (0, 0))
                    await websocket.send(move_msg.to_json())
                    print(f"Client {client_id}: Sent movement to ({x}, {y}, {z})")
            
            # Run both tasks concurrently
            receive_task = asyncio.create_task(receive_messages())
            send_task = asyncio.create_task(send_updates())
            
            # Wait for the specified duration
            await asyncio.sleep(duration)
            
            # Cancel tasks
            receive_task.cancel()
            send_task.cancel()
            
            print(f"Client {client_id}: Test completed, received {message_count} messages")
    
    except Exception as e:
        print(f"Client {client_id}: Error - {e}")

async def test_multiple_clients():
    """Test with multiple clients."""
    print("Starting multi-client test...")
    
    # Start 3 clients concurrently
    tasks = [
        test_client(1, 15),
        test_client(2, 15),
        test_client(3, 15)
    ]
    
    await asyncio.gather(*tasks)
    print("Multi-client test completed!")

if __name__ == "__main__":
    asyncio.run(test_multiple_clients())