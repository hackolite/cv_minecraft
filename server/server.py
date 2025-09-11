#!/usr/bin/env python3
"""
Minecraft-like Server
Handles WebSocket clients, maintains world state, manages player agents, broadcasts updates.
"""

import asyncio
import websockets
import json
import math
import random
import time
from collections import deque, defaultdict
from typing import Dict, List, Tuple, Optional, Set

# Import noise generation for terrain
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from noise_gen import NoiseGen

# Block type constants
GRASS = "GRASS"
SAND = "SAND" 
BRICK = "BRICK"
STONE = "STONE"
WOOD = "WOOD"
LEAF = "LEAF"
WATER = "WATER"

# Face directions for neighbor checking
FACES = [
    (0, 1, 0),   # top
    (0, -1, 0),  # bottom
    (-1, 0, 0),  # left
    (1, 0, 0),   # right
    (0, 0, 1),   # front
    (0, 0, -1),  # back
]

# Game constants
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50
PLAYER_HEIGHT = 2
WALKING_SPEED = 5
FLYING_SPEED = 15

# Server constants
TICK_RATE = 20  # Server ticks per second
UPDATE_RATE = 5  # World updates sent to clients per second


class Block:
    """Represents a block in the world"""
    def __init__(self, x: int, y: int, z: int, block_type: str):
        self.x = x
        self.y = y
        self.z = z
        self.block_type = block_type
        
    def to_dict(self):
        return {
            "pos": [self.x, self.y, self.z],
            "type": self.block_type
        }


class Player:
    """Represents a connected player agent"""
    def __init__(self, name: str, websocket):
        self.name = name
        self.websocket = websocket
        self.position = [30.0, 50.0, 80.0]  # Starting position
        self.rotation = [0.0, 0.0]  # horizontal, vertical rotation
        self.velocity = [0.0, 0.0, 0.0]  # velocity vector
        self.flying = False
        self.inventory = [BRICK, GRASS, SAND, WOOD, LEAF]
        self.selected_block = BRICK
        self.last_update = time.time()
        
    def to_dict(self):
        return {
            "name": self.name,
            "pos": self.position,
            "rotation": self.rotation,
            "flying": self.flying
        }


def normalize(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert floating point position to block coordinates"""
    x, y, z = position
    return int(math.floor(x)), int(math.floor(y)), int(math.floor(z))


def sectorize(position: Tuple[int, int, int]) -> Tuple[int, int]:
    """Convert block coordinates to sector coordinates"""
    x, y, z = position
    return x // 16, z // 16


class MinecraftServer:
    """Main server class managing the Minecraft-like world and players"""
    
    def __init__(self, world_size: int = 64, port: int = 8765):
        self.world_size = world_size
        self.port = port
        
        # World state
        self.world: Dict[Tuple[int, int, int], Block] = {}
        self.sectors: Dict[Tuple[int, int], List[Tuple[int, int, int]]] = defaultdict(list)
        
        # Connected players
        self.players: Dict[str, Player] = {}
        self.websockets: Set = set()
        
        # Server state
        self.running = False
        self.last_update = time.time()
        
        # Generate initial world
        self._generate_world()
        
    def _generate_world(self):
        """Generate the initial world terrain"""
        print(f"Generating world of size {self.world_size}x{self.world_size}...")
        
        gen = NoiseGen(452692)
        n = self.world_size
        s = 1  # step size
        
        # Generate height map
        height_map = {}
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map[(x, z)] = int(gen.getHeight(x, z))
        
        # Generate the world based on height map
        for x in range(0, n, s):
            for z in range(0, n, s):
                h = height_map[(x, z)]
                
                # Water level
                if h < 15:
                    self.add_block((x, h, z), SAND)
                    for y in range(h + 1, 15):
                        self.add_block((x, y, z), WATER)
                    continue
                    
                # Beach sand
                if h < 18:
                    self.add_block((x, h, z), SAND)
                else:
                    # Grass surface
                    self.add_block((x, h, z), GRASS)
                    
                # Underground stone
                for y in range(h - 1, 0, -1):
                    self.add_block((x, y, z), STONE)
                    
                # Maybe add trees
                if h > 20:
                    if random.randrange(0, 1000) > 990:
                        tree_height = random.randrange(5, 7)
                        # Tree trunk
                        for y in range(h + 1, h + tree_height):
                            self.add_block((x, y, z), WOOD)
                        # Tree leaves
                        leaf_h = h + tree_height
                        for lz in range(z - 2, z + 3):
                            for lx in range(x - 2, x + 3):
                                for ly in range(3):
                                    self.add_block((lx, leaf_h + ly, lz), LEAF)
        
        print(f"Generated {len(self.world)} blocks")
    
    def add_block(self, position: Tuple[int, int, int], block_type: str):
        """Add a block to the world"""
        x, y, z = position
        if position in self.world:
            self.remove_block(position)
            
        block = Block(x, y, z, block_type)
        self.world[position] = block
        self.sectors[sectorize(position)].append(position)
    
    def remove_block(self, position: Tuple[int, int, int]):
        """Remove a block from the world"""
        if position in self.world:
            del self.world[position]
            sector = sectorize(position)
            if position in self.sectors[sector]:
                self.sectors[sector].remove(position)
    
    def get_blocks_in_range(self, center: Tuple[float, float, float], radius: int = 50) -> List[Block]:
        """Get all blocks within a radius of a position"""
        cx, cy, cz = center
        blocks = []
        
        for (x, y, z), block in self.world.items():
            distance = math.sqrt((x - cx)**2 + (y - cy)**2 + (z - cz)**2)
            if distance <= radius:
                blocks.append(block)
                
        return blocks
    
    def hit_test(self, position: Tuple[float, float, float], vector: Tuple[float, float, float], 
                 max_distance: int = 8) -> Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]]]:
        """Line of sight search from current position"""
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
            
        return None, None
    
    def validate_position(self, position: Tuple[float, float, float]) -> bool:
        """Check if a position is valid (not inside blocks)"""
        x, y, z = position
        # Check if player would be inside any blocks
        for dy in [0, 1]:  # Check player height
            block_pos = normalize((x, y + dy, z))
            if block_pos in self.world:
                return False
        return True
    
    async def handle_client_message(self, websocket, message_data: dict, player: Player):
        """Handle a message from a client"""
        message_type = message_data.get("type")
        
        if message_type == "move":
            new_pos = message_data.get("pos", player.position)
            # Validate the new position
            if self.validate_position(new_pos):
                player.position = new_pos
                player.last_update = time.time()
                
        elif message_type == "rotate":
            player.rotation = message_data.get("rotation", player.rotation)
            
        elif message_type == "block":
            action = message_data.get("action")
            pos = message_data.get("pos")
            
            if action == "place" and pos:
                block_type = message_data.get("block_type", player.selected_block)
                block_pos = tuple(pos)
                if not self.validate_position([p + 0.5 for p in block_pos]):  # Check if placement is valid
                    self.add_block(block_pos, block_type)
                    
            elif action == "remove" and pos:
                block_pos = tuple(pos)
                self.remove_block(block_pos)
                
        elif message_type == "select_block":
            block_type = message_data.get("block_type")
            if block_type in player.inventory:
                player.selected_block = block_type
                
        elif message_type == "chat":
            message = message_data.get("message", "")
            # Broadcast chat message to all players
            chat_msg = {
                "type": "chat",
                "player": player.name,
                "message": message
            }
            await self.broadcast_message(chat_msg)
    
    async def handle_client(self, websocket, path):
        """Handle a new client connection"""
        player = None
        try:
            self.websockets.add(websocket)
            print(f"New client connected from {websocket.remote_address}")
            
            # Wait for join message
            join_message = await websocket.recv()
            join_data = json.loads(join_message)
            
            if join_data.get("type") != "join":
                await websocket.send(json.dumps({"type": "error", "message": "Expected join message"}))
                return
                
            player_name = join_data.get("name", f"Player{len(self.players)}")
            
            # Create player
            player = Player(player_name, websocket)
            self.players[player_name] = player
            
            print(f"Player {player_name} joined the game")
            
            # Send initial world state
            await self.send_world_update(websocket, player)
            
            # Send welcome message
            welcome_msg = {
                "type": "welcome",
                "name": player_name,
                "position": player.position
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Handle client messages
            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    await self.handle_client_message(websocket, message_data, player)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {player_name}: {message}")
                except Exception as e:
                    print(f"Error handling message from {player_name}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # Clean up
            self.websockets.discard(websocket)
            if player and player.name in self.players:
                print(f"Player {player.name} left the game")
                del self.players[player.name]
    
    async def send_world_update(self, websocket, player: Player):
        """Send world state update to a specific client"""
        # Get blocks near the player
        blocks = self.get_blocks_in_range(player.position, radius=50)
        
        update_msg = {
            "type": "world_update",
            "blocks": [block.to_dict() for block in blocks],
            "player": player.to_dict()
        }
        
        try:
            await websocket.send(json.dumps(update_msg))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected clients"""
        if self.websockets:
            message_str = json.dumps(message)
            # Send to all connected clients
            disconnected = []
            for websocket in self.websockets:
                try:
                    await websocket.send(message_str)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.append(websocket)
            
            # Clean up disconnected clients
            for websocket in disconnected:
                self.websockets.discard(websocket)
    
    async def game_loop(self):
        """Main game loop that sends regular updates"""
        while self.running:
            try:
                # Send updates to all players
                current_time = time.time()
                
                if current_time - self.last_update >= 1.0 / UPDATE_RATE:
                    # Create player list for broadcast
                    players_data = [player.to_dict() for player in self.players.values()]
                    
                    update_msg = {
                        "type": "update",
                        "players": players_data,
                        "timestamp": current_time
                    }
                    
                    await self.broadcast_message(update_msg)
                    self.last_update = current_time
                
                # Sleep until next tick
                await asyncio.sleep(1.0 / TICK_RATE)
                
            except Exception as e:
                print(f"Error in game loop: {e}")
                await asyncio.sleep(1.0)
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        print(f"Starting Minecraft server on port {self.port}...")
        
        # Start the WebSocket server
        start_server = websockets.serve(self.handle_client, "localhost", self.port)
        
        # Start the game loop
        game_task = asyncio.create_task(self.game_loop())
        
        print(f"Server running on ws://localhost:{self.port}")
        print("Waiting for clients to connect...")
        
        # Run both the server and game loop
        await asyncio.gather(start_server, game_task)
    
    def stop(self):
        """Stop the server"""
        self.running = False


async def main():
    """Main entry point"""
    server = MinecraftServer(world_size=64)
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("Server shutting down...")
        server.stop()


if __name__ == "__main__":
    asyncio.run(main())