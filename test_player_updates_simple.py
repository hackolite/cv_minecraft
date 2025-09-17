#!/usr/bin/env python3
"""
Simple test specifically for player updates after our fix.
"""

import asyncio
import websockets
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def test_two_players_see_each_other():
    """Test that two players can see each other's updates."""
    logging.info("🧪 Testing that two players can see each other...")
    
    # Connect two players
    ws1 = websockets.connect(SERVER_URI)
    ws2 = websockets.connect(SERVER_URI)
    
    async with ws1 as client1, ws2 as client2:
        # Player 1 joins
        await client1.send(json.dumps({"type": "player_join", "data": {"name": "Player1"}}))
        
        # Player 2 joins  
        await client2.send(json.dumps({"type": "player_join", "data": {"name": "Player2"}}))
        
        # Skip initial messages (world_init, chunks, etc.)
        player1_updates = []
        player2_updates = []
        
        async def collect_player_updates(ws, updates_list, player_name):
            try:
                while len(updates_list) < 5:  # Collect a few updates
                    message_str = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    message = json.loads(message_str)
                    
                    if message["type"] == "player_update":
                        updates_list.append(message["data"])
                        other_player_name = message["data"].get("name", "Unknown")
                        logging.info(f"👤 {player_name} received update from {other_player_name}")
                    elif message["type"] == "player_list":
                        players = message["data"]["players"]
                        logging.info(f"📋 {player_name} received player list with {len(players)} players")
                        for p in players:
                            logging.info(f"   - {p.get('name', 'Unknown')} at {p['position']}")
            except asyncio.TimeoutError:
                logging.info(f"⏰ {player_name} timed out after collecting {len(updates_list)} updates")
        
        # Send a movement to trigger updates
        await client1.send(json.dumps({
            "type": "player_move", 
            "data": {"position": [65.0, 100.0, 64.0], "rotation": [0.0, 0.0]}
        }))
        
        await client2.send(json.dumps({
            "type": "player_move", 
            "data": {"position": [64.0, 100.0, 65.0], "rotation": [45.0, 0.0]}
        }))
        
        # Collect updates for both players
        await asyncio.gather(
            collect_player_updates(client1, player1_updates, "Player1"),
            collect_player_updates(client2, player2_updates, "Player2")
        )
        
        logging.info(f"📊 Results:")
        logging.info(f"   Player1 received {len(player1_updates)} player updates")
        logging.info(f"   Player2 received {len(player2_updates)} player updates")
        
        # Check if players saw each other
        player1_saw_player2 = any(update.get("name") == "Player2" for update in player1_updates)
        player2_saw_player1 = any(update.get("name") == "Player1" for update in player2_updates)
        
        logging.info(f"   Player1 saw Player2: {player1_saw_player2}")
        logging.info(f"   Player2 saw Player1: {player2_saw_player1}")
        
        if player1_saw_player2 and player2_saw_player1:
            logging.info("✅ SUCCESS: Both players can see each other!")
            return True
        else:
            logging.error("❌ FAILED: Players cannot see each other")
            return False

async def main():
    """Run the test."""
    success = await test_two_players_see_each_other()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🎯 Final result: {'PASS' if result else 'FAIL'}")