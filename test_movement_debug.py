"""
Test specifically focused on player movement debug and broadcast functionality.
This test will trigger actual player movements to demonstrate the debug system.
"""

import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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
    print(f"📤 CLIENT SENT: {msg_type} - {data}")

async def recv_json(ws):
    """Receive and parse a JSON message from the websocket."""
    msg = await ws.recv()
    data = json.loads(msg)
    if data["type"] in ["player_update", "player_move"]:
        print(f"📥 CLIENT RECEIVED: {data['type']} - Player: {data['data'].get('id', 'unknown')[:8]} at {data['data'].get('position', 'unknown')}")
    return data

async def setup_player(ws, name):
    """Set up a player and return their ID and initial position."""
    await send_json(ws, "player_join", {"name": name})
    
    # Get world_init
    init_msg = await recv_json(ws)
    while init_msg["type"] != "world_init":
        init_msg = await recv_json(ws)
    
    player_id = init_msg.get("player_id")
    spawn_pos = init_msg.get("spawn_position", [64, 100, 64])
    
    # Skip chunks until player_list
    while True:
        msg = await recv_json(ws)
        if msg["type"] == "player_list":
            break
    
    print(f"✅ Player {name} setup complete: ID={player_id[:8]}, spawn={spawn_pos}")
    return player_id, spawn_pos

async def test_movement_debug():
    """Test that demonstrates movement debugging specifically."""
    
    print("🚀 Starting MOVEMENT DEBUG test...")
    
    try:
        # Connect two players
        print("\n🔗 Connecting players...")
        alice_ws = await websockets.connect(SERVER_URI)
        bob_ws = await websockets.connect(SERVER_URI)
        
        # Set up players
        alice_id, alice_pos = await setup_player(alice_ws, "Alice")
        bob_id, bob_pos = await setup_player(bob_ws, "Bob")
        
        # Give some time for both players to see each other
        await asyncio.sleep(1.0)
        
        print(f"\n🚶 TESTING MOVEMENT DEBUG SYSTEM")
        print(f"   Check server logs for detailed movement debug output!")
        
        # Test 1: Alice moves significantly
        print(f"\n🔄 Test 1: Alice big movement")
        new_alice_pos = [alice_pos[0] + 20, alice_pos[1] + 5, alice_pos[2] + 15]
        await send_json(alice_ws, "player_move", {
            "position": new_alice_pos,
            "rotation": [45, 30]
        })
        
        # Collect responses
        await asyncio.sleep(1.0)
        try:
            while True:
                await asyncio.wait_for(recv_json(alice_ws), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        try:
            while True:
                await asyncio.wait_for(recv_json(bob_ws), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        # Test 2: Bob moves in different direction
        print(f"\n🔄 Test 2: Bob movement")
        new_bob_pos = [bob_pos[0] - 10, bob_pos[1] + 2, bob_pos[2] - 8]
        await send_json(bob_ws, "player_move", {
            "position": new_bob_pos,
            "rotation": [180, 0]
        })
        
        # Collect responses
        await asyncio.sleep(1.0)
        try:
            while True:
                await asyncio.wait_for(recv_json(alice_ws), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        try:
            while True:
                await asyncio.wait_for(recv_json(bob_ws), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        
        # Test 3: Rapid movements to stress test debug system
        print(f"\n🔄 Test 3: Rapid movements")
        for i in range(5):
            rapid_pos = [new_alice_pos[0] + i*2, new_alice_pos[1], new_alice_pos[2] + i*2]
            await send_json(alice_ws, "player_move", {
                "position": rapid_pos,
                "rotation": [i * 45, 0]
            })
            await asyncio.sleep(0.3)  # Small delay between moves
            
            # Drain any responses
            try:
                while True:
                    await asyncio.wait_for(recv_json(alice_ws), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            try:
                while True:
                    await asyncio.wait_for(recv_json(bob_ws), timeout=0.1)
            except asyncio.TimeoutError:
                pass
        
        print(f"\n✅ Movement test completed!")
        print(f"📊 Check server logs for:")
        print(f"   🚶 PLAYER_MOVE DEBUG entries with position details")
        print(f"   📡 Broadcasting debug info")
        print(f"   📊 PLAYER DEBUG SUMMARY with updated positions")
        
        # Clean up
        await alice_ws.close()
        await bob_ws.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("📝 Make sure the server is running with: python server.py")
    print("🔍 This test will demonstrate the movement debug logging system")
    print("👀 Watch the server terminal for detailed debug output!")
    asyncio.run(test_movement_debug())