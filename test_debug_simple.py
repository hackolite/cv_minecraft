"""
Simple test to verify that the debug and broadcast system is working.
This test focuses on demonstrating the debug logging and position broadcasting.
"""

import asyncio
import websockets
import json
import logging
import sys

# Configure logging to see all debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    stream=sys.stdout
)

SERVER_URI = "ws://localhost:8765"

async def send_json(ws, msg_type, data=None):
    """Send a JSON message to the websocket."""
    msg = {"type": msg_type}
    if data:
        msg["data"] = data
    await ws.send(json.dumps(msg))
    print(f"📤 CLIENT SENT: {msg}")

async def recv_json(ws):
    """Receive and parse a JSON message from the websocket."""
    msg = await ws.recv()
    data = json.loads(msg)
    print(f"📥 CLIENT RECEIVED: {data}")
    return data

async def wait_for_message_type(ws, expected_type, timeout=5.0):
    """Wait for a specific message type, skipping others."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            msg = await asyncio.wait_for(recv_json(ws), timeout=1.0)
            if msg["type"] == expected_type:
                return msg
        except asyncio.TimeoutError:
            continue
    raise TimeoutError(f"Expected message type '{expected_type}' not received within {timeout}s")

async def skip_chunk_messages(ws):
    """Skip all chunk messages until we get to player_list."""
    while True:
        try:
            msg = await asyncio.wait_for(recv_json(ws), timeout=2.0)
            if msg["type"] == "player_list":
                return msg
        except asyncio.TimeoutError:
            break
    return None

async def test_debug_system():
    """Test that demonstrates the debug and broadcast system."""
    
    print("🚀 Starting debug system test...")
    
    try:
        # Connect two players
        print("🔗 Connecting Player 1...")
        player1_ws = await websockets.connect(SERVER_URI)
        
        print("🔗 Connecting Player 2...")
        player2_ws = await websockets.connect(SERVER_URI)
        
        # Player 1 joins
        print("\n👤 Player 1 (Alice) joining...")
        await send_json(player1_ws, "player_join", {"name": "Alice"})
        
        # Get initialization message
        init1 = await wait_for_message_type(player1_ws, "world_init")
        initial_pos1 = init1.get("spawn_position", [64, 100, 64])
        print(f"✅ Alice spawned at: {initial_pos1}")
        
        # Skip chunks for player 1
        await skip_chunk_messages(player1_ws)
        
        # Player 2 joins
        print("\n👤 Player 2 (Bob) joining...")
        await send_json(player2_ws, "player_join", {"name": "Bob"})
        
        # Get initialization message  
        init2 = await wait_for_message_type(player2_ws, "world_init")
        initial_pos2 = init2.get("spawn_position", [64, 100, 64])
        print(f"✅ Bob spawned at: {initial_pos2}")
        
        # Skip chunks for player 2
        await skip_chunk_messages(player2_ws)
        
        # Let both players see each other
        await asyncio.sleep(1.0)
        
        print("\n🚶 Testing Player Movement with Debug Logging...")
        
        # Player 1 moves
        new_position1 = [initial_pos1[0] + 10, initial_pos1[1], initial_pos1[2] + 5]
        print(f"\n🔄 Alice moving from {initial_pos1} to {new_position1}")
        
        await send_json(player1_ws, "player_move", {
            "position": new_position1,
            "rotation": [45, 0]
        })
        
        # Wait for responses
        print("⏳ Waiting for server responses...")
        await asyncio.sleep(2.0)
        
        # Try to receive any pending messages
        try:
            while True:
                msg1 = await asyncio.wait_for(recv_json(player1_ws), timeout=0.5)
        except asyncio.TimeoutError:
            pass
            
        try:
            while True:
                msg2 = await asyncio.wait_for(recv_json(player2_ws), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        # Player 2 moves
        new_position2 = [initial_pos2[0] - 8, initial_pos2[1] + 3, initial_pos2[2] - 2]
        print(f"\n🔄 Bob moving from {initial_pos2} to {new_position2}")
        
        await send_json(player2_ws, "player_move", {
            "position": new_position2,
            "rotation": [90, 15]
        })
        
        # Wait for responses
        print("⏳ Waiting for server responses...")
        await asyncio.sleep(2.0)
        
        # Try to receive any pending messages
        try:
            while True:
                msg1 = await asyncio.wait_for(recv_json(player1_ws), timeout=0.5)
        except asyncio.TimeoutError:
            pass
            
        try:
            while True:
                msg2 = await asyncio.wait_for(recv_json(player2_ws), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        print("\n✅ Test completed! Check the server logs for debug output.")
        
        # Close connections
        await player1_ws.close()
        await player2_ws.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Note: This requires the server to be running separately
    print("📝 Make sure to start the server first with: python server.py")
    print("🔍 This test will demonstrate the debug logging system")
    asyncio.run(test_debug_system())