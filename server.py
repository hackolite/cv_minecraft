"""
Minecraft Server - Manages game world and client connections.
Extracted from the monolithic minecraft.py to handle server-side logic.
"""

import asyncio
import websockets
import json
import uuid
import time
from typing import Dict, Set, List, Tuple, Optional
from collections import deque

from protocol import *
from noise_gen import NoiseGen

# Import block texture mappings from original minecraft.py
def tex_coord(x, y, n=4):
    """ Return the bounding vertices of the texture square. """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    """ Return a list of the texture squares for the top, bottom and side. """
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

# Block texture definitions
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))

# Block type to texture mapping
BLOCK_TEXTURES = {
    BlockType.GRASS: GRASS,
    BlockType.SAND: SAND,
    BlockType.BRICK: BRICK,
    BlockType.STONE: STONE,
    BlockType.WOOD: WOOD,
    BlockType.LEAF: LEAF,
    BlockType.WATER: WATER
}

# Texture to block type mapping (reverse lookup)
TEXTURE_TO_BLOCK = {tuple(v): k for k, v in BLOCK_TEXTURES.items()}

# Size of sectors used to ease block loading.
SECTOR_SIZE = 16

def normalize(position):
    """Accepts position of arbitrary precision and returns the block containing that position."""
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    """Returns a tuple representing the sector for the given position."""
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class GameWorld:
    """Manages the game world state on the server side."""
    
    def __init__(self):
        # A mapping from position to the block type at that position
        self.world = {}
        # Mapping from sector to a list of positions inside that sector
        self.sectors = {}
        self._initialize_world()
    
    def _initialize_world(self):
        """Initialize the world by placing all the blocks."""
        gen = NoiseGen(452692)
        n = 128  # size of the world
        s = 1    # step size
        
        # Generate height map
        height_map = []
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map.append(0)
        
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map[z + x * n] = int(gen.getHeight(x, z))
        
        # Generate the world
        for x in range(0, n, s):
            for z in range(0, n, s):
                h = height_map[z + x * n]
                
                if h < 15:
                    self.add_block((x, h, z), BlockType.SAND)
                    for y in range(h, 15):
                        self.add_block((x, y, z), BlockType.WATER)
                    continue
                
                if h < 18:
                    self.add_block((x, h, z), BlockType.SAND)
                else:
                    self.add_block((x, h, z), BlockType.GRASS)
                
                # Add stone layers below surface
                for y in range(h - 1, 0, -1):
                    self.add_block((x, y, z), BlockType.STONE)
                
                # Maybe add tree at this (x, z)
                if h > 20:
                    import random
                    if random.randrange(0, 1000) > 990:
                        tree_height = random.randrange(5, 7)
                        # Tree trunk
                        for y in range(h + 1, h + tree_height):
                            self.add_block((x, y, z), BlockType.WOOD)
                        # Tree leaves
                        leaf_h = h + tree_height
                        for lz in range(z - 2, z + 3):
                            for lx in range(x - 2, x + 3):
                                for ly in range(3):
                                    self.add_block((lx, leaf_h + ly, lz), BlockType.LEAF)
    
    def add_block(self, position: Tuple[int, int, int], block_type: str) -> bool:
        """Add a block to the world."""
        if position in self.world:
            return False  # Block already exists
        
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        return True
    
    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Remove a block from the world."""
        if position not in self.world:
            return False  # Block doesn't exist
        
        # Don't allow removing stone blocks (like in original)
        if self.world[position] == BlockType.STONE:
            return False
        
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        return True
    
    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        """Get the block type at a position."""
        return self.world.get(position)
    
    def get_world_data(self) -> Dict[str, Any]:
        """Get world data for client initialization."""
        return {
            "world_size": 128,
            "spawn_position": [30, 50, 80]
        }
    
    def get_world_chunk(self, chunk_x: int, chunk_z: int, chunk_size: int = 16) -> Dict[str, Any]:
        """Get a chunk of world data."""
        world_blocks = {}
        start_x = chunk_x * chunk_size
        start_z = chunk_z * chunk_size
        end_x = start_x + chunk_size
        end_z = start_z + chunk_size
        
        for pos, block_type in self.world.items():
            x, y, z = pos
            if start_x <= x < end_x and start_z <= z < end_z:
                key = f"{x},{y},{z}"
                world_blocks[key] = block_type
        
        return {
            "chunk_x": chunk_x,
            "chunk_z": chunk_z,
            "blocks": world_blocks
        }
    
    def hit_test(self, position: Tuple[float, float, float], 
                 vector: Tuple[float, float, float], max_distance: int = 8) -> Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]]]:
        """Line of sight search from current position. Returns hit block and previous block."""
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

class MinecraftServer:
    """Main server class handling client connections and game logic."""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.world = GameWorld()
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.players: Dict[str, PlayerState] = {}
        self.running = False
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol) -> str:
        """Register a new client and return player ID."""
        player_id = str(uuid.uuid4())
        self.clients[player_id] = websocket
        
        # Default spawn position
        spawn_position = (30.0, 50.0, 80.0)
        spawn_rotation = (0.0, 0.0)
        
        player = PlayerState(player_id, spawn_position, spawn_rotation)
        self.players[player_id] = player
        
        print(f"Player {player_id} connected from {websocket.remote_address}")
        return player_id
    
    async def unregister_client(self, player_id: str):
        """Unregister a client."""
        if player_id in self.clients:
            del self.clients[player_id]
        if player_id in self.players:
            del self.players[player_id]
        
        # Notify other players
        await self.broadcast_player_list()
        print(f"Player {player_id} disconnected")
    
    async def broadcast_message(self, message: Message, exclude_player: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        
        json_msg = message.to_json()
        disconnected = []
        
        for player_id, websocket in self.clients.items():
            if exclude_player and player_id == exclude_player:
                continue
            
            try:
                await websocket.send(json_msg)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(player_id)
        
        # Clean up disconnected clients
        for player_id in disconnected:
            await self.unregister_client(player_id)
    
    async def send_to_client(self, player_id: str, message: Message):
        """Send a message to a specific client."""
        if player_id not in self.clients:
            return
        
        try:
            await self.clients[player_id].send(message.to_json())
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(player_id)
    
    async def broadcast_player_list(self):
        """Broadcast the current player list to all clients."""
        message = create_player_list_message(list(self.players.values()))
        await self.broadcast_message(message)
    
    async def handle_client_message(self, player_id: str, message: Message):
        """Handle a message from a client."""
        if message.type == MessageType.PLAYER_JOIN:
            # Update player name
            if player_id in self.players:
                self.players[player_id].name = message.data.get("name", f"Player_{player_id[:8]}")
            
            # Send basic world info to new player
            world_data = self.world.get_world_data()
            init_message = create_world_init_message(world_data)
            await self.send_to_client(player_id, init_message)
            
            # Send world chunks (8x8 chunks for 128x128 world)
            chunk_size = 16
            world_size = 128
            chunks_per_side = world_size // chunk_size
            
            for chunk_x in range(chunks_per_side):
                for chunk_z in range(chunks_per_side):
                    chunk_data = self.world.get_world_chunk(chunk_x, chunk_z, chunk_size)
                    if chunk_data["blocks"]:  # Only send non-empty chunks
                        chunk_message = create_world_chunk_message(chunk_data)
                        await self.send_to_client(player_id, chunk_message)
            
            # Send player list to new player and broadcast updated list
            await self.broadcast_player_list()
        
        elif message.type == MessageType.PLAYER_MOVE:
            if player_id in self.players:
                player = self.players[player_id]
                player.position = tuple(message.data["position"])
                player.rotation = tuple(message.data["rotation"])
                
                # Broadcast player update to other clients
                player_message = Message(MessageType.PLAYER_UPDATE, player.to_dict())
                await self.broadcast_message(player_message, exclude_player=player_id)
        
        elif message.type == MessageType.BLOCK_PLACE:
            position = tuple(message.data["position"])
            block_type = message.data["block_type"]
            
            if self.world.add_block(position, block_type):
                # Broadcast block update
                block_update = BlockUpdate(position, block_type, player_id)
                update_message = create_world_update_message([block_update])
                await self.broadcast_message(update_message)
        
        elif message.type == MessageType.BLOCK_DESTROY:
            position = tuple(message.data["position"])
            
            if self.world.remove_block(position):
                # Broadcast block removal (air block)
                block_update = BlockUpdate(position, BlockType.AIR, player_id)
                update_message = create_world_update_message([block_update])
                await self.broadcast_message(update_message)
        
        elif message.type == MessageType.CHAT_MESSAGE:
            # Broadcast chat message with player name
            player_name = self.players[player_id].name if player_id in self.players else "Unknown"
            chat_text = f"{player_name}: {message.data['text']}"
            
            chat_message = Message(MessageType.CHAT_BROADCAST, {"text": chat_text})
            await self.broadcast_message(chat_message)
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a client connection."""
        player_id = await self.register_client(websocket)
        
        try:
            async for message_str in websocket:
                try:
                    message = Message.from_json(message_str)
                    message.player_id = player_id
                    await self.handle_client_message(player_id, message)
                except Exception as e:
                    print(f"Error handling message from {player_id}: {e}")
                    error_msg = Message(MessageType.ERROR, {"message": str(e)})
                    await self.send_to_client(player_id, error_msg)
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(player_id)
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.running = True
        print(f"Starting Minecraft server on {self.host}:{self.port}")
        
        server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"Server started! Connect clients to ws://{self.host}:{self.port}")
        
        await server.wait_closed()
    
    def stop_server(self):
        """Stop the server."""
        self.running = False

def main():
    """Main entry point for the server."""
    server = MinecraftServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop_server()

if __name__ == "__main__":
    main()