#!/usr/bin/env python3
"""
Test to verify that multiple users connect to the same map/world.

This test validates that:
1. Multiple users get the same world data
2. Changes made by one user are visible to others
3. All users spawn in the same world with the same blocks
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"


async def recv_json(ws):
    msg = await ws.recv()
    logging.info(f"Reçu <- {msg[:100]}...")  # Truncate long messages
    return json.loads(msg)


async def send_json(ws, msg_type, data=None):
    msg = {"type": msg_type}
    if data:
        msg["data"] = data
    await ws.send(json.dumps(msg))
    logging.info(f"Envoyé -> {msg}")


async def connect_user_and_get_world_data(username):
    """Connect a user and get their world initialization data."""
    async with websockets.connect(SERVER_URI) as ws:
        # Send player join
        await send_json(ws, "player_join", {"name": username})
        
        # Receive world_init
        init_msg = await recv_json(ws)
        assert init_msg["type"] == "world_init", f"Expected world_init, got {init_msg['type']}"
        
        # Collect all chunks
        chunks = {}
        chunks_received = 0
        while True:
            msg = await recv_json(ws)
            if msg["type"] == "world_chunk":
                chunk_data = msg["data"]
                chunk_key = (chunk_data["chunk_x"], chunk_data["chunk_z"])
                chunks[chunk_key] = chunk_data["blocks"]
                chunks_received += 1
            elif msg["type"] == "player_list":
                logging.info(f"User {username} received {chunks_received} chunks")
                break
            else:
                logging.info(f"Unexpected message during init: {msg['type']}")
                break
        
        return init_msg["data"], chunks


async def test_multiple_users_same_world():
    """Test that multiple users get the same world data."""
    logging.info("🧪 Testing multiple users receive the same world...")
    
    # Connect two users and get their world data
    user1_world, user1_chunks = await connect_user_and_get_world_data("User1")
    user2_world, user2_chunks = await connect_user_and_get_world_data("User2")
    
    # Verify world initialization data is the same
    assert user1_world == user2_world, f"World data differs:\nUser1: {user1_world}\nUser2: {user2_world}"
    logging.info("✅ Both users received identical world initialization data")
    
    # Verify both users got the same chunks
    assert user1_chunks.keys() == user2_chunks.keys(), "Users received different chunk sets"
    
    # Check a few sample chunks for identical content
    sample_chunks = list(user1_chunks.keys())[:3]  # Check first 3 chunks
    for chunk_key in sample_chunks:
        assert user1_chunks[chunk_key] == user2_chunks[chunk_key], f"Chunk {chunk_key} differs between users"
    
    logging.info(f"✅ Verified {len(sample_chunks)} sample chunks are identical between users")
    logging.info(f"Total chunks: {len(user1_chunks)}")


async def test_shared_block_changes():
    """Test that block changes by one user are visible to others."""
    logging.info("🧪 Testing shared block changes...")
    
    # Connect two users
    ws1 = await websockets.connect(SERVER_URI)
    ws2 = await websockets.connect(SERVER_URI)
    
    try:
        # User 1 joins
        await send_json(ws1, "player_join", {"name": "User1"})
        await recv_json(ws1)  # world_init
        
        # Wait for all chunks and player_list for user 1
        while True:
            msg = await recv_json(ws1)
            if msg["type"] == "player_list":
                break
        
        # User 2 joins
        await send_json(ws2, "player_join", {"name": "User2"})
        await recv_json(ws2)  # world_init
        
        # Wait for all chunks and player_list for user 2
        while True:
            msg = await recv_json(ws2)
            if msg["type"] == "player_list":
                break
        
        # User 1 places a block at a unique position
        test_position = [50, 85, 50]
        await send_json(ws1, "block_place", {"position": test_position, "block_type": "brick"})
        
        # User 1 should receive world_update
        msg1 = await recv_json(ws1)
        # Might get player_update first due to physics, so keep reading until world_update
        while msg1["type"] != "world_update":
            msg1 = await recv_json(ws1)
        
        assert msg1["type"] == "world_update", f"User1 expected world_update, got {msg1['type']}"
        
        # User 2 should also receive the same world_update
        msg2 = await recv_json(ws2)
        # Might get player_update first due to physics, so keep reading until world_update
        while msg2["type"] != "world_update":
            msg2 = await recv_json(ws2)
            
        assert msg2["type"] == "world_update", f"User2 expected world_update, got {msg2['type']}"
        assert msg1["data"] == msg2["data"], f"Block update differs:\nUser1: {msg1['data']}\nUser2: {msg2['data']}"
        
        logging.info("✅ Block changes are properly shared between users")
        
    finally:
        await ws1.close()
        await ws2.close()


async def main():
    """Run all tests."""
    await test_multiple_users_same_world()
    await test_shared_block_changes()
    logging.info("🎉 All multi-user tests passed! Users are on the same map.")


if __name__ == "__main__":
    asyncio.run(main())