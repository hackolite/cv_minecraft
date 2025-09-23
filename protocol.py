"""
Protocole minimal pour communication client-serveur Minecraft.
"""

import json
from enum import Enum
from typing import Dict, Tuple, Any, Optional

class MessageType(Enum):
    """Types de messages échangés entre client et serveur."""
    # Client vers Serveur
    PLAYER_JOIN = "player_join"
    PLAYER_MOVE = "player_move"
    BLOCK_PLACE = "block_place"
    BLOCK_DESTROY = "block_destroy"
    
    # Serveur vers Client
    WORLD_INIT = "world_init"
    WORLD_CHUNK = "world_chunk"
    PLAYER_UPDATE = "player_update"
    BLOCK_UPDATE = "block_update"

class BlockType:
    """Types de blocs."""
    GRASS = "grass"
    SAND = "sand"
    BRICK = "brick"
    STONE = "stone"

class Message:
    """Message de base pour communication client-serveur."""
    
    def __init__(self, msg_type: MessageType, data: Dict[str, Any]):
        self.type = msg_type
        self.data = data
    
    def to_json(self) -> str:
        return json.dumps({"type": self.type.value, "data": self.data})
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        msg_type = MessageType(data["type"])
        return cls(msg_type, data["data"])

class PlayerState:
    """État minimal d'un joueur."""
    
    def __init__(self, player_id: str, position: Tuple[float, float, float]):
        self.id = player_id
        self.position = position
        self.velocity = [0.0, 0.0, 0.0]

# Fonctions de création de messages simplifiées
def create_world_init_message(spawn_position: Tuple[float, float, float]) -> Dict[str, Any]:
    return {"type": "world_init", "spawn_position": list(spawn_position)}

def create_world_chunk_message(chunk_data: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "world_chunk", "data": chunk_data}

def create_player_update_message(player: PlayerState) -> Dict[str, Any]:
    return {
        "type": "player_update", 
        "data": {"id": player.id, "position": list(player.position)}
    }

def create_block_update_message(position: Tuple[int, int, int], block_type: str) -> Dict[str, Any]:
    return {
        "type": "block_update",
        "data": {"position": list(position), "block_type": block_type}
    }