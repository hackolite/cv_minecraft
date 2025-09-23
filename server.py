"""
Serveur Minecraft minimal.
"""

import asyncio
import logging
import random
import websockets
from typing import Dict, Tuple, Optional

from noise_gen import NoiseGen
from protocol import MessageType, BlockType, create_world_init_message, create_world_chunk_message, PlayerState
from minecraft_physics import MinecraftCollisionDetector, MinecraftPhysics

# Constantes
WORLD_SIZE = 128
DEFAULT_SPAWN_POSITION = (64, 100, 64)
WATER_LEVEL = 15
GRASS_LEVEL = 18

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def normalize(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Normalise une position en coordonnées de bloc."""
    return tuple(int(round(coord)) for coord in position)

class WorldGenerator:
    """Générateur de monde minimal."""
    
    def __init__(self):
        self.noise = NoiseGen(random.randint(0, 1000000))
        self.world_blocks = {}
        self._generate_basic_world()
    
    def _generate_basic_world(self):
        """Génère un monde basique."""
        # Génère un terrain simple autour du spawn
        for x in range(50, 80):
            for z in range(50, 80):
                height = int(self.noise.getHeight(x, z))
                height = max(WATER_LEVEL, min(height, GRASS_LEVEL + 5))
                
                # Ajoute des blocs jusqu'à la hauteur du terrain
                for y in range(height):
                    if y < WATER_LEVEL:
                        self.world_blocks[(x, y, z)] = BlockType.SAND
                    elif y < height - 1:
                        self.world_blocks[(x, y, z)] = BlockType.STONE
                    else:
                        self.world_blocks[(x, y, z)] = BlockType.GRASS
    
    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        """Retourne le type de bloc à la position donnée."""
        return self.world_blocks.get(position)
    
    def add_block(self, position: Tuple[int, int, int], block_type: str) -> bool:
        """Ajoute un bloc."""
        if position not in self.world_blocks:
            self.world_blocks[position] = block_type
            return True
        return False
    
    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Retire un bloc."""
        if position in self.world_blocks:
            del self.world_blocks[position]
            return True
        return False
    
    def get_world_chunk(self, chunk_x: int, chunk_z: int, chunk_size: int = 16) -> Dict:
        """Retourne un chunk du monde."""
        blocks = {}
        start_x = chunk_x * chunk_size
        start_z = chunk_z * chunk_size
        
        for x in range(start_x, start_x + chunk_size):
            for z in range(start_z, start_z + chunk_size):
                for y in range(WORLD_SIZE):
                    position = (x, y, z)
                    block_type = self.get_block(position)
                    if block_type:
                        blocks[f"{x},{y},{z}"] = block_type
        
        return {"blocks": blocks, "chunk_x": chunk_x, "chunk_z": chunk_z}

class MinecraftServer:
    """Serveur Minecraft minimal."""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.clients = {}  # websocket -> player_id mapping
        self.players = {}  # player_id -> PlayerState mapping
        self.world = WorldGenerator()
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def handle_client(self, websocket, path):
        """Gère une connexion client."""
        player_id = None
        try:
            self.logger.info(f"New client connected from {websocket.remote_address}")
            
            async for message in websocket:
                data = eval(message)  # Simplifié - normalement on utiliserait json.loads
                await self.process_message(websocket, data)
                
        except Exception as e:
            self.logger.error(f"Client error: {e}")
        finally:
            if player_id and player_id in self.players:
                del self.players[player_id]
                self.logger.info(f"Player {player_id} disconnected")
    
    async def process_message(self, websocket, data):
        """Traite un message reçu d'un client."""
        msg_type = data.get("type")
        msg_data = data.get("data", {})
        
        if msg_type == "player_join":
            await self.handle_player_join(websocket, msg_data)
        elif msg_type == "player_move":
            await self.handle_player_move(websocket, msg_data)
        elif msg_type == "block_place":
            await self.handle_block_place(websocket, msg_data)
        elif msg_type == "block_destroy":
            await self.handle_block_destroy(websocket, msg_data)
    
    async def handle_player_join(self, websocket, data):
        """Gère l'arrivée d'un joueur."""
        player_name = data.get("name", "Player")
        player_id = f"player_{len(self.players)}"
        
        # Crée le joueur
        player = PlayerState(player_id, DEFAULT_SPAWN_POSITION)
        self.players[player_id] = player
        self.clients[websocket] = player_id
        
        # Envoie l'initialisation du monde
        init_msg = create_world_init_message(DEFAULT_SPAWN_POSITION)
        await websocket.send(str(init_msg))
        
        # Envoie les chunks autour du spawn
        spawn_chunk_x = DEFAULT_SPAWN_POSITION[0] // 16
        spawn_chunk_z = DEFAULT_SPAWN_POSITION[2] // 16
        
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                chunk_data = self.world.get_world_chunk(spawn_chunk_x + dx, spawn_chunk_z + dz)
                chunk_msg = create_world_chunk_message(chunk_data)
                await websocket.send(str(chunk_msg))
        
        self.logger.info(f"Player {player_name} ({player_id}) joined")
    
    async def handle_player_move(self, websocket, data):
        """Gère le mouvement d'un joueur."""
        player_id = self.clients.get(websocket)
        if player_id and player_id in self.players:
            position = data.get("position")
            if position:
                self.players[player_id].position = tuple(position)
    
    async def handle_block_place(self, websocket, data):
        """Gère le placement d'un bloc."""
        position = tuple(data.get("position", [0, 0, 0]))
        block_type = data.get("block_type", BlockType.STONE)
        
        if self.world.add_block(position, block_type):
            # Broadcast aux autres clients
            await self.broadcast_block_update(position, block_type)
    
    async def handle_block_destroy(self, websocket, data):
        """Gère la destruction d'un bloc."""
        position = tuple(data.get("position", [0, 0, 0]))
        
        if self.world.remove_block(position):
            # Broadcast aux autres clients
            await self.broadcast_block_update(position, None)
    
    async def broadcast_block_update(self, position, block_type):
        """Diffuse une mise à jour de bloc à tous les clients."""
        update_msg = {
            "type": "block_update",
            "data": {"position": list(position), "block_type": block_type}
        }
        
        for websocket in self.clients:
            try:
                await websocket.send(str(update_msg))
            except:
                pass  # Client déconnecté
    
    async def start_server(self):
        """Démarre le serveur."""
        self.running = True
        self.logger.info(f"Starting Minecraft server on {self.host}:{self.port}")
        
        try:
            server = await websockets.serve(self.handle_client, self.host, self.port)
            self.logger.info(f"Server started! Connect clients to ws://{self.host}:{self.port}")
            await server.wait_closed()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.running = False

def main():
    """Point d'entrée principal du serveur."""
    server = MinecraftServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server crashed: {e}")

if __name__ == "__main__":
    main()