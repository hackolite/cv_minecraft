#!/usr/bin/env python3
"""
Demo script showing the connection reuse fix in action.
Run this with the server running to see how player sessions are preserved.
"""

import asyncio
import websockets
import json
import time

async def demo_connection_reuse():
    """Demonstrate that connections are now properly reused"""
    
    print("🎮 Connection Reuse Demo")
    print("=" * 50)
    print("This demo shows how the server now reuses player sessions")
    print("instead of creating new ones for each reconnection.\n")
    
    player_name = "DemoPlayer"
    server_url = "ws://localhost:8765"
    
    # First connection
    print("📡 First connection (creates new session)...")
    websocket1 = await websockets.connect(server_url)
    
    join_msg = {"type": "join", "name": player_name}
    await websocket1.send(json.dumps(join_msg))
    
    welcome1 = await websocket1.recv()
    print(f"✅ Connected! Server response: {json.loads(welcome1)['type']}")
    
    # Set a specific position
    position = [42.5, 55.0, 123.7]
    move_msg = {"type": "move", "pos": position, "rotation": [45.0, 0.0]}
    await websocket1.send(json.dumps(move_msg))
    print(f"📍 Set position to: {position}")
    
    # Disconnect
    await websocket1.close()
    print("🔌 Disconnected from server")
    print("   📝 Check server logs: should show 'session preserved for reconnection'")
    
    await asyncio.sleep(2)
    
    # Second connection - should reuse session
    print("\n📡 Reconnection (reuses existing session)...")
    websocket2 = await websockets.connect(server_url)
    
    await websocket2.send(json.dumps(join_msg))
    welcome2 = await websocket2.recv()
    welcome2_data = json.loads(welcome2)
    
    print(f"✅ Reconnected! Server response: {welcome2_data['type']}")
    print("   📝 Check server logs: should show 'reconnected (reusing existing session)'")
    
    # Check if position was preserved
    if 'player' in welcome2_data:
        server_position = welcome2_data['player'].get('pos', [])
        print(f"📍 Server position: {server_position}")
        
        if server_position == position:
            print("🎉 SUCCESS! Position preserved across reconnection!")
        else:
            print("❌ Position not preserved (unexpected)")
    else:
        print("ℹ️  Position data not in welcome message")
    
    await websocket2.close()
    print("🔌 Disconnected from server")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed!")
    print("🔍 Check the server console to see the difference:")
    print("   • First connection: 'joined the game (new session)'")
    print("   • Reconnection: 'reconnected (reusing existing session)'")
    print("\n💡 This solves the issue: 'a chaque fois, une nouvelle connexion est mise en place'")
    print("   (each time, a new connection is established)")

async def main():
    try:
        await demo_connection_reuse()
    except ConnectionRefusedError:
        print("❌ Cannot connect to server!")
        print("🔧 Make sure the server is running: python3 server/server.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())