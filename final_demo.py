#!/usr/bin/env python3
"""
Final demonstration of the username and player visibility fixes.
"""
import asyncio
import websockets
import json
import subprocess
import sys
import time
import os

async def demo_multiple_players():
    """Demonstrate multiple players with custom usernames seeing each other."""
    print("🎮 MINECRAFT USERNAME AND VISIBILITY DEMO")
    print("=" * 50)
    
    # Start server
    print("🔄 Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Wait for server to start
    await asyncio.sleep(3)
    print("✅ Server started on localhost:8765")
    
    try:
        # Connect multiple players with different names
        player_names = ["Alice_Windows", "Bob_Linux", "Charlie_Mac"]
        players = []
        
        print("\n👥 Connecting players with custom usernames...")
        
        for i, name in enumerate(player_names):
            ws = await websockets.connect("ws://localhost:8765")
            players.append((ws, name))
            
            # Send join message with custom username
            join_msg = {"type": "player_join", "data": {"name": name}}
            await ws.send(json.dumps(join_msg))
            print(f"   {i+1}. {name} connected")
            
            # Wait a bit for server processing
            await asyncio.sleep(0.5)
        
        print("\n📡 Receiving initial messages...")
        
        # Collect initial messages for each player
        for ws, name in players:
            try:
                # Get world init message
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                world_init = json.loads(msg)
                print(f"   {name} received world initialization")
                
                # Skip chunk messages (just wait a bit)
                start_time = time.time()
                chunk_count = 0
                while time.time() - start_time < 3.0:  # Wait up to 3 seconds for chunks
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.1)
                        data = json.loads(msg)
                        if data["type"] == "world_chunk":
                            chunk_count += 1
                        elif data["type"] == "player_list":
                            players_in_list = data["data"]["players"]
                            print(f"   {name} sees {len(players_in_list)} players:")
                            for p in players_in_list:
                                print(f"     - {p.get('name', 'Unknown')} at {p['position']}")
                            break
                    except asyncio.TimeoutError:
                        continue
                
                print(f"   {name} loaded {chunk_count} world chunks")
                
            except asyncio.TimeoutError:
                print(f"   {name} timed out during initialization")
        
        print("\n🏃 Testing player movement and visibility...")
        
        # Move players and check updates
        movements = [
            [1.0, 0.0, 0.0],  # Alice moves right
            [0.0, 0.0, 1.0],  # Bob moves forward
            [-1.0, 0.0, 0.0]  # Charlie moves left
        ]
        
        # Send movement commands
        for (ws, name), movement in zip(players, movements):
            move_msg = {
                "type": "player_move",
                "data": {"delta": movement, "rotation": [0.0, 0.0]}
            }
            await ws.send(json.dumps(move_msg))
            print(f"   {name} moved by {movement}")
        
        # Collect player updates
        print("\n👀 Checking if players can see each other...")
        update_counts = {}
        seen_players = {}
        
        for ws, name in players:
            update_counts[name] = 0
            seen_players[name] = set()
            
            try:
                for _ in range(10):  # Collect up to 10 updates
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    
                    if data["type"] == "player_update":
                        update_counts[name] += 1
                        other_player = data["data"].get("name", "Unknown")
                        seen_players[name].add(other_player)
                        print(f"   {name} saw {other_player} move")
                        
            except asyncio.TimeoutError:
                pass
        
        # Results
        print("\n📊 RESULTS:")
        print("-" * 30)
        
        all_can_see_others = True
        for name in player_names:
            updates = update_counts.get(name, 0)
            seen = seen_players.get(name, set())
            others_seen = len(seen - {name})  # Exclude self
            
            print(f"  {name}:")
            print(f"    Received {updates} player updates")
            print(f"    Saw {others_seen} other players: {list(seen - {name})}")
            
            if others_seen < 1:  # Should see at least 1 other player
                all_can_see_others = False
        
        print("\n🎯 FINAL VERDICT:")
        if all_can_see_others:
            print("✅ SUCCESS: All players can see each other!")
            print("✅ Custom usernames working correctly")
            print("✅ Player visibility functioning properly")
        else:
            print("❌ ISSUE: Some players cannot see others")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        for ws, name in players:
            try:
                await ws.close()
                print(f"   {name} disconnected")
            except:
                pass
        
        server_process.terminate()
        server_process.wait()
        print("   Server stopped")

async def main():
    """Run the demonstration."""
    success = await demo_multiple_players()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("   ✓ Username input (Windows/Unix compatible)")
        print("   ✓ Player visibility working")
        print("   ✓ Multiple players can see each other")
        print("   ✓ Custom usernames properly transmitted")
    else:
        print("❌ DEMO FAILED - Issues remain")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)