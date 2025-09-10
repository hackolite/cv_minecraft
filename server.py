#!/usr/bin/env python3
"""
Serveur Minecraft-like en Python
Gère le monde, les joueurs et les interactions
"""

import asyncio
import websockets
import json
import uuid
import logging
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import random

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Block:
    """Représente un bloc dans le monde"""
    x: int
    y: int
    z: int
    block_type: str = "grass"
    
    def to_dict(self):
        return asdict(self)

@dataclass
class Player:
    """Représente un joueur connecté"""
    id: str
    name: str
    x: float = 0.0
    y: float = 10.0
    z: float = 0.0
    websocket: object = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z
        }

class MinecraftServer:
    def __init__(self, world_size=50, host="localhost", port=8765):
        self.world_size = world_size
        self.host = host
        self.port = port
        
        # Stockage du monde - clé: (x,y,z), valeur: Block
        self.world: Dict[Tuple[int, int, int], Block] = {}
        
        # Joueurs connectés - clé: player_id, valeur: Player
        self.players: Dict[str, Player] = {}
        
        # WebSockets des clients connectés
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Types de blocs disponibles
        self.block_types = ["grass", "stone", "wood", "dirt", "sand", "water"]
        
        # Générer le monde initial
        self.generate_world()
        
    def generate_world(self):
        """Génère un monde simple avec terrain et structures basiques"""
        logger.info("Génération du monde...")
        
        # Génération du terrain de base
        for x in range(-self.world_size//2, self.world_size//2):
            for z in range(-self.world_size//2, self.world_size//2):
                # Hauteur du terrain avec un peu de variation
                height = int(5 + 3 * random.random())
                
                # Couches du terrain
                for y in range(height):
                    if y == height - 1:
                        block_type = "grass"
                    elif y >= height - 3:
                        block_type = "dirt" 
                    else:
                        block_type = "stone"
                        
                    block = Block(x, y, z, block_type)
                    self.world[(x, y, z)] = block
                    
        # Ajouter quelques structures simples
        self.add_simple_structures()
        logger.info(f"Monde généré avec {len(self.world)} blocs")
        
    def add_simple_structures(self):
        """Ajoute quelques structures simples au monde"""
        # Petite maison
        for x in range(5, 10):
            for z in range(5, 10):
                # Murs
                if x == 5 or x == 9 or z == 5 or z == 9:
                    for y in range(8, 12):
                        self.world[(x, y, z)] = Block(x, y, z, "wood")
                        
        # Tour simple
        for y in range(8, 20):
            self.world[(-5, y, -5)] = Block(-5, y, -5, "stone")
            
    def get_world_data(self) -> List[dict]:
        """Retourne les données du monde pour les clients"""
        return [block.to_dict() for block in self.world.values()]
        
    def get_players_data(self) -> List[dict]:
        """Retourne les données des joueurs connectés"""
        return [player.to_dict() for player in self.players.values()]
        
    async def register_player(self, websocket, name: str) -> str:
        """Enregistre un nouveau joueur"""
        player_id = str(uuid.uuid4())
        
        # Position de spawn aléatoire
        spawn_x = random.randint(-10, 10)
        spawn_z = random.randint(-10, 10)
        spawn_y = 15  # Au-dessus du terrain
        
        player = Player(
            id=player_id,
            name=name,
            x=spawn_x,
            y=spawn_y,
            z=spawn_z,
            websocket=websocket
        )
        
        self.players[player_id] = player
        self.connected_clients.add(websocket)
        
        logger.info(f"Joueur {name} connecté (ID: {player_id})")
        
        # Notifier tous les clients qu'un nouveau joueur s'est connecté
        await self.broadcast_player_update()
        
        return player_id
        
    async def unregister_player(self, websocket):
        """Déconnecte un joueur"""
        player_to_remove = None
        for player in self.players.values():
            if player.websocket == websocket:
                player_to_remove = player
                break
                
        if player_to_remove:
            logger.info(f"Joueur {player_to_remove.name} déconnecté")
            del self.players[player_to_remove.id]
            
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
            
        # Notifier les autres clients
        await self.broadcast_player_update()
        
    async def update_player_position(self, player_id: str, x: float, y: float, z: float):
        """Met à jour la position d'un joueur"""
        if player_id in self.players:
            player = self.players[player_id]
            player.x = x
            player.y = y
            player.z = z
            
            # Diffuser la nouvelle position à tous les clients
            await self.broadcast_player_update()
            
    async def place_block(self, x: int, y: int, z: int, block_type: str = "grass"):
        """Place un bloc dans le monde"""
        if block_type in self.block_types:
            self.world[(x, y, z)] = Block(x, y, z, block_type)
            await self.broadcast_world_update(x, y, z, "place", block_type)
            logger.info(f"Bloc {block_type} placé en ({x}, {y}, {z})")
            
    async def remove_block(self, x: int, y: int, z: int):
        """Retire un bloc du monde"""
        if (x, y, z) in self.world:
            del self.world[(x, y, z)]
            await self.broadcast_world_update(x, y, z, "remove")
            logger.info(f"Bloc retiré en ({x}, {y}, {z})")
            
    async def broadcast_player_update(self):
        """Diffuse les mises à jour des joueurs à tous les clients"""
        if self.connected_clients:
            message = {
                "type": "players_update",
                "players": self.get_players_data()
            }
            await asyncio.gather(
                *[self.send_safe(client, json.dumps(message)) 
                  for client in self.connected_clients],
                return_exceptions=True
            )
            
    async def broadcast_world_update(self, x: int, y: int, z: int, action: str, block_type: str = None):
        """Diffuse une modification du monde à tous les clients"""
        if self.connected_clients:
            message = {
                "type": "world_update",
                "action": action,
                "x": x,
                "y": y,
                "z": z,
                "block_type": block_type
            }
            await asyncio.gather(
                *[self.send_safe(client, json.dumps(message)) 
                  for client in self.connected_clients],
                return_exceptions=True
            )
            
    async def send_safe(self, websocket, message):
        """Envoie un message de manière sécurisée"""
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            
    async def handle_client_message(self, websocket, message_data):
        """Gère les messages reçus des clients"""
        try:
            message = json.loads(message_data)
            msg_type = message.get("type")
            
            if msg_type == "join":
                player_name = message.get("name", "Joueur")
                player_id = await self.register_player(websocket, player_name)
                
                # Envoyer les données initiales au nouveau client
                response = {
                    "type": "init",
                    "player_id": player_id,
                    "world": self.get_world_data(),
                    "players": self.get_players_data()
                }
                await websocket.send(json.dumps(response))
                
            elif msg_type == "move":
                player_id = message.get("player_id")
                x = message.get("x")
                y = message.get("y")
                z = message.get("z")
                await self.update_player_position(player_id, x, y, z)
                
            elif msg_type == "place_block":
                x = message.get("x")
                y = message.get("y")
                z = message.get("z")
                block_type = message.get("block_type", "grass")
                await self.place_block(x, y, z, block_type)
                
            elif msg_type == "remove_block":
                x = message.get("x")
                y = message.get("y")
                z = message.get("z")
                await self.remove_block(x, y, z)
                
            elif msg_type == "chat":
                # Diffuser le message de chat
                chat_message = {
                    "type": "chat",
                    "player_name": message.get("player_name"),
                    "message": message.get("message"),
                    "timestamp": datetime.now().isoformat()
                }
                await asyncio.gather(
                    *[self.send_safe(client, json.dumps(chat_message)) 
                      for client in self.connected_clients],
                    return_exceptions=True
                )
                
        except json.JSONDecodeError:
            logger.error("Message JSON invalide reçu")
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            
    async def handle_client(self, websocket, path):
        """Gère une connexion client"""
        logger.info(f"Nouvelle connexion client: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client déconnecté")
        except Exception as e:
            logger.error(f"Erreur connexion client: {e}")
        finally:
            await self.unregister_player(websocket)
            
    async def start_server(self):
        """Démarre le serveur WebSocket"""
        logger.info(f"Démarrage du serveur sur {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info("Serveur Minecraft démarré ! En attente de connexions...")
        await server.wait_closed()

def main():
    """Point d'entrée principal"""
    print("🎮 Serveur Minecraft-like")
    print("=" * 30)
    
    # Configuration
    HOST = "localhost"
    PORT = 8765
    WORLD_SIZE = 50
    
    # Créer et démarrer le serveur
    server = MinecraftServer(world_size=WORLD_SIZE, host=HOST, port=PORT)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du serveur...")
    except Exception as e:
        logger.error(f"Erreur serveur: {e}")

if __name__ == "__main__":
    main()
