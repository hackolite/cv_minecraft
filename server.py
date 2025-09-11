#!/usr/bin/env python3
"""
Minecraft-like Server - Version corrigée
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

# Block types - utilisation d'identifiants simples
GRASS = "grass"
SAND = "sand"
BRICK = "brick"
STONE = "stone"
WOOD = "wood"
LEAF = "leaf"
WATER = "water"
FROG = "frog"

# Coordonnées de texture pour le client
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

# Mapping des textures - à envoyer au client si nécessaire
BLOCK_TEXTURES = {
    GRASS: tex_coords((1, 0), (0, 1), (0, 0)),
    SAND: tex_coords((1, 1), (1, 1), (1, 1)),
    BRICK: tex_coords((2, 0), (2, 0), (2, 0)),
    STONE: tex_coords((2, 1), (2, 1), (2, 1)),
    WOOD: tex_coords((3, 1), (3, 1), (3, 1)),
    LEAF: tex_coords((3, 0), (3, 0), (3, 0)),
    WATER: tex_coords((0, 2), (0, 2), (0, 2)),
    FROG: tex_coords((1, 2), (1, 2), (1, 2))
}

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
            'position': list(self.position),  # Assure-toi que c'est une liste
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
        
        print("Generating world...")
        
        # Generate height map
        height_map = {}
        for x in xrange(0, n, s):
            for z in xrange(0, n, s):
                height_map[(x, z)] = int(gen.getHeight(x, z))
        
        # Generate the world
        blocks_created = 0
        for x in xrange(0, n, s):
            for z in xrange(0, n, s):
                h = height_map[(x, z)]
                
                # Water level blocks
                if h < 15:
                    self.add_block((x, h, z), SAND)
                    blocks_created += 1
                    for y in range(h + 1, 15):
                        self.add_block((x, y, z), WATER)
                        blocks_created += 1
                    continue
                
                # Sandy areas
                if h < 18:
                    self.add_block((x, h, z), SAND)
                    blocks_created += 1
                else:
                    self.add_block((x, h, z), GRASS)
                    blocks_created += 1
                
                # Fill below surface with stone
                for y in xrange(max(1, h - 3), h):  # Réduit de 5 à 3 pour moins de blocs souterrains
                    self.add_block((x, y, z), STONE)
                    blocks_created += 1
                
                # Maybe add tree
                if h > 20:
                    if random.randrange(0, 1000) > 998:  # Moins d'arbres (0.2% au lieu de 0.5%)
                        tree_height = random.randrange(3, 5)
                        
                        # Tree trunk
                        for y in xrange(h + 1, h + tree_height):
                            self.add_block((x, y, z), WOOD)
                            blocks_created += 1
                        
                        # Tree leaves (plus compact)
                        leaf_h = h + tree_height
                        for lz in xrange(z - 1, z + 2):
                            for lx in xrange(x - 1, x + 2):
                                for ly in xrange(2):
                                    if 0 <= lx < n and 0 <= lz < n:  # Vérification des limites
                                        self.add_block((lx, leaf_h + ly, lz), LEAF)
                                        blocks_created += 1
        
        print(f"World generation complete. Created {blocks_created} blocks.")
    
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
    
    def get_blocks_in_range(self, center_pos, radius):
        """Get all blocks within radius of center position."""
        cx, cy, cz = center_pos
        blocks = []
        
        for position, block in self.world.items():
            x, y, z = position
            distance = ((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) ** 0.5
            if distance <= radius:
                blocks.append(block)
        
        return blocks

class MinecraftServer:
    """Main server class handling WebSocket connections and world management."""
    
    def __init__(self, world_size=24, port=8765):  # Taille réduite pour moins de blocs
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
    
    def find_spawn_position(self):
        """Find a suitable spawn position above ground."""
        # Cherche une position au sol près du centre du monde
        center = self.world.world_size // 2
        
        for x in range(center - 10, center + 10):
            for z in range(center - 10, center + 10):
                # Trouve le bloc le plus haut à cette position
                for y in range(50, 10, -1):  # Cherche de haut en bas
                    if (x, y, z) in self.world.world:
                        # Position du spawn = 2 blocs au-dessus du sol
                        return (x, y + 2, z)
        
        # Position par défaut si rien n'est trouvé
        return (center, 25, center)
    
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
            import traceback
            traceback.print_exc()
    
    async def handle_join(self, websocket, data):
        """Handle player join."""
        player_name = data.get('name', 'Anonymous')
        
        # Trouve une position de spawn appropriée
        spawn_pos = self.find_spawn_position()
        self.player_positions[websocket] = spawn_pos
        
        print(f"Player {player_name} spawned at {spawn_pos}")
        
        # Send welcome message
        response = {
            'type': 'welcome',
            'player_name': player_name,
            'position': spawn_pos
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
        block_type = data.get('block_type', STONE)  # Type par défaut
        
        if position:
            if self.world.add_block(position, block_type):
                print(f"Block added at {position}: {block_type}")
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
                print(f"Block removed at {position}")
                # Broadcast block removal to all clients
                await self.broadcast({
                    'type': 'block_removed',
                    'position': position
                })
    
    async def handle_get_world(self, websocket, data):
        """Send world data to client."""
        # Position du joueur
        player_pos = self.player_positions.get(websocket)
        if not player_pos:
            player_pos = self.find_spawn_position()
            self.player_positions[websocket] = player_pos
        
        print(f"Sending world data around position: {player_pos}")
        
        # Obtient les blocs dans un rayon autour du joueur
        radius = 50  # Rayon augmenté
        blocks_in_range = self.world.get_blocks_in_range(player_pos, radius)
        
        # Filtre seulement les blocs exposés pour réduire la taille des données
        visible_blocks = []
        for block in blocks_in_range:
            if self.world.exposed(block.position):
                visible_blocks.append(block.to_dict())
        
        print(f"Sending {len(visible_blocks)} visible blocks to client (radius: {radius})")
        
        # Envoie les coordonnées de texture aussi
        response = {
            'type': 'world_data',
            'blocks': visible_blocks,
            'textures': BLOCK_TEXTURES  # Inclut les définitions de texture
        }
        
        # Envoie en plusieurs petits messages si nécessaire
        if len(visible_blocks) > 500:  # Si trop de blocs
            # Découpe en chunks
            chunk_size = 500
            for i in range(0, len(visible_blocks), chunk_size):
                chunk = visible_blocks[i:i+chunk_size]
                chunk_response = {
                    'type': 'world_chunk',
                    'blocks': chunk,
                    'chunk_index': i // chunk_size,
                    'total_chunks': (len(visible_blocks) + chunk_size - 1) // chunk_size
                }
                if i == 0:  # Premier chunk inclut les textures
                    chunk_response['textures'] = BLOCK_TEXTURES
                await websocket.send(json.dumps(chunk_response))
            
            # Message de fin
            await websocket.send(json.dumps({
                'type': 'world_complete',
                'total_blocks': len(visible_blocks)
            }))
        else:
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
    server = MinecraftServer()  # Use default reduced size (24)
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nServer shutting down...")

if __name__ == "__main__":
    main()
