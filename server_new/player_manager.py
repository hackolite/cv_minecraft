"""
Player manager for server
Handles player state, inventory, and game logic
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from protocol.auth import PlayerSession


logger = logging.getLogger(__name__)


@dataclass
class ServerPlayer:
    """Server-side player representation"""
    uuid: str
    username: str
    entity_id: int
    position: List[float] = field(default_factory=lambda: [30.0, 50.0, 80.0])
    rotation: List[float] = field(default_factory=lambda: [0.0, 0.0])
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # Game state
    health: float = 20.0
    food: float = 20.0
    experience: int = 0
    gamemode: int = 1  # 0=survival, 1=creative, 2=adventure, 3=spectator
    
    # Physics state
    on_ground: bool = True
    flying: bool = False
    allow_flying: bool = True
    
    # Inventory
    inventory: List[str] = field(default_factory=lambda: ["BRICK", "GRASS", "SAND", "WOOD", "LEAF"])
    selected_slot: int = 0
    
    # Connection info
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    ping: float = 0.0
    
    # Player settings
    view_distance: int = 10
    chat_enabled: bool = True
    
    def update_last_seen(self):
        """Update the last seen timestamp"""
        self.last_seen = time.time()
    
    def get_selected_item(self) -> str:
        """Get the currently selected item"""
        if 0 <= self.selected_slot < len(self.inventory):
            return self.inventory[self.selected_slot]
        return "BRICK"  # Default item
    
    def set_selected_slot(self, slot: int):
        """Set the selected inventory slot"""
        if 0 <= slot < len(self.inventory):
            self.selected_slot = slot
    
    def is_online(self, timeout: float = 60.0) -> bool:
        """Check if player is considered online"""
        return time.time() - self.last_seen < timeout
    
    def to_dict(self) -> dict:
        """Convert to dictionary for network transmission"""
        return {
            'uuid': self.uuid,
            'username': self.username,
            'entity_id': self.entity_id,
            'position': self.position.copy(),
            'rotation': self.rotation.copy(),
            'health': self.health,
            'gamemode': self.gamemode,
            'flying': self.flying,
            'selected_item': self.get_selected_item()
        }


class PlayerManager:
    """
    Player manager with separated concerns
    Handles player state, inventory, and game logic separate from networking
    """
    
    def __init__(self):
        # Player storage
        self.players: Dict[str, ServerPlayer] = {}  # UUID -> Player
        self.username_to_uuid: Dict[str, str] = {}  # Username -> UUID
        
        # Entity ID management
        self._next_entity_id = 1
        
        # Player limits
        self.max_players = 20
        self.default_gamemode = 1  # Creative
        
        # Game configuration
        self.spawn_position = [30.0, 50.0, 80.0]
        self.world_spawn = [0.0, 50.0, 0.0]
        
        logger.info("Player manager initialized")
    
    async def create_player(self, uuid: str, username: str, spawn_pos: List[float] = None) -> ServerPlayer:
        """Create a new player or return existing one"""
        if uuid in self.players:
            # Player already exists, update connection info
            player = self.players[uuid]
            player.update_last_seen()
            logger.info(f"Returning existing player {username} ({uuid})")
            return player
        
        # Create new player
        entity_id = self._get_next_entity_id()
        position = spawn_pos or self.spawn_position.copy()
        
        player = ServerPlayer(
            uuid=uuid,
            username=username,
            entity_id=entity_id,
            position=position,
            gamemode=self.default_gamemode
        )
        
        # Store player
        self.players[uuid] = player
        self.username_to_uuid[username.lower()] = uuid
        
        logger.info(f"Created new player {username} ({uuid}) with entity ID {entity_id}")
        return player
    
    def _get_next_entity_id(self) -> int:
        """Get the next available entity ID"""
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        return entity_id
    
    def get_player(self, uuid: str) -> Optional[ServerPlayer]:
        """Get a player by UUID"""
        return self.players.get(uuid)
    
    def get_player_by_username(self, username: str) -> Optional[ServerPlayer]:
        """Get a player by username"""
        uuid = self.username_to_uuid.get(username.lower())
        if uuid:
            return self.players.get(uuid)
        return None
    
    def get_online_players(self) -> List[ServerPlayer]:
        """Get all online players"""
        return [player for player in self.players.values() if player.is_online()]
    
    def get_all_players(self) -> List[ServerPlayer]:
        """Get all players (online and offline)"""
        return list(self.players.values())
    
    async def disconnect_player(self, uuid: str):
        """Handle player disconnection"""
        player = self.players.get(uuid)
        if player:
            player.update_last_seen()
            logger.info(f"Player {player.username} ({uuid}) disconnected")
            
            # In a real implementation, you might save player data here
            # For now, we keep the player in memory for potential reconnection
    
    async def remove_player(self, uuid: str):
        """Completely remove a player"""
        player = self.players.pop(uuid, None)
        if player:
            self.username_to_uuid.pop(player.username.lower(), None)
            logger.info(f"Removed player {player.username} ({uuid})")
    
    async def update_player_position(self, uuid: str, position: List[float], rotation: List[float] = None):
        """Update a player's position and rotation"""
        player = self.players.get(uuid)
        if player:
            player.position = position.copy()
            if rotation:
                player.rotation = rotation.copy()
            player.update_last_seen()
            
            # Basic physics validation
            await self._validate_player_position(player)
    
    async def _validate_player_position(self, player: ServerPlayer):
        """Validate and correct player position if needed"""
        # Basic ground check
        if player.position[1] < 1.0:
            player.position[1] = 1.0
            player.velocity[1] = 0.0
            player.on_ground = True
        
        # World bounds check (basic)
        max_coord = 1000.0
        for i in range(3):
            if abs(player.position[i]) > max_coord:
                player.position[i] = max(-max_coord, min(max_coord, player.position[i]))
    
    async def update_player_health(self, uuid: str, health: float):
        """Update a player's health"""
        player = self.players.get(uuid)
        if player:
            player.health = max(0.0, min(20.0, health))
            player.update_last_seen()
            
            if player.health <= 0:
                await self._handle_player_death(player)
    
    async def _handle_player_death(self, player: ServerPlayer):
        """Handle player death"""
        logger.info(f"Player {player.username} died")
        
        # Respawn player
        player.health = 20.0
        player.food = 20.0
        player.position = self.spawn_position.copy()
        player.velocity = [0.0, 0.0, 0.0]
        
        # In a real implementation, you might drop items, send death message, etc.
    
    async def update_player_gamemode(self, uuid: str, gamemode: int):
        """Update a player's gamemode"""
        player = self.players.get(uuid)
        if player and 0 <= gamemode <= 3:
            player.gamemode = gamemode
            player.update_last_seen()
            
            # Update abilities based on gamemode
            if gamemode == 1:  # Creative
                player.allow_flying = True
                player.flying = True
            elif gamemode == 3:  # Spectator
                player.allow_flying = True
                player.flying = True
            else:  # Survival, Adventure
                player.allow_flying = False
                player.flying = False
    
    async def update_player_inventory(self, uuid: str, inventory: List[str]):
        """Update a player's inventory"""
        player = self.players.get(uuid)
        if player:
            player.inventory = inventory.copy()
            player.update_last_seen()
    
    async def set_player_selected_slot(self, uuid: str, slot: int):
        """Set a player's selected inventory slot"""
        player = self.players.get(uuid)
        if player:
            player.set_selected_slot(slot)
            player.update_last_seen()
    
    async def teleport_player(self, uuid: str, position: List[float], rotation: List[float] = None):
        """Teleport a player to a specific position"""
        player = self.players.get(uuid)
        if player:
            player.position = position.copy()
            if rotation:
                player.rotation = rotation.copy()
            player.velocity = [0.0, 0.0, 0.0]
            player.update_last_seen()
            
            logger.info(f"Teleported {player.username} to {position}")
    
    async def send_message_to_player(self, uuid: str, message: str, sender: str = "Server"):
        """Send a message to a specific player"""
        player = self.players.get(uuid)
        if player:
            # In a real implementation, this would send a packet to the player
            logger.info(f"Message to {player.username}: [{sender}] {message}")
    
    async def broadcast_message(self, message: str, sender: str = "Server", exclude_uuid: str = None):
        """Broadcast a message to all online players"""
        online_players = self.get_online_players()
        
        for player in online_players:
            if exclude_uuid and player.uuid == exclude_uuid:
                continue
            
            await self.send_message_to_player(player.uuid, message, sender)
    
    async def get_players_in_range(self, center: List[float], radius: float) -> List[ServerPlayer]:
        """Get players within a certain range of a position"""
        import math
        
        players_in_range = []
        cx, cy, cz = center
        
        for player in self.get_online_players():
            px, py, pz = player.position
            distance = math.sqrt((px - cx)**2 + (py - cy)**2 + (pz - cz)**2)
            
            if distance <= radius:
                players_in_range.append(player)
        
        return players_in_range
    
    async def cleanup_disconnected_players(self):
        """Clean up players who have been disconnected for too long"""
        offline_timeout = 300.0  # 5 minutes
        current_time = time.time()
        
        players_to_remove = []
        for uuid, player in self.players.items():
            if current_time - player.last_seen > offline_timeout:
                players_to_remove.append(uuid)
        
        for uuid in players_to_remove:
            await self.remove_player(uuid)
        
        if players_to_remove:
            logger.info(f"Cleaned up {len(players_to_remove)} disconnected players")
    
    def get_player_count(self) -> int:
        """Get total number of players"""
        return len(self.players)
    
    def get_online_count(self) -> int:
        """Get number of online players"""
        return len(self.get_online_players())
    
    def is_username_taken(self, username: str) -> bool:
        """Check if a username is already taken by an online player"""
        uuid = self.username_to_uuid.get(username.lower())
        if uuid:
            player = self.players.get(uuid)
            return player is not None and player.is_online()
        return False
    
    def get_stats(self) -> dict:
        """Get player manager statistics"""
        online_players = self.get_online_players()
        
        return {
            'total_players': self.get_player_count(),
            'online_players': len(online_players),
            'max_players': self.max_players,
            'next_entity_id': self._next_entity_id,
            'default_gamemode': self.default_gamemode,
            'spawn_position': self.spawn_position,
            'average_ping': sum(p.ping for p in online_players) / len(online_players) if online_players else 0
        }