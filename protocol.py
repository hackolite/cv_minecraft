"""
Shared protocol definitions for client-server communication.
Defines message types and data structures used between client and server.
"""

import json
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional

class MessageType(Enum):
    """Types of messages exchanged between client and server."""
    # Client to Server
    PLAYER_JOIN = "player_join"
    PLAYER_MOVE = "player_move"
    PLAYER_LOOK = "player_look"
    BLOCK_PLACE = "block_place"
    BLOCK_DESTROY = "block_destroy"
    CHAT_MESSAGE = "chat_message"
    PLAYER_DISCONNECT = "player_disconnect"

    # Server to Client
    WORLD_INIT = "world_init"
    WORLD_CHUNK = "world_chunk"
    WORLD_UPDATE = "world_update"
    PLAYER_UPDATE = "player_update"
    BLOCK_UPDATE = "block_update"
    CHAT_BROADCAST = "chat_broadcast"
    PLAYER_LIST = "player_list"
    ERROR = "error"

class BlockType:
    """Block type definitions shared between client and server."""
    GRASS = "grass"
    SAND = "sand"
    BRICK = "brick"
    STONE = "stone"
    WOOD = "wood"
    LEAF = "leaf"
    WATER = "water"
    AIR = "air"  # Represents removed blocks
    CAMERA = "camera"  # Special camera block that creates a user with FastAPI server

class Message:
    """Base message class for client-server communication."""

    def __init__(self, msg_type: MessageType, data: Dict[str, Any], player_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = None  # Can be added for timing

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "player_id": self.player_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        data = json.loads(json_str)
        msg_type = MessageType(data["type"])
        return cls(msg_type, data["data"], data.get("player_id"))

class Cube:
    """Base class representing a cube in the game world."""
    
    def __init__(self, cube_id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float] = (0, 0), size: float = 0.5):
        self.id = cube_id
        self.position = position  # (x, y, z)
        self.rotation = rotation  # (horizontal, vertical)
        self.size = size  # Half-size of the cube (cube extends from -size to +size)
        self.velocity = [0.0, 0.0, 0.0]  # (dx, dy, dz)
        self.color = None  # Will be set by the model
    
    def update_position(self, position: Tuple[float, float, float]):
        """Update the cube's position with validation."""
        if not isinstance(position, (tuple, list)) or len(position) != 3:
            raise ValueError(f"Position must be a 3-element tuple/list, got: {position}")
        
        x, y, z = position
        if not all(isinstance(coord, (int, float)) for coord in [x, y, z]):
            raise ValueError(f"Position coordinates must be numeric: {position}")
        
        self.position = position
    
    def update_rotation(self, rotation: Tuple[float, float]):
        """Update the cube's rotation."""
        self.rotation = rotation
    
    def get_render_position(self) -> Tuple[float, float, float]:
        """Get the position for rendering (positioned on ground with bottom touching surface)."""
        x, y, z = self.position
        
        # Defensive validation: ensure position is valid
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)) or not isinstance(z, (int, float)):
            raise ValueError(f"Invalid position values: {self.position}")
        
        # Calculate render position: cube center is elevated by size so bottom touches surface at Y
        render_y = y + self.size
        return (x, render_y, z)  # Elevate by half-size so bottom touches ground

class PlayerState(Cube):
    """Represents a player's state in the game world. Extends Cube for unified handling."""

    def __init__(self, id: str, position: Tuple[float, float, float],
                 rotation: Tuple[float, float], name: Optional[str] = None, 
                 is_connected: bool = True, is_rtsp_user: bool = False):
        super().__init__(id, position, rotation, size=0.5)
        self.name = name or f"Player_{id[:8]}"
        self.flying = False
        self.sprinting = False
        self.on_ground = False
        self.is_local = False  # Flag to identify local player
        self.is_connected = is_connected  # Flag for connected WebSocket clients
        self.is_rtsp_user = is_rtsp_user  # Flag for RTSP users
        self.last_move_time = 0.0  # Timestamp of last voluntary movement

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "position": self.position,
            "rotation": self.rotation,
            "name": self.name,
            "flying": self.flying,
            "sprinting": self.sprinting,
            "velocity": self.velocity,
            "on_ground": self.on_ground,
            "size": self.size,
            "is_connected": self.is_connected,
            "is_rtsp_user": self.is_rtsp_user
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create from dictionary."""
        player = cls(data["id"], tuple(data["position"]), tuple(data["rotation"]), 
                    data.get("name"), data.get("is_connected", True), data.get("is_rtsp_user", False))
        player.flying = data.get("flying", False)
        player.sprinting = data.get("sprinting", False)
        player.size = data.get("size", 0.5)
        return player

class BlockUpdate:
    """Represents a block change in the world."""

    def __init__(self, position: Tuple[int, int, int], block_type: str, player_id: Optional[str] = None):
        self.position = position
        self.block_type = block_type
        self.player_id = player_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "position": self.position,
            "block_type": self.block_type,
            "player_id": self.player_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockUpdate':
        """Create from dictionary."""
        return cls(tuple(data["position"]), data["block_type"], data.get("player_id"))

def create_player_join_message(player_name: str) -> Message:
    """Create a player join message."""
    return Message(MessageType.PLAYER_JOIN, {"name": player_name})

def create_player_move_message(position: Tuple[float, float, float],
                             rotation: Tuple[float, float]) -> Message:
    """Create a player movement message with absolute position updates."""
    return Message(MessageType.PLAYER_MOVE, {
        "position": position,
        "rotation": rotation
    })

def create_block_place_message(position: Tuple[int, int, int], block_type: str) -> Message:
    """Create a block placement message."""
    return Message(MessageType.BLOCK_PLACE, {
        "position": position,
        "block_type": block_type
    })

def create_block_destroy_message(position: Tuple[int, int, int]) -> Message:
    """Create a block destruction message."""
    return Message(MessageType.BLOCK_DESTROY, {
        "position": position
    })

def create_chat_message(text: str) -> Message:
    """Create a chat message."""
    return Message(MessageType.CHAT_MESSAGE, {"text": text})

def create_world_init_message(world_data: Dict[str, Any]) -> Message:
    """Create a world initialization message for new clients."""
    return Message(MessageType.WORLD_INIT, world_data)

def create_world_chunk_message(chunk_data: Dict[str, Any]) -> Message:
    """Create a world chunk message for streaming world data."""
    return Message(MessageType.WORLD_CHUNK, chunk_data)

def create_world_update_message(blocks: List[BlockUpdate]) -> Message:
    """Create a world update message with multiple block changes."""
    return Message(MessageType.WORLD_UPDATE, {
        "blocks": [block.to_dict() for block in blocks]
    })

def create_player_update_message(player: PlayerState) -> Message:
    """Create a player update message."""
    return Message(MessageType.PLAYER_UPDATE, player.to_dict())

def create_player_list_message(players: List[PlayerState]) -> Message:
    """Create a player list message."""
    import logging
    logger = logging.getLogger(__name__)
    
    player_dicts = []
    for player in players:
        player_dict = player.to_dict()
        player_dicts.append(player_dict)
        logger.info(f"Creating player list entry: {player.name} -> {player_dict}")
    
    logger.info(f"Player list message created with {len(player_dicts)} players")
    return Message(MessageType.PLAYER_LIST, {
        "players": player_dicts
    })
