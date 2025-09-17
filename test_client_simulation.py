#!/usr/bin/env python3
"""
Test script to verify that players can see each other in the client.
This script simulates the client behavior without opening a window.
"""

import asyncio
import websockets
import json
import logging
import time
from protocol import Message, MessageType, PlayerState

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

SERVER_URI = "ws://localhost:8765"

class MockClientModel:
    """Mock client model to test player rendering logic."""
    
    def __init__(self):
        self.other_players = {}
        self.player_colors = {}
    
    def get_or_create_player_color(self, player_id):
        """Generate a random color for a player."""
        if player_id not in self.player_colors:
            import random
            self.player_colors[player_id] = (
                random.uniform(0.3, 1.0),
                random.uniform(0.3, 1.0), 
                random.uniform(0.3, 1.0)
            )
        return self.player_colors[player_id]
    
    def remove_player(self, player_id):
        """Remove a player."""
        self.other_players.pop(player_id, None)
        self.player_colors.pop(player_id, None)

async def test_client_simulation():
    """Simulate client behavior to test player visibility."""
    logging.info("🎮 Simulating client behavior...")
    
    model = MockClientModel()
    my_player_id = None
    
    async with websockets.connect(SERVER_URI) as ws:
        # Join the game
        join_msg = {"type": "player_join", "data": {"name": "TestClient"}}
        await ws.send(json.dumps(join_msg))
        
        logging.info("📡 Connected to server and joined game")
        
        # Process messages for a while
        messages_processed = 0
        start_time = time.time()
        
        while time.time() - start_time < 10 and messages_processed < 100:  # 10 seconds or 100 messages
            try:
                message_str = await asyncio.wait_for(ws.recv(), timeout=1.0)
                message_data = json.loads(message_str)
                messages_processed += 1
                
                # Extract player_id if present
                if "player_id" in message_data and my_player_id is None:
                    my_player_id = message_data["player_id"]
                    logging.info(f"🆔 My player ID: {my_player_id}")
                
                message_type = message_data["type"]
                data = message_data.get("data", {})
                
                # Simulate client message handling
                if message_type == "player_update":
                    # Update other player positions
                    player_id = data["id"]
                    
                    if player_id != my_player_id:  # Don't update our own position
                        model.other_players[player_id] = PlayerState.from_dict(data)
                        color = model.get_or_create_player_color(player_id)
                        logging.info(f"👤 Updated player {data.get('name', 'Unknown')} at {data['position']} (color: {color})")
                
                elif message_type == "player_list":
                    # Update player list
                    players = data.get("players", [])
                    
                    # Get current player IDs from server
                    current_player_ids = {p["id"] for p in players if p["id"] != my_player_id}
                    
                    # Remove players no longer in list
                    for player_id in list(model.other_players.keys()):
                        if player_id not in current_player_ids:
                            model.remove_player(player_id)
                            logging.info(f"🚪 Removed player {player_id}")
                    
                    # Update/add current players
                    for player_data in players:
                        player = PlayerState.from_dict(player_data)
                        if player.id != my_player_id:
                            model.other_players[player.id] = player
                            color = model.get_or_create_player_color(player.id)
                            logging.info(f"📋 Player in list: {player.name} at {player.position} (color: {color})")
                
                elif message_type == "world_init":
                    logging.info(f"🌍 World initialized: {data}")
                    
                elif message_type == "world_chunk":
                    # Don't log every chunk, too verbose
                    pass
                    
                elif message_type == "world_update":
                    blocks = data.get("blocks", [])
                    logging.info(f"🧱 World update with {len(blocks)} block changes")
                
            except asyncio.TimeoutError:
                # Check if we should send a movement to trigger updates
                if time.time() - start_time > 5:  # After 5 seconds, send movement
                    move_msg = {
                        "type": "player_move",
                        "data": {"position": [65.0, 100.0, 64.0], "rotation": [45.0, 0.0]}
                    }
                    await ws.send(json.dumps(move_msg))
                    logging.info("🏃 Sent movement update")
        
        # Report final state
        logging.info(f"📊 Final state:")
        logging.info(f"   Messages processed: {messages_processed}")
        logging.info(f"   Other players visible: {len(model.other_players)}")
        
        for player_id, player in model.other_players.items():
            color = model.get_or_create_player_color(player_id)
            logging.info(f"   👤 {player.name} at {player.position} (color: {color})")
        
        if len(model.other_players) > 0:
            logging.info("✅ SUCCESS: Other players are visible and would be rendered!")
            return True
        else:
            logging.warning("⚠️  No other players visible. Try running with multiple clients.")
            return False

async def main():
    """Run the client simulation test."""
    result = await test_client_simulation()
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🎯 Final result: {'PASS' if result else 'NO OTHER PLAYERS'}")