#!/usr/bin/env python3
"""
Simple multiplayer test that creates multiple AI clients to demonstrate the server functionality
"""

import asyncio
import websockets
import json
import time
import random

class TestAIClient:
    """Simple AI client for testing multiplayer functionality"""
    
    def __init__(self, name):
        self.name = name
        self.position = [30 + random.randint(-10, 10), 50, 80 + random.randint(-10, 10)]
        self.running = True
        
    async def connect_and_play(self):
        """Connect to server and perform simple AI actions"""
        try:
            print(f"[{self.name}] Connecting to server...")
            websocket = await websockets.connect("ws://localhost:8765")
            
            # Join the game
            join_msg = {"type": "join", "name": self.name}
            await websocket.send(json.dumps(join_msg))
            
            # Wait for welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"[{self.name}] Connected! Received: {welcome_data['type']}")
            
            # Start AI behavior
            await self.ai_behavior(websocket)
            
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
    
    async def ai_behavior(self, websocket):
        """Simple AI behavior: move around and place blocks"""
        move_count = 0
        
        try:
            while self.running and move_count < 20:
                # Random movement
                self.position[0] += random.uniform(-1, 1)
                self.position[2] += random.uniform(-1, 1)
                
                # Send movement
                move_msg = {
                    "type": "move", 
                    "pos": self.position,
                    "rotation": [random.uniform(0, 360), 0]
                }
                await websocket.send(json.dumps(move_msg))
                
                # Sometimes place a block
                if random.random() < 0.3:
                    block_pos = [
                        int(self.position[0] + random.randint(-2, 2)),
                        int(self.position[1]),
                        int(self.position[2] + random.randint(-2, 2))
                    ]
                    
                    block_msg = {
                        "type": "block",
                        "action": "place",
                        "pos": block_pos,
                        "block_type": random.choice(["BRICK", "WOOD", "SAND"])
                    }
                    await websocket.send(json.dumps(block_msg))
                    print(f"[{self.name}] Placed block at {block_pos}")
                
                # Sometimes send chat
                if random.random() < 0.1:
                    chat_msg = {
                        "type": "chat",
                        "message": f"Hello from {self.name}! Move {move_count}"
                    }
                    await websocket.send(json.dumps(chat_msg))
                
                move_count += 1
                await asyncio.sleep(0.5)  # Move every 0.5 seconds
                
            print(f"[{self.name}] Finished AI routine")
            await websocket.close()
            
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}] Connection closed")
        except Exception as e:
            print(f"[{self.name}] AI error: {e}")

async def main():
    """Create multiple AI clients to test multiplayer"""
    print("🤖 Starting multiplayer AI test...")
    print("Make sure the server is running: python3 server/server.py")
    print()
    
    # Wait a moment for user to read
    await asyncio.sleep(2)
    
    # Create AI clients
    ai_clients = [
        TestAIClient("Alice_AI"),
        TestAIClient("Bob_AI"),
        TestAIClient("Charlie_AI")
    ]
    
    # Run all AI clients concurrently
    tasks = [client.connect_and_play() for client in ai_clients]
    
    print("🚀 Starting AI clients...")
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print("🏁 AI test completed!")

if __name__ == "__main__":
    asyncio.run(main())