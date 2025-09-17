"""
Simple movement test that will actually show the movement debug system working.
"""

import asyncio
import websockets
import json

SERVER_URI = "ws://localhost:8765"

async def simple_movement_test():
    """Simple test that will trigger movement debug logs."""
    
    try:
        # Connect to server
        ws = await websockets.connect(SERVER_URI)
        print("✅ Connected to server")
        
        # Join as player
        join_msg = {"type": "player_join", "data": {"name": "DebugTester"}}
        await ws.send(json.dumps(join_msg))
        print("📤 Sent player_join")
        
        # Receive messages until we can send moves
        msg_count = 0
        while msg_count < 70:  # Skip init messages
            msg = await ws.recv()
            data = json.loads(msg)
            msg_count += 1
            if data["type"] == "player_list":
                print("✅ Ready to send movements")
                break
        
        # Now send some movements to trigger debug logs
        movements = [
            {"position": [64, 20, 64], "rotation": [0, 0]},
            {"position": [74, 20, 64], "rotation": [90, 0]},
            {"position": [74, 20, 74], "rotation": [180, 0]},
            {"position": [64, 20, 74], "rotation": [270, 0]},
            {"position": [64, 25, 64], "rotation": [0, 45]},
        ]
        
        for i, move_data in enumerate(movements, 1):
            print(f"📤 Sending movement {i}: {move_data['position']}")
            move_msg = {"type": "player_move", "data": move_data}
            await ws.send(json.dumps(move_msg))
            
            # Wait a bit and drain any response
            await asyncio.sleep(0.5)
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=0.1)
                    resp_data = json.loads(response)
                    if resp_data["type"] == "player_update":
                        print(f"📥 Received position confirmation: {resp_data['data']['position']}")
            except asyncio.TimeoutError:
                pass
        
        print("✅ Movement test completed! Check server logs for debug output:")
        print("   🚶 Look for 'PLAYER_MOVE DEBUG' entries")
        print("   📡 Look for 'Broadcasting position update' entries")
        print("   📊 Look for 'PLAYER DEBUG SUMMARY' entries")
        
        await ws.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 Running simple movement debug test")
    print("👀 Watch the server terminal for debug output!")
    asyncio.run(simple_movement_test())