#!/usr/bin/env python3
"""
Test to debug player visibility issues.
Connects two clients and checks if they can see each other.
"""

import asyncio
import websockets
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

async def send_json(ws, message_type, data):
    """Send a JSON message to the server."""
    message = {"type": message_type, "data": data}
    await ws.send(json.dumps(message))
    logging.info(f"Sent -> {message}")

async def recv_json(ws):
    """Receive and parse a JSON message from the server."""
    message_str = await ws.recv()
    message = json.loads(message_str)
    logging.info(f"Received <- {message}")
    return message

async def connect_and_monitor_player(username, duration=10):
    """Connect a player and monitor their view of other players."""
    logging.info(f"🔌 Connecting {username}...")
    
    async with websockets.connect(SERVER_URI) as ws:
        # Join the game
        await send_json(ws, "player_join", {"name": username})
        
        # Wait for world initialization and chunks
        world_init_msg = await recv_json(ws)
        assert world_init_msg["type"] == "world_init", f"Expected world_init, got {world_init_msg['type']}"
        
        # Skip through chunks until we get player_list
        while True:
            try:
                message = await asyncio.wait_for(recv_json(ws), timeout=2.0)
                if message["type"] == "player_list":
                    # Found player list, now start monitoring
                    break
            except asyncio.TimeoutError:
                logging.warning(f"{username} timed out waiting for player_list")
                break
        
        other_players_seen = set()
        player_updates_received = 0
        player_lists_received = 0
        
        # Monitor for the specified duration
        end_time = time.time() + duration
        
        try:
            while time.time() < end_time:
                message = await asyncio.wait_for(recv_json(ws), timeout=1.0)
                
                if message["type"] == "player_update":
                    player_updates_received += 1
                    player_id = message["data"]["id"]
                    player_name = message["data"].get("name", "Unknown")
                    other_players_seen.add(f"{player_name} ({player_id[:8]})")
                    logging.info(f"👥 {username} saw player update for: {player_name}")
                
                elif message["type"] == "player_list":
                    player_lists_received += 1
                    players = message["data"]["players"]
                    logging.info(f"👥 {username} received player list with {len(players)} players:")
                    for player in players:
                        player_name = player.get("name", "Unknown")
                        player_id = player["id"]
                        logging.info(f"  - {player_name} ({player_id[:8]})")
        
        except asyncio.TimeoutError:
            # Normal - we're just monitoring for a specific duration
            pass
        
        logging.info(f"📊 {username} summary:")
        logging.info(f"  - Player updates received: {player_updates_received}")
        logging.info(f"  - Player lists received: {player_lists_received}")
        logging.info(f"  - Other players seen: {len(other_players_seen)}")
        for player in other_players_seen:
            logging.info(f"    * {player}")
        
        return {
            "username": username,
            "player_updates": player_updates_received,
            "player_lists": player_lists_received,
            "other_players": other_players_seen
        }

async def test_player_visibility():
    """Test if two players can see each other."""
    logging.info("🧪 Testing player visibility...")
    
    # Start both players simultaneously
    results = await asyncio.gather(
        connect_and_monitor_player("Alice", 8),
        connect_and_monitor_player("Bob", 8),
        return_exceptions=True
    )
    
    alice_result, bob_result = results
    
    # Handle any exceptions
    if isinstance(alice_result, Exception):
        logging.error(f"Alice connection failed: {alice_result}")
        return False
    if isinstance(bob_result, Exception):
        logging.error(f"Bob connection failed: {bob_result}")
        return False
    
    # Check if Alice could see Bob
    alice_saw_bob = any("Bob" in player for player in alice_result["other_players"])
    bob_saw_alice = any("Alice" in player for player in bob_result["other_players"])
    
    logging.info("🔍 Visibility Analysis:")
    logging.info(f"  Alice saw Bob: {alice_saw_bob}")
    logging.info(f"  Bob saw Alice: {bob_saw_alice}")
    
    if alice_saw_bob and bob_saw_alice:
        logging.info("✅ Both players can see each other!")
        return True
    else:
        logging.error("❌ Players cannot see each other!")
        if not alice_saw_bob:
            logging.error("  - Alice cannot see Bob")
        if not bob_saw_alice:
            logging.error("  - Bob cannot see Alice")
        return False

async def main():
    """Run the visibility test."""
    success = await test_player_visibility()
    
    if success:
        logging.info("🎉 Player visibility test PASSED!")
    else:
        logging.error("💥 Player visibility test FAILED!")
        logging.info("🔧 Issue: Players are not seeing each other in the game")

if __name__ == "__main__":
    asyncio.run(main())