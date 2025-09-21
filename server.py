"""
Minecraft Server - Server-side game world and client connections
"""

import asyncio
import logging
import math
import random
import time
import uuid
import websockets
from typing import Dict, Tuple, Optional, List, Any

from noise_gen import NoiseGen
from protocol import (
    MessageType, BlockType, Message, PlayerState, BlockUpdate,
    create_world_init_message, create_world_chunk_message, 
    create_world_update_message, create_player_list_message,
    create_player_update_message, create_movement_response_message
)
from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY,
    unified_check_collision, unified_check_player_collision
)

# ---------- Constants ----------
SECTOR_SIZE = 16
WORLD_SIZE = 128
DEFAULT_CHUNK_SIZE = 16
DEFAULT_SPAWN_POSITION = (64, 100, 64)  # High spawn position for gravity testing
WATER_LEVEL = 15
GRASS_LEVEL = 18

# Physics constants - use standard Minecraft values
STANDARD_GRAVITY = GRAVITY
STANDARD_TERMINAL_VELOCITY = TERMINAL_VELOCITY
STANDARD_PLAYER_HEIGHT = PLAYER_HEIGHT
PHYSICS_TICK_RATE = 20  # Updates per second

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------- Texture System (from minecraft.py) ----------

def tex_coord(x, y, n=4):
    """ Return the bounding vertices of the texture square.

    """
    m = 1.0 / n
    dx = x * m
    dy = y * m
    return dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m


def tex_coords(top, bottom, side):
    """ Return a list of the texture squares for the top, bottom and side.

    """
    top = tex_coord(*top)
    bottom = tex_coord(*bottom)
    side = tex_coord(*side)
    result = []
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result


TEXTURE_PATH = 'texture.png'

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))

# ---------- Utility functions ----------

def normalize(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Normalize position to integer coordinates."""
    x, y, z = position
    return int(round(x)), int(round(y)), int(round(z))


def sectorize(position: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert position to sector coordinates for spatial indexing."""
    x, y, z = normalize(position)
    return x // SECTOR_SIZE, 0, z // SECTOR_SIZE


def validate_position(position: Tuple[float, float, float]) -> bool:
    """Validate that position is within world bounds."""
    x, y, z = position
    return (0 <= x < WORLD_SIZE and 
            y >= 0 and y < 256 and  # Allow Y starting from 0
            0 <= z < WORLD_SIZE)


def validate_block_type(block_type: str) -> bool:
    """Validate that block type is allowed."""
    allowed_types = {
        BlockType.GRASS, BlockType.SAND, BlockType.BRICK, 
        BlockType.STONE, BlockType.WOOD, BlockType.LEAF, 
        BlockType.WATER, BlockType.AIR
    }
    return block_type in allowed_types

# ---------- Game World ----------

class GameWorld:
    """Game world management with spatial indexing and validation."""
    
    def __init__(self):
        self.world = {}       # position -> block type
        self.sectors = {}     # sector -> list of positions
        self._initialize_world()

    def _initialize_world(self):
        """Initialize world with enhanced terrain generation including water, sand, grass, stone, and trees."""
        logging.info("Initializing world with enhanced terrain generation...")
        gen = NoiseGen(452692)
        
        n = WORLD_SIZE  # size of the world
        s = 1  # step size
        
        # Generate height map
        height_map = []
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map.append(0)
        
        for x in range(0, n, s):
            for z in range(0, n, s):
                height_map[z + x * n] = int(gen.getHeight(x, z))

        # Generate the world based on height map
        blocks_created = 0
        for x in range(0, n, s):
            for z in range(0, n, s):
                h = height_map[z + x * n]
                
                # Water level generation (below 15)
                if h < WATER_LEVEL:
                    # Add sand at the bottom
                    if self._add_block_internal((x, h, z), BlockType.SAND):
                        blocks_created += 1
                    # Fill with water up to water level
                    for y in range(h + 1, WATER_LEVEL + 1):
                        if self._add_block_internal((x, y, z), BlockType.WATER):
                            blocks_created += 1
                    continue
                
                # Sand at water edges (15-18)
                if h < GRASS_LEVEL:
                    if self._add_block_internal((x, h, z), BlockType.SAND):
                        blocks_created += 1
                else:
                    # Grass surface for higher terrain
                    if self._add_block_internal((x, h, z), BlockType.GRASS):
                        blocks_created += 1
                
                # Underground stone layers
                for y in range(h - 1, 0, -1):
                    if self._add_block_internal((x, y, z), BlockType.STONE):
                        blocks_created += 1
                
                # Tree generation for higher terrain
                if h > 20:
                    if random.randrange(0, 1000) > 990:  # 1% chance
                        tree_height = random.randrange(5, 7)
                        
                        # Tree trunk
                        for y in range(h + 1, h + tree_height + 1):
                            if self._add_block_internal((x, y, z), BlockType.WOOD):
                                blocks_created += 1
                        
                        # Tree leaves
                        leaf_h = h + tree_height
                        for lz in range(z - 2, z + 3):
                            for lx in range(x - 2, x + 3):
                                for ly in range(3):
                                    # Check bounds before adding leaves
                                    if (0 <= lx < WORLD_SIZE and 0 <= lz < WORLD_SIZE and 
                                        leaf_h + ly < 256):
                                        if self._add_block_internal((lx, leaf_h + ly, lz), BlockType.LEAF):
                                            blocks_created += 1
        
        logging.info(f"Enhanced world initialized with {blocks_created} blocks including water, sand, grass, stone, and trees")

    def _add_block_internal(self, position: Tuple[int, int, int], block_type: str) -> bool:
        """Internal method to add blocks without validation (for world generation)."""
        if position in self.world:
            return False
        
        x, y, z = position
        # Ensure position is within bounds before adding
        if not (0 <= x < WORLD_SIZE and y >= 0 and y < 256 and 0 <= z < WORLD_SIZE):
            return False
            
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        return True

    def add_block(self, position: Tuple[int, int, int], block_type: str) -> bool:
        """Add a block at the specified position."""
        if not validate_position(position):
            logging.warning(f"Invalid position for block placement: {position}")
            return False
            
        if not validate_block_type(block_type):
            logging.warning(f"Invalid block type: {block_type}")
            return False
            
        if position in self.world:
            return False  # Block already exists
            
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        return True

    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Remove a block at the specified position."""
        if not validate_position(position):
            logging.warning(f"Invalid position for block removal: {position}")
            return False
            
        if position not in self.world:
            return False  # No block to remove
            
        # Prevent removal of stone blocks (bedrock protection)
        if self.world[position] == BlockType.STONE:
            return False
            
        del self.world[position]
        sector = sectorize(position)
        if sector in self.sectors and position in self.sectors[sector]:
            self.sectors[sector].remove(position)
        return True

    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        """Get block type at specified position."""
        return self.world.get(position)

    def get_world_data(self) -> Dict[str, Any]:
        """Get basic world information for client initialization."""
        return {
            "world_size": WORLD_SIZE, 
            "spawn_position": DEFAULT_SPAWN_POSITION
        }

    def get_world_chunk(self, chunk_x: int, chunk_z: int, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Dict[str, Any]:
        """Get a chunk of world data for streaming to clients."""
        blocks = {}
        start_x, start_z = chunk_x * chunk_size, chunk_z * chunk_size
        end_x, end_z = start_x + chunk_size, start_z + chunk_size
        
        for pos, block_type in self.world.items():
            x, y, z = pos
            if start_x <= x < end_x and start_z <= z < end_z:
                blocks[f"{x},{y},{z}"] = block_type
                
        return {
            "chunk_x": chunk_x, 
            "chunk_z": chunk_z, 
            "blocks": blocks
        }

# ---------- Custom Exceptions ----------

class ServerError(Exception):
    """Base exception for server errors."""
    pass


class InvalidPlayerDataError(ServerError):
    """Raised when player data is invalid."""
    pass


class InvalidWorldDataError(ServerError):
    """Raised when world/block data is invalid."""
    pass


# ---------- Minecraft Server ----------

class MinecraftServer:
    """WebSocket-based Minecraft server handling multiple clients."""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.world = GameWorld()
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.players: Dict[str, PlayerState] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        # Physics tick timing
        self.last_physics_update = time.time()

    def _check_simple_collision(self, position: Tuple[float, float, float], player_id: str = None) -> bool:
        """
        Simple collision check: only checks if player center position is inside a solid block.
        As specified in requirements, this is a very simple collision method.
        """
        px, py, pz = position
        
        # Check if the player's center position (feet) is in a solid block
        foot_block = (int(math.floor(px)), int(math.floor(py)), int(math.floor(pz)))
        if foot_block in self.world.world:
            return True
            
        # Check if the player's head position is in a solid block
        head_y = py + 1.8  # Standard player height
        head_block = (int(math.floor(px)), int(math.floor(head_y)), int(math.floor(pz)))
        if head_block in self.world.world:
            return True
            
        return False

    def _check_ground_collision(self, position: Tuple[float, float, float]) -> bool:
        """Check ground collision using unified collision system."""
        return unified_check_collision(position, self.world.world)

    def _check_player_collision(self, player_id: str, position: Tuple[float, float, float]) -> bool:
        """Check player collision using unified collision system."""
        other_players = [p for p in self.players.values() if p.id != player_id]
        return unified_check_player_collision(position, other_players, player_id)

    def _apply_physics(self, player: PlayerState, dt: float) -> None:
        """
        Apply standard Minecraft physics to a player using the new physics system.
        """
        if player.flying:
            return  # No gravity when flying
        
        # Don't apply physics immediately after a voluntary movement to prevent interference
        if time.time() - player.last_move_time < 0.5:  # 500ms grace period
            return
        
        # Initialize physics system if needed
        if not hasattr(self, '_collision_detector'):
            self._collision_detector = MinecraftCollisionDetector(self.world.world)
            self._physics = MinecraftPhysics(self._collision_detector)
        
        # Update collision detector with current world
        self._collision_detector.world_blocks = self.world.world
        
        # Current state
        current_velocity = player.velocity
        on_ground = player.on_ground
        
        # Apply standard Minecraft physics
        new_position, new_velocity, new_on_ground = self._physics.update_position(
            player.position, current_velocity, dt, on_ground, False  # server doesn't handle jumping directly
        )
        
        # Check for player-to-player collision during physics updates
        if self._check_player_collision(player.id, new_position):
            # If physics would cause a collision, stop the movement
            return  # Don't update position
        
        # Update player state
        player.position = new_position
        player.velocity = new_velocity
        player.on_ground = new_on_ground
        
        # Defensive validation: ensure physics didn't corrupt position
        if not isinstance(new_position, (tuple, list)) or len(new_position) != 3:
            self.logger.error(f"❌ PHYSICS ERROR: Physics corrupted position for {player.id}: {new_position}")
            # Reset to previous valid position if available
            return
        
        x, y, z = new_position
        if not all(isinstance(coord, (int, float)) for coord in [x, y, z]):
            self.logger.error(f"❌ PHYSICS ERROR: Physics generated non-numeric position for {player.id}: {new_position}")
            return

    async def _physics_update_loop(self):
        """Main physics update loop running at PHYSICS_TICK_RATE."""
        last_debug_summary = time.time()
        debug_summary_interval = 10.0  # Every 10 seconds
        
        while self.running:
            current_time = time.time()
            dt = current_time - self.last_physics_update
            
            # Update physics for all players
            for player in self.players.values():
                self._apply_physics(player, dt)
            
            # Broadcast player updates
            await self._broadcast_physics_updates()
            
            # Periodic debug summary
            if current_time - last_debug_summary > debug_summary_interval:
                self._log_player_debug_summary()
                last_debug_summary = current_time
            
            self.last_physics_update = current_time
            
            # Sleep to maintain physics tick rate
            await asyncio.sleep(1.0 / PHYSICS_TICK_RATE)

    def _log_player_debug_summary(self):
        """Log a summary of all connected players and their positions."""
        if not self.players:
            self.logger.info("📊 PLAYER DEBUG SUMMARY: No players connected")
            return
            
        self.logger.info(f"📊 PLAYER DEBUG SUMMARY: {len(self.players)} players connected")
        for player in self.players.values():
            last_move_ago = time.time() - getattr(player, 'last_move_time', time.time())
            self.logger.info(f"   🎯 {player.name or player.id[:8]}: pos={player.position}, "
                           f"vel={player.velocity}, on_ground={player.on_ground}, "
                           f"last_move={last_move_ago:.1f}s ago")

    async def _broadcast_physics_updates(self):
        """Broadcast physics updates for all players."""
        for player in self.players.values():
            if player.id in self.clients:
                update_msg = create_player_update_message(player)
                # Send this player's position to all OTHER players (not to themselves)
                await self.broadcast_message(update_msg, exclude_player=player.id)

    async def register_client(self, websocket) -> str:
        """Register a new client connection."""
        player_id = str(uuid.uuid4())
        self.clients[player_id] = websocket
        self.players[player_id] = PlayerState(player_id, DEFAULT_SPAWN_POSITION, (0, 0))
        self.logger.info(f"Player {player_id} connected from {websocket.remote_address}")
        return player_id

    async def unregister_client(self, player_id: str):
        """Unregister a client connection and clean up."""
        if player_id in self.clients:
            self.clients.pop(player_id, None)
            player = self.players.pop(player_id, None)
            if player:
                self.logger.info(f"Player {player.name} ({player_id}) disconnected")
                await self.broadcast_player_list()

    async def broadcast_message(self, message: Message, exclude_player: Optional[str] = None):
        """Broadcast a message to all connected clients with enhanced debugging."""
        if not self.clients:
            self.logger.debug("📡 No clients connected for broadcast")
            return
            
        json_msg = message.to_json()
        disconnected = []
        sent_count = 0
        
        # Debug log for player updates specifically
        if message.type == MessageType.PLAYER_UPDATE:
            player_data = message.data
            sender_name = self.players.get(player_data.get("id", ""), type('obj', (object,), {'name': 'Unknown'})).name
            self.logger.debug(f"📡 Broadcasting player update from {sender_name or 'Unknown'}")
        
        for pid, ws in list(self.clients.items()):
            if exclude_player == pid:
                continue
                
            try:
                await ws.send(json_msg)
                sent_count += 1
                
                # Debug log successful sends for player updates
                if message.type == MessageType.PLAYER_UPDATE:
                    receiver_name = self.players.get(pid, type('obj', (object,), {'name': 'Unknown'})).name
                    self.logger.debug(f"   ✅ Sent to {receiver_name or pid[:8]}")
                    
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(pid)
                self.logger.warning(f"   ❌ Connection closed for {pid[:8]}")
            except Exception as e:
                self.logger.error(f"   ❌ Error sending message to {pid[:8]}: {e}")
                disconnected.append(pid)
        
        # Log broadcast summary
        if message.type == MessageType.PLAYER_UPDATE:
            self.logger.info(f"📡 Broadcast complete: {sent_count} players notified, {len(disconnected)} disconnected")
        
        # Clean up disconnected clients
        for pid in disconnected:
            await self.unregister_client(pid)

    async def send_to_client(self, player_id: str, message: Message):
        """Send a message to a specific client."""
        if player_id not in self.clients:
            self.logger.warning(f"Attempted to send message to non-existent client: {player_id}")
            return
            
        try:
            await self.clients[player_id].send(message.to_json())
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(player_id)
        except Exception as e:
            self.logger.error(f"Error sending message to {player_id}: {e}")
            await self.unregister_client(player_id)

    async def broadcast_player_list(self):
        """Broadcast updated player list to all clients."""
        message = create_player_list_message(list(self.players.values()))
        await self.broadcast_message(message)

    async def handle_client_message(self, player_id: str, message: Message):
        """Handle incoming client messages with proper validation and error handling."""
        try:
            if message.type == MessageType.PLAYER_JOIN:
                await self._handle_player_join(player_id, message)
                
            elif message.type == MessageType.PLAYER_MOVE:
                await self._handle_player_move(player_id, message)
                
            elif message.type == MessageType.BLOCK_PLACE:
                await self._handle_block_place(player_id, message)
                
            elif message.type == MessageType.BLOCK_DESTROY:
                await self._handle_block_destroy(player_id, message)
                
            elif message.type == MessageType.CHAT_MESSAGE:
                await self._handle_chat_message(player_id, message)
                
            else:
                self.logger.warning(f"Unhandled message type: {message.type} from {player_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling message from {player_id}: {e}")
            await self.send_to_client(player_id, Message(MessageType.ERROR, {"message": str(e)}))

    async def _handle_player_join(self, player_id: str, message: Message):
        """Handle player join message."""
        if player_id not in self.players:
            raise InvalidPlayerDataError(f"Player {player_id} not found")
            
        player_name = message.data.get("name", f"Player_{player_id[:8]}")
        
        # Validate player name
        if not isinstance(player_name, str) or len(player_name.strip()) == 0:
            raise InvalidPlayerDataError("Invalid player name")
            
        if len(player_name) > 32:  # Reasonable limit
            player_name = player_name[:32]
            
        self.players[player_id].name = player_name.strip()
        
        # Send world initialization with player ID
        world_data = self.world.get_world_data()
        world_data["player_id"] = player_id  # Include player ID so client knows its own ID
        await self.send_to_client(player_id, create_world_init_message(world_data))
        
        # Send world chunks
        chunks_sent = 0
        for cx in range(WORLD_SIZE // DEFAULT_CHUNK_SIZE):
            for cz in range(WORLD_SIZE // DEFAULT_CHUNK_SIZE):
                chunk = self.world.get_world_chunk(cx, cz, DEFAULT_CHUNK_SIZE)
                if chunk["blocks"]:
                    await self.send_to_client(player_id, create_world_chunk_message(chunk))
                    chunks_sent += 1
                    
        self.logger.info(f"Sent {chunks_sent} chunks to player {player_name}")
        await self.broadcast_player_list()

    async def _handle_player_move(self, player_id: str, message: Message):
        """Handle player movement with server-side collision checking and response."""
        if player_id not in self.players:
            raise InvalidPlayerDataError(f"Player {player_id} not found")
            
        try:
            # Validate message format
            if "position" not in message.data:
                raise InvalidPlayerDataError("Missing required field: 'position'")
                
            position = message.data["position"]
            rotation = message.data.get("rotation", [0, 0])
            
            if not isinstance(position, (list, tuple)) or len(position) != 3:
                raise InvalidPlayerDataError("Invalid position format")
                
            if not isinstance(rotation, (list, tuple)) or len(rotation) != 2:
                raise InvalidPlayerDataError("Invalid rotation format")
            
            new_position = tuple(position)
            new_rotation = tuple(rotation)
            player = self.players[player_id]
            
            # ENHANCED DEBUG: Log detailed movement information
            old_position = player.position
            old_x, old_y, old_z = old_position
            new_x, new_y, new_z = new_position
            dx, dy, dz = new_x - old_x, new_y - old_y, new_z - old_z
            movement_distance = (dx**2 + dy**2 + dz**2)**0.5
            
            self.logger.info(f"🚶 PLAYER_MOVE DEBUG - Player {player.name or player_id[:8]}")
            self.logger.info(f"   Old position: {old_position}")
            self.logger.info(f"   New position: {new_position}")
            self.logger.info(f"   Delta: dx={dx:.2f}, dy={dy:.2f}, dz={dz:.2f}")
            self.logger.info(f"   Distance: {movement_distance:.2f}")
            self.logger.info(f"   Rotation: {rotation}")
            
            # Anti-cheat: validate reasonable movement distance from current position
            if abs(dx) > 50 or abs(dy) > 50 or abs(dz) > 50:
                self.logger.warning(f"❌ ANTI-CHEAT: Movement distance too large for {player.name}")
                # Send forbidden status with current position
                response = create_movement_response_message("forbidden", old_position, player.rotation)
                await self.send_to_client(player_id, response)
                return
            
            if not validate_position(new_position):
                self.logger.warning(f"❌ ANTI-CHEAT: Invalid position {new_position} for {player.name}")
                # Send forbidden status with current position
                response = create_movement_response_message("forbidden", old_position, player.rotation)
                await self.send_to_client(player_id, response)
                return
            
            # Server-side simple collision check
            if self._check_simple_collision(new_position, player_id):
                self.logger.warning(f"🚫 COLLISION: Player {player.name or player_id[:8]} blocked at {new_position}")
                # Send forbidden status with current (last valid) position
                response = create_movement_response_message("forbidden", old_position, player.rotation)
                await self.send_to_client(player_id, response)
                return
            
            # Check for player-to-player collision
            if self._check_player_collision(player_id, new_position):
                self.logger.warning(f"🚫 COLLISION: Player {player.name or player_id[:8]} blocked by other player at {new_position}")
                # Send forbidden status with current position
                response = create_movement_response_message("forbidden", old_position, player.rotation)
                await self.send_to_client(player_id, response)
                return
            
            # Movement is valid - update player state
            player.position = new_position
            player.rotation = new_rotation
            
            # Reset velocity when player makes deliberate movement to prevent physics interference
            player.velocity = [0.0, 0.0, 0.0]
            player.on_ground = True  # Assume player is on ground after movement
            player.last_move_time = time.time()  # Mark when player last moved voluntarily

            # Send 'ok' status with accepted position to the moving player
            response = create_movement_response_message("ok", new_position, new_rotation)
            await self.send_to_client(player_id, response)
            
            # ENHANCED BROADCAST: Send to other players with debug logging
            other_players_count = len([p for p in self.clients.keys() if p != player_id])
            self.logger.info(f"📡 Broadcasting position update to {other_players_count} other players")
            
            update_message = create_player_update_message(player)
            await self.broadcast_message(update_message, exclude_player=player_id)
            
        except KeyError as e:
            raise InvalidPlayerDataError(f"Missing required field: {e}")

    async def _handle_block_place(self, player_id: str, message: Message):
        """Handle block placement with validation."""
        try:
            position = tuple(message.data["position"])
            block_type = message.data["block_type"]
            
            if not isinstance(position, (list, tuple)) or len(position) != 3:
                raise InvalidWorldDataError("Invalid position format")
                
            if not validate_block_type(block_type):
                raise InvalidWorldDataError(f"Invalid block type: {block_type}")
                
            if self.world.add_block(position, block_type):
                update_message = create_world_update_message([
                    BlockUpdate(position, block_type, player_id)
                ])
                await self.broadcast_message(update_message)
                self.logger.info(f"Player {player_id} placed {block_type} at {position}")
            else:
                await self.send_to_client(player_id, Message(
                    MessageType.ERROR, 
                    {"message": "Cannot place block at this position"}
                ))
                
        except KeyError as e:
            raise InvalidWorldDataError(f"Missing required field: {e}")

    async def _handle_block_destroy(self, player_id: str, message: Message):
        """Handle block destruction with validation."""
        try:
            position = tuple(message.data["position"])
            
            if not isinstance(position, (list, tuple)) or len(position) != 3:
                raise InvalidWorldDataError("Invalid position format")
                
            if self.world.remove_block(position):
                update_message = create_world_update_message([
                    BlockUpdate(position, BlockType.AIR, player_id)
                ])
                await self.broadcast_message(update_message)
                self.logger.info(f"Player {player_id} destroyed block at {position}")
            else:
                await self.send_to_client(player_id, Message(
                    MessageType.ERROR, 
                    {"message": "Cannot destroy block at this position"}
                ))
                
        except KeyError as e:
            raise InvalidWorldDataError(f"Missing required field: {e}")

    async def _handle_chat_message(self, player_id: str, message: Message):
        """Handle chat messages with filtering."""
        try:
            text = message.data["text"]
            
            if not isinstance(text, str):
                raise InvalidPlayerDataError("Chat message must be a string")
                
            text = text.strip()
            if not text:
                return  # Ignore empty messages
                
            if len(text) > 256:  # Reasonable message limit
                text = text[:256]
                
            player_name = self.players.get(player_id, {}).name if player_id in self.players else "Unknown"
            
            chat_message = Message(MessageType.CHAT_BROADCAST, {
                "text": f"{player_name}: {text}"
            })
            await self.broadcast_message(chat_message)
            self.logger.info(f"Chat from {player_name}: {text}")
            
        except KeyError as e:
            raise InvalidPlayerDataError(f"Missing required field: {e}")

    async def handle_client(self, websocket):
        """Handle a client WebSocket connection."""
        player_id = await self.register_client(websocket)
        try:
            async for msg_str in websocket:
                try:
                    message = Message.from_json(msg_str)
                    message.player_id = player_id
                    await self.handle_client_message(player_id, message)
                except Exception as e:
                    self.logger.error(f"Error processing message from {player_id}: {e}")
                    await self.send_to_client(player_id, Message(
                        MessageType.ERROR, 
                        {"message": f"Message processing error: {str(e)}"}
                    ))
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Client {player_id} connection closed")
        except Exception as e:
            self.logger.error(f"Unexpected error with client {player_id}: {e}")
        finally:
            await self.unregister_client(player_id)

    async def start_server(self):
        """Start the WebSocket server."""
        self.running = True
        self.logger.info(f"Starting Minecraft server on {self.host}:{self.port}")
        
        try:
            # Start physics update loop
            physics_task = asyncio.create_task(self._physics_update_loop())
            
            server = await websockets.serve(self.handle_client, self.host, self.port)
            self.logger.info(f"Server started! Connect clients to ws://{self.host}:{self.port}")
            
            # Wait for the server to close
            await server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.running = False
            raise

    def stop_server(self):
        """Stop the server."""
        self.running = False
        self.logger.info("Server stop requested")


def main():
    """Main entry point for the server."""
    server = MinecraftServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        server.stop_server()
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server crashed: {e}")
        raise


if __name__ == "__main__":
    main()
