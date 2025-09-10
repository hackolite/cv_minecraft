#!/usr/bin/env python3
"""
Minecraft-like Server
Manages the game world and handles client connections via WebSocket
"""

import asyncio
import websockets
import json
import math
import random
import sys
from collections import deque

from noise_gen import NoiseGen

# Block types and texture coordinates
def tex_coord(x, y, n=4):
    """Return the bounding vertices of the texture square."""
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m

def tex_coords(top, bottom, side):
    """Return a list of the texture squares for the top, bottom and side."""
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)    # top
    result.extend(bottom) # bottom
    result.extend(side)   # left
    result.extend(side)   # right
    result.extend(side)   # front
    result.extend(side)   # back
    return result

# Block type definitions
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))
FROG = tex_coords((1, 2), (1, 2), (1, 2))

# Constants
SECTOR_SIZE = 16

# For Python 2/3 compatibility
if sys.version_info[0] >= 3:
    xrange = range

def normalize(position):
    """Convert float position to integer block position."""
    x, y, z = position
    return (int(round(x)), int(round(y)), int(round(z)))

def sectorize(position):
    """Return sector containing given position."""
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class Block:
    """Represents a single block in the world."""
    def __init__(self, position, block_type):
        self.position = position
        self.block_type = block_type
        
    def to_dict(self):
        """Convert block to dictionary for JSON serialization."""
        return {
            'position': self.position,
            'block_type': self.block_type
        }

class GameWorld:
    """Manages the world state and blocks."""
    
    def __init__(self, world_size=128):
        self.world = {}  # position -> Block
        self.sectors = {}  # sector -> list of positions
        self.world_size = world_size
        self._initialize()
    
    def _initialize(self):
        """Initialize the world by placing all the blocks."""
        gen = NoiseGen(452692)
        
        n = self.world_size
        s = 1  # step size
        
        # Generate height map
        height_map = {}
        for x in xrange(0, n, s):
            for z in xrange(0, n, s):
                height_map[(x, z)] = int(gen.getHeight(x, z))
        
        # Generate the world
        for x in xrange(0, n, s):
            for z in xrange(0, n, s):
                h = height_map[(x, z)]
                
                # Water level blocks
                if h < 15:
                    self.add_block((x, h, z), SAND)
                    for y in range(h + 1, 15):
                        self.add_block((x, y, z), WATER)
                    continue
                
                # Sandy areas
                if h < 18:
                    self.add_block((x, h, z), SAND)
                else:
                    self.add_block((x, h, z), GRASS)
                
                # Fill below surface with stone
                for y in xrange(h - 1, 0, -1):
                    self.add_block((x, y, z), STONE)
                
                # Maybe add tree
                if h > 20:
                    if random.randrange(0, 1000) > 990:
                        tree_height = random.randrange(5, 7)
                        
                        # Tree trunk
                        for y in xrange(h + 1, h + tree_height):
                            self.add_block((x, y, z), WOOD)
                        
                        # Tree leaves
                        leaf_h = h + tree_height
                        for lz in xrange(z - 2, z + 3):
                            for lx in xrange(x - 2, x + 3):
                                for ly in xrange(3):
                                    self.add_block((lx, leaf_h + ly, lz), LEAF)
    
    def add_block(self, position, texture):
        """Add a block to the world."""
        position = normalize(position)
        if position in self.world:
            return False
        
        self.world[position] = Block(position, texture)
        sector = sectorize(position)
        if sector not in self.sectors:
            self.sectors[sector] = []
        self.sectors[sector].append(position)
        return True
    
    def remove_block(self, position):
        """Remove a block from the world."""
        position = normalize(position)
        if position not in self.world:
            return False
        
        del self.world[position]
        sector = sectorize(position)
        if sector in self.sectors:
            self.sectors[sector].remove(position)
            if not self.sectors[sector]:
                del self.sectors[sector]
        return True
    
    def get_block(self, position):
        """Get block at position."""
        position = normalize(position)
        return self.world.get(position)
    
    def hit_test(self, position, vector, max_distance=8):
        """Line of sight search from current position."""
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        
        for _ in xrange(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        
        return None, None
    
    def exposed(self, position):
        """Check if block at position is exposed (has at least one visible face)."""
        x, y, z = position
        for dx, dy, dz in [(0, 1, 0), (0, -1, 0), (-1, 0, 0), (1, 0, 0), (0, 0, 1), (0, 0, -1)]:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    
    def get_visible_blocks_in_sector(self, sector):
        """Get all visible blocks in a sector."""
        if sector not in self.sectors:
            return []
        
        visible_blocks = []
        for position in self.sectors[sector]:
            if self.exposed(position):
                block = self.world[position]
                visible_blocks.append(block.to_dict())
        
        return visible_blocks

class MinecraftServer:
    """Main server class handling WebSocket connections and world management."""
    
    def __init__(self, world_size=128, port=8765):
        self.world = GameWorld(world_size)
        self.port = port
        self.clients = set()
        self.player_positions = {}  # websocket -> position
        
    def __len__(self):
        """Return number of blocks in the world."""
        return len(self.world.world)
    
    async def register_client(self, websocket):
        """Register a new client."""
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
    
    async def unregister_client(self, websocket):
        """Unregister a client."""
        self.clients.discard(websocket)
        if websocket in self.player_positions:
            del self.player_positions[websocket]
        print(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, message, exclude_client=None):
        """Broadcast message to all clients except excluded one."""
        if not self.clients:
            return
        
        message_str = json.dumps(message)
        clients_to_send = self.clients - {exclude_client} if exclude_client else self.clients
        
        # Remove disconnected clients
        disconnected = set()
        for client in clients_to_send:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
    
    async def handle_message(self, websocket, message):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'join':
                await self.handle_join(websocket, data)
            elif message_type == 'move':
                await self.handle_move(websocket, data)
            elif message_type == 'add_block':
                await self.handle_add_block(websocket, data)
            elif message_type == 'remove_block':
                await self.handle_remove_block(websocket, data)
            elif message_type == 'get_world':
                await self.handle_get_world(websocket, data)
            else:
                print(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            print(f"Invalid JSON received: {message}")
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def handle_join(self, websocket, data):
        """Handle player join."""
        player_name = data.get('name', 'Anonymous')
        
        # Set initial position
        self.player_positions[websocket] = (30, 50, 80)
        
        # Send welcome message
        response = {
            'type': 'welcome',
            'player_name': player_name,
            'position': self.player_positions[websocket]
        }
        await websocket.send(json.dumps(response))
        
        # Broadcast player join to others
        await self.broadcast({
            'type': 'player_joined',
            'player_name': player_name
        }, exclude_client=websocket)
    
    async def handle_move(self, websocket, data):
        """Handle player movement."""
        position = data.get('position')
        if position and websocket in self.player_positions:
            self.player_positions[websocket] = position
            
            # Broadcast position to other players
            await self.broadcast({
                'type': 'player_moved',
                'position': position
            }, exclude_client=websocket)
    
    async def handle_add_block(self, websocket, data):
        """Handle block placement."""
        position = data.get('position')
        block_type = data.get('block_type')
        
        if position and block_type:
            if self.world.add_block(position, block_type):
                # Broadcast block addition to all clients
                await self.broadcast({
                    'type': 'block_added',
                    'position': position,
                    'block_type': block_type
                })
    
    async def handle_remove_block(self, websocket, data):
        """Handle block removal."""
        position = data.get('position')
        
        if position:
            if self.world.remove_block(position):
                # Broadcast block removal to all clients
                await self.broadcast({
                    'type': 'block_removed',
                    'position': position
                })
    
    async def handle_get_world(self, websocket, data):
        """Send world data to client."""
        # For now, send a subset of the world around the player
        player_pos = self.player_positions.get(websocket, (30, 50, 80))
        player_sector = sectorize(player_pos)
        
        # Get blocks in nearby sectors
        blocks = []
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                sector = (player_sector[0] + dx, player_sector[1], player_sector[2] + dz)
                blocks.extend(self.world.get_visible_blocks_in_sector(sector))
        
        response = {
            'type': 'world_data',
            'blocks': blocks
        }
        await websocket.send(json.dumps(response))
    
    async def handle_client(self, websocket, path):
        """Handle a client connection."""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the WebSocket server."""
        print(f"Starting Minecraft server on port {self.port}")
        print(f"World size: {self.world.world_size}x{self.world.world_size}")
        print(f"Total blocks generated: {len(self.world.world)}")
        
        server = await websockets.serve(self.handle_client, "localhost", self.port)
        print(f"Server started on ws://localhost:{self.port}")
        await server.wait_closed()

def main():
    """Main function to start the server."""
    server = MinecraftServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nServer shutting down...")

if __name__ == "__main__":
    main()