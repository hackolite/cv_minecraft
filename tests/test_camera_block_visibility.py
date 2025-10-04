#!/usr/bin/env python3
"""
Test to verify that camera blocks are visible to all users who connect to the server.
This addresses the requirement: "le bloc camera doit etre visible de tout les utilisateurs qui se connecte au serveur"
"""

import asyncio
import websockets
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def connect_and_check_camera_blocks(username):
    """Connect a user and check if camera blocks are visible in their world."""
    try:
        async with websockets.connect(SERVER_URI) as ws:
            # Join the game
            join_msg = {"type": "player_join", "data": {"name": username}}
            await ws.send(json.dumps(join_msg))
            
            # Get world initialization
            msg = await ws.recv()
            world_init = json.loads(msg)
            assert world_init["type"] == "world_init", f"Expected world_init, got {world_init['type']}"
            
            # Collect world chunks and look for camera blocks
            camera_blocks_found = []
            chunks_received = 0
            
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data["type"] == "world_chunk":
                    chunk_data = data["data"]
                    blocks = chunk_data["blocks"]
                    
                    # Check for camera blocks in this chunk
                    for pos, block_type in blocks.items():
                        if block_type == "camera":
                            # Convert string position back to tuple
                            pos_tuple = eval(pos)  # Safe since we control the data
                            camera_blocks_found.append(pos_tuple)
                    
                    chunks_received += 1
                    
                elif data["type"] == "player_list":
                    # Initialization complete
                    break
            
            logging.info(f"User {username}: Found {len(camera_blocks_found)} camera blocks")
            for pos in camera_blocks_found:
                logging.info(f"  - Camera block at position {pos}")
            
            return camera_blocks_found
            
    except Exception as e:
        logging.error(f"Error connecting user {username}: {e}")
        return []

async def test_camera_block_visibility():
    """Test that camera blocks are visible to all connecting users."""
    logging.info("🎥 Testing camera block visibility for all users")
    
    # Test with multiple users connecting
    users = ["Alice", "Bob", "Charlie"]
    user_camera_blocks = {}
    
    for user in users:
        camera_blocks = await connect_and_check_camera_blocks(user)
        user_camera_blocks[user] = camera_blocks
        # Small delay to avoid overwhelming the server
        await asyncio.sleep(0.5)
    
    # Verify all users see the same camera blocks
    if not user_camera_blocks:
        logging.error("❌ No users successfully connected")
        return False
    
    first_user = list(user_camera_blocks.keys())[0]
    expected_camera_blocks = user_camera_blocks[first_user]
    
    if not expected_camera_blocks:
        logging.error(f"❌ No camera blocks found for user {first_user}")
        return False
    
    # Check that all users see the same camera blocks
    all_match = True
    for user, camera_blocks in user_camera_blocks.items():
        if set(camera_blocks) != set(expected_camera_blocks):
            logging.error(f"❌ User {user} sees different camera blocks!")
            logging.error(f"   Expected: {expected_camera_blocks}")
            logging.error(f"   Got: {camera_blocks}")
            all_match = False
    
    if all_match:
        logging.info("✅ All users see the same camera blocks:")
        for pos in expected_camera_blocks:
            logging.info(f"   📹 Camera block at {pos}")
        logging.info(f"✅ Camera blocks are visible to all {len(users)} users!")
        return True
    else:
        logging.error("❌ Camera block visibility test failed")
        return False

async def main():
    """Main test function."""
    try:
        success = await test_camera_block_visibility()
        return 0 if success else 1
    except Exception as e:
        logging.error(f"Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))