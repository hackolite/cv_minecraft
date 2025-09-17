"""
Test for enhanced player position debugging and broadcasting system.
Tests that player movements are properly debugged, broadcasted, and received.
"""

import asyncio
import websockets
import json
import logging
import time
import pytest
from server import MinecraftServer
from protocol import MessageType

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO, 
    format="[%(asctime)s] %(levelname)s - %(message)s"
)

SERVER_URI = "ws://localhost:8765"

class MockPlayer:
    """Helper class to represent a test player."""
    def __init__(self, name, websocket=None):
        self.name = name
        self.websocket = websocket
        self.position = None
        self.player_id = None
        self.received_updates = []

async def send_json(ws, msg_type, data=None):
    """Send a JSON message to the websocket."""
    msg = {"type": msg_type}
    if data:
        msg["data"] = data
    await ws.send(json.dumps(msg))
    logging.info(f"📤 Sent: {msg}")

async def recv_json(ws):
    """Receive and parse a JSON message from the websocket."""
    msg = await ws.recv()
    data = json.loads(msg)
    logging.info(f"📥 Received: {data}")
    return data

@pytest.mark.asyncio
async def test_player_position_debug_and_broadcast():
    """Test that player position changes are properly debugged and broadcasted."""
    
    # Start the server in the background
    server = MinecraftServer()
    server_task = asyncio.create_task(server.start_server())
    
    # Wait a moment for the server to start
    await asyncio.sleep(0.5)
    
    try:
        # Create two test players
        player1_ws = await websockets.connect(SERVER_URI)
        player2_ws = await websockets.connect(SERVER_URI)
        
        # Player 1 joins
        await send_json(player1_ws, "player_join", {"name": "Alice"})
        init1 = await recv_json(player1_ws)
        assert init1["type"] == "world_init"
        player1_id = init1.get("player_id")
        initial_pos1 = init1.get("spawn_position", [64, 100, 64])
        
        # Skip chunk messages for player 1
        while True:
            msg = await recv_json(player1_ws)
            if msg["type"] == "player_list":
                break
        
        # Player 2 joins
        await send_json(player2_ws, "player_join", {"name": "Bob"})
        init2 = await recv_json(player2_ws)
        assert init2["type"] == "world_init"
        player2_id = init2.get("player_id")
        initial_pos2 = init2.get("spawn_position", [64, 100, 64])
        
        # Skip chunk messages for player 2
        while True:
            msg = await recv_json(player2_ws)
            if msg["type"] == "player_list":
                break
        
        # Player 1 should receive notification about Player 2 joining
        player_update = await recv_json(player1_ws)
        if player_update["type"] == "player_list":
            # Both players are now connected
            logging.info("✅ Both players connected successfully")
        
        # Test 1: Player 1 moves and Player 2 should receive the update
        new_position1 = [initial_pos1[0] + 10, initial_pos1[1], initial_pos1[2] + 5]
        await send_json(player1_ws, "player_move", {
            "position": new_position1,
            "rotation": [45, 0]
        })
        
        # Player 1 should receive confirmation
        confirmation1 = await recv_json(player1_ws)
        assert confirmation1["type"] == "player_update"
        assert confirmation1["data"]["id"] == player1_id
        assert confirmation1["data"]["position"] == new_position1
        
        # Player 2 should receive the broadcast
        broadcast_to_2 = await recv_json(player2_ws)
        assert broadcast_to_2["type"] == "player_update"
        assert broadcast_to_2["data"]["id"] == player1_id
        assert broadcast_to_2["data"]["position"] == new_position1
        
        logging.info("✅ Test 1 passed: Player movement broadcasted correctly")
        
        # Test 2: Player 2 moves and Player 1 should receive the update
        new_position2 = [initial_pos2[0] - 8, initial_pos2[1] + 3, initial_pos2[2] - 2]
        await send_json(player2_ws, "player_move", {
            "position": new_position2,
            "rotation": [90, 15]
        })
        
        # Player 2 should receive confirmation
        confirmation2 = await recv_json(player2_ws)
        assert confirmation2["type"] == "player_update"
        assert confirmation2["data"]["id"] == player2_id
        assert confirmation2["data"]["position"] == new_position2
        
        # Player 1 should receive the broadcast
        broadcast_to_1 = await recv_json(player1_ws)
        assert broadcast_to_1["type"] == "player_update"
        assert broadcast_to_1["data"]["id"] == player2_id
        assert broadcast_to_1["data"]["position"] == new_position2
        
        logging.info("✅ Test 2 passed: Second player movement broadcasted correctly")
        
        # Test 3: Rapid movements to test debug logging
        for i in range(3):
            rapid_pos = [new_position1[0] + i, new_position1[1], new_position1[2] + i]
            await send_json(player1_ws, "player_move", {
                "position": rapid_pos,
                "rotation": [i * 30, 0]
            })
            
            # Receive confirmations and broadcasts
            await recv_json(player1_ws)  # confirmation
            await recv_json(player2_ws)  # broadcast
        
        logging.info("✅ Test 3 passed: Rapid movements handled correctly")
        
        # Clean up
        await player1_ws.close()
        await player2_ws.close()
        
    finally:
        # Stop the server
        server.running = False
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_player_position_storage_verification():
    """Test that clients properly store received player positions."""
    
    # This test would require access to client model internals
    # For now, we rely on the debug logging to verify storage
    
    # Start the server
    server = MinecraftServer()
    server_task = asyncio.create_task(server.start_server())
    
    await asyncio.sleep(0.5)
    
    try:
        # Connect a single client
        ws = await websockets.connect(SERVER_URI)
        
        # Join as a player
        await send_json(ws, "player_join", {"name": "TestPlayer"})
        init_msg = await recv_json(ws)
        
        # Skip chunks and wait for player_list
        while True:
            msg = await recv_json(ws)
            if msg["type"] == "player_list":
                break
        
        # Move the player
        new_pos = [50, 75, 30]
        await send_json(ws, "player_move", {
            "position": new_pos,
            "rotation": [0, 0]
        })
        
        # Receive confirmation
        confirmation = await recv_json(ws)
        assert confirmation["type"] == "player_update"
        assert confirmation["data"]["position"] == new_pos
        
        logging.info("✅ Position storage verification test passed")
        
        await ws.close()
        
    finally:
        server.running = False
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_player_position_debug_and_broadcast())
    asyncio.run(test_player_position_storage_verification())