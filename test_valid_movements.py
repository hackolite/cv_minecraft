"""
Test with smaller movements that won't trigger anti-cheat to see full debug system.
"""

import asyncio
import websockets
import json

SERVER_URI = "ws://localhost:8765"

async def test_valid_movements():
    """Test with small movements that will be allowed."""
    
    try:
        # Connect and join
        ws = await websockets.connect(SERVER_URI)
        print("✅ Connected to server")
        
        join_msg = {"type": "player_join", "data": {"name": "ValidMover"}}
        await ws.send(json.dumps(join_msg))
        print("📤 Sent player_join")
        
        # Skip init messages
        msg_count = 0
        while msg_count < 70:
            msg = await ws.recv()
            data = json.loads(msg)
            msg_count += 1
            if data["type"] == "player_list":
                print("✅ Ready to send valid movements")
                break
        
        # Start with spawn position and make small valid movements
        current_pos = [64, 100, 64]  # Default spawn
        
        # Small valid movements (< 50 unit distance)
        movements = [
            {"position": [current_pos[0] + 5, current_pos[1], current_pos[2]], "rotation": [45, 0]},
            {"position": [current_pos[0] + 10, current_pos[1], current_pos[2] + 5], "rotation": [90, 0]},
            {"position": [current_pos[0] + 8, current_pos[1] - 2, current_pos[2] + 8], "rotation": [135, 15]},
            {"position": [current_pos[0] + 3, current_pos[1] - 1, current_pos[2] + 12], "rotation": [180, 0]},
            {"position": [current_pos[0] - 2, current_pos[1] + 1, current_pos[2] + 10], "rotation": [225, -10]},
        ]
        
        for i, move_data in enumerate(movements, 1):
            print(f"📤 Valid movement {i}: {move_data['position']}")
            move_msg = {"type": "player_move", "data": move_data}
            await ws.send(json.dumps(move_msg))
            
            # Wait and check for responses
            await asyncio.sleep(1.0)
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=0.2)
                    resp_data = json.loads(response)
                    if resp_data["type"] == "player_update":
                        print(f"📥 Position confirmed: {resp_data['data']['position']}")
            except asyncio.TimeoutError:
                pass
            
            # Update current position for next movement
            current_pos = move_data["position"]
        
        print("✅ Valid movement test completed!")
        print("🔍 Check server logs for:")
        print("   🚶 PLAYER_MOVE DEBUG entries (should show successful movements)")
        print("   📡 Broadcasting entries (should show successful broadcasts)")
        print("   📊 No anti-cheat warnings (movements should be accepted)")
        
        await ws.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 Testing valid small movements to see full debug system")
    asyncio.run(test_valid_movements())