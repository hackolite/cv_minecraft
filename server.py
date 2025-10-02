"""
Minecraft Server - Server-side game world and client connections
"""

import asyncio
import logging
import random
import time
import uuid
import websockets
import threading
from typing import Dict, Tuple, Optional, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import io
from PIL import Image, ImageDraw

from noise_gen import NoiseGen
from protocol import (
    MessageType, BlockType, Message, PlayerState, BlockUpdate, Cube,
    create_world_init_message, create_world_chunk_message, 
    create_world_update_message, create_player_list_message,
    create_player_update_message
)
from minecraft_physics import (
    MinecraftCollisionDetector, MinecraftPhysics,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY,
    unified_check_collision, unified_check_player_collision
)
from cube_manager import cube_manager
# from user_manager import user_manager, CameraUser  # Removed as per IMPLEMENTATION_SUMMARY.md

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
CAMERA = tex_coords((0, 3), (0, 3), (0, 3))  # Camera block - distinctive texture

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
        BlockType.WATER, BlockType.CAMERA, BlockType.AIR
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
        
        # Add camera blocks at strategic locations for all users to see
        spawn_x, spawn_y, spawn_z = DEFAULT_SPAWN_POSITION
        camera_locations = [
            (spawn_x + 5, spawn_y + 2, spawn_z),      # East of spawn, elevated
            (spawn_x - 5, spawn_y + 2, spawn_z),      # West of spawn, elevated  
            (spawn_x, spawn_y + 2, spawn_z + 5),      # South of spawn, elevated
            (spawn_x, spawn_y + 2, spawn_z - 5),      # North of spawn, elevated
            (spawn_x, spawn_y + 5, spawn_z),          # Directly above spawn
        ]
        
        for camera_pos in camera_locations:
            if self._add_block_internal(camera_pos, BlockType.CAMERA):
                blocks_created += 1
                logging.info(f"Added camera block at position {camera_pos}")
        
        logging.info(f"Enhanced world initialized with {blocks_created} blocks including water, sand, grass, stone, trees, and {len(camera_locations)} camera blocks")

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
        self.user_cubes: Dict[str, Cube] = {}  # Player ID -> Cube mapping
        self.rtsp_users: Dict[str, Any] = {}  # Kept for compatibility but unused
        self.running = False
        self.logger = logging.getLogger(__name__)
        # Physics tick timing
        self.last_physics_update = time.time()
        
        
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
        """Register a new client connection and create a user cube."""
        player_id = str(uuid.uuid4())
        self.clients[player_id] = websocket
        
        # Create a new connected player
        self.players[player_id] = PlayerState(player_id, DEFAULT_SPAWN_POSITION, (0, 0), is_connected=True, is_rtsp_user=False)
        
        # Create a cube for this user with dedicated port
        user_cube = Cube(
            cube_id=f"user_{player_id[:8]}", 
            position=DEFAULT_SPAWN_POSITION
        )
        
        # Add cube to user cubes
        self.user_cubes[player_id] = user_cube
        self.logger.info(f"Player {player_id} connected with cube")
        
        self.logger.info(f"Player {player_id} connected from {websocket.remote_address}")
        return player_id

    async def unregister_client(self, player_id: str):
        """Unregister a client connection and clean up cube."""
        if player_id in self.clients:
            self.clients.pop(player_id, None)
            
            # Clean up user cube
            if player_id in self.user_cubes:
                user_cube = self.user_cubes[player_id]
                # Clean up window if it exists
                if user_cube.window:
                    user_cube.window.close()
                    user_cube.window = None
                del self.user_cubes[player_id]
                self.logger.info(f"Cleaned up cube for player {player_id}")
            
            # Only remove connected players, not RTSP users
            player = self.players.get(player_id)
            if player and not player.is_rtsp_user:
                self.players.pop(player_id, None)
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
        # Include both connected players and RTSP users in the player list
        all_players = list(self.players.values())
        self.logger.info(f"Broadcasting player list with {len(all_players)} players")
        for player in all_players:
            self.logger.info(f"  - {player.name} (RTSP: {player.is_rtsp_user}, Connected: {player.is_connected})")
        message = create_player_list_message(all_players)
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
        """Handle player movement with absolute position updates only."""
        if player_id not in self.players:
            raise InvalidPlayerDataError(f"Player {player_id} not found")
            
        try:
            rotation = message.data["rotation"]
            
            if not isinstance(rotation, (list, tuple)) or len(rotation) != 2:
                raise InvalidPlayerDataError("Invalid rotation format")
            
            player = self.players[player_id]
            
            # Only handle absolute position-based movement
            if "position" not in message.data:
                raise InvalidPlayerDataError("Missing required field: 'position' must be provided")
                
            position = message.data["position"]
            
            if not isinstance(position, (list, tuple)) or len(position) != 3:
                raise InvalidPlayerDataError("Invalid position format")
                
            new_position = tuple(position)
            
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
                raise InvalidPlayerDataError("Movement distance too large")
            
            if not validate_position(new_position):
                self.logger.warning(f"❌ ANTI-CHEAT: Invalid position {new_position} for {player.name}")
                raise InvalidPlayerDataError("Invalid target position")
            
            # Check for collision with blocks
            if self._check_ground_collision(new_position):
                self.logger.warning(f"🚫 COLLISION: Player {player.name or player_id[:8]} blocked by blocks at {new_position}")
                raise InvalidPlayerDataError("Movement blocked by blocks")
            
            # Check for player-to-player collision
            if self._check_player_collision(player_id, new_position):
                self.logger.warning(f"🚫 COLLISION: Player {player.name or player_id[:8]} blocked by other player at {new_position}")
                raise InvalidPlayerDataError("Movement blocked by another player")
                
            # Enhanced position validation
            if not isinstance(new_position, (tuple, list)) or len(new_position) != 3:
                self.logger.warning(f"❌ VALIDATION: Invalid position format {new_position} for {player.name}")
                raise InvalidPlayerDataError("Position must be a 3-element array")
            
            # Validate position coordinates are numeric
            x, y, z = new_position
            if not all(isinstance(coord, (int, float)) for coord in [x, y, z]):
                self.logger.warning(f"❌ VALIDATION: Non-numeric position coordinates {new_position} for {player.name}")
                raise InvalidPlayerDataError("Position coordinates must be numeric")
            
            # Validate rotation
            if not isinstance(rotation, (tuple, list)) or len(rotation) != 2:
                self.logger.warning(f"❌ VALIDATION: Invalid rotation format {rotation} for {player.name}")
                raise InvalidPlayerDataError("Rotation must be a 2-element array")
            
            h, v = rotation
            if not all(isinstance(angle, (int, float)) for angle in [h, v]):
                self.logger.warning(f"❌ VALIDATION: Non-numeric rotation angles {rotation} for {player.name}")
                raise InvalidPlayerDataError("Rotation angles must be numeric")
            
            player.position = new_position
            player.rotation = tuple(rotation)
            
            # Reset velocity when player makes deliberate movement to prevent physics interference
            # This prevents gravity from immediately affecting the player's intended position
            player.velocity = [0.0, 0.0, 0.0]
            player.on_ground = True  # Assume player is on ground after movement
            player.last_move_time = time.time()  # Mark when player last moved voluntarily

            # ENHANCED BROADCAST: Send to other players with debug logging
            other_players_count = len([p for p in self.clients.keys() if p != player_id])
            self.logger.info(f"📡 Broadcasting position update to {other_players_count} other players")
            
            update_message = create_player_update_message(player)
            await self.broadcast_message(update_message, exclude_player=player_id)

            # Send updated position back to player (confirmation)
            self.logger.debug(f"✅ Sending position confirmation to {player.name}")
            await self.send_to_client(player_id, update_message)
            
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


# ---------- HTTP API Server ----------

# Create FastAPI app for HTTP API endpoints
api_app = FastAPI(title="Minecraft Server API", version="1.0.0")

# Global reference to the Minecraft server instance
_minecraft_server: Optional[MinecraftServer] = None

def set_minecraft_server(server: MinecraftServer):
    """Set the global Minecraft server instance for API access."""
    global _minecraft_server
    _minecraft_server = server

@api_app.get("/")
async def api_home():
    """API home page with available endpoints."""
    return {
        "name": "Minecraft Server API",
        "version": "1.0.0",
        "endpoints": {
            "cameras": "/api/cameras",
            "users": "/api/users", 
            "blocks": "/api/blocks",
            "render": "/api/render"
        }
    }

@api_app.get("/api/cameras")
async def get_cameras():
    """Get list of all camera blocks in the world."""
    if _minecraft_server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    cameras = []
    for position, block_type in _minecraft_server.world.world.items():
        if block_type == BlockType.CAMERA:
            cameras.append({
                "position": list(position),
                "block_type": block_type
            })
    
    return {
        "count": len(cameras),
        "cameras": cameras
    }

@api_app.get("/api/users")
async def get_users():
    """Get list of all users with their positions and other information."""
    if _minecraft_server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    users = []
    for player_id, player in _minecraft_server.players.items():
        users.append({
            "id": player.id,
            "name": player.name,
            "position": list(player.position),
            "rotation": list(player.rotation),
            "flying": player.flying,
            "sprinting": player.sprinting,
            "on_ground": player.on_ground,
            "velocity": list(player.velocity),
            "is_connected": player.is_connected,
            "is_rtsp_user": player.is_rtsp_user
        })
    
    return {
        "count": len(users),
        "users": users
    }

@api_app.get("/api/blocks")
async def get_blocks(
    min_x: int = 0, 
    min_y: int = 0, 
    min_z: int = 0,
    max_x: int = WORLD_SIZE,
    max_y: int = 256,
    max_z: int = WORLD_SIZE
):
    """Get blocks in a specific area defined by min/max coordinates."""
    if _minecraft_server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    # Validate bounds
    if not (0 <= min_x < WORLD_SIZE and 0 <= max_x <= WORLD_SIZE):
        raise HTTPException(status_code=400, detail="Invalid X bounds")
    if not (0 <= min_y < 256 and 0 <= max_y <= 256):
        raise HTTPException(status_code=400, detail="Invalid Y bounds")
    if not (0 <= min_z < WORLD_SIZE and 0 <= max_z <= WORLD_SIZE):
        raise HTTPException(status_code=400, detail="Invalid Z bounds")
    
    blocks = []
    for position, block_type in _minecraft_server.world.world.items():
        x, y, z = position
        if (min_x <= x < max_x and 
            min_y <= y < max_y and 
            min_z <= z < max_z):
            blocks.append({
                "position": list(position),
                "block_type": block_type
            })
    
    return {
        "count": len(blocks),
        "bounds": {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z]
        },
        "blocks": blocks
    }

@api_app.post("/api/render")
async def render_view(
    position: List[float],
    rotation: List[float],
    width: int = 640,
    height: int = 480,
    fov: float = 65.0,
    render_distance: int = 50
):
    """
    Reconstruct view as an image from a specific position and rotation.
    
    Parameters:
    - position: [x, y, z] coordinates
    - rotation: [horizontal, vertical] angles in degrees
    - width: image width in pixels (default 640)
    - height: image height in pixels (default 480)
    - fov: field of view in degrees (default 65)
    - render_distance: max distance to render blocks (default 50)
    
    Returns: PNG image
    """
    if _minecraft_server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    # Validate inputs
    if not isinstance(position, list) or len(position) != 3:
        raise HTTPException(status_code=400, detail="Position must be [x, y, z]")
    if not isinstance(rotation, list) or len(rotation) != 2:
        raise HTTPException(status_code=400, detail="Rotation must be [horizontal, vertical]")
    
    if width < 1 or width > 4096:
        raise HTTPException(status_code=400, detail="Width must be between 1 and 4096")
    if height < 1 or height > 4096:
        raise HTTPException(status_code=400, detail="Height must be between 1 and 4096")
    
    # Get blocks within render distance
    x, y, z = position
    nearby_blocks = []
    
    for pos, block_type in _minecraft_server.world.world.items():
        bx, by, bz = pos
        # Calculate distance
        distance = ((bx - x)**2 + (by - y)**2 + (bz - z)**2)**0.5
        if distance <= render_distance:
            nearby_blocks.append({
                "position": list(pos),
                "block_type": block_type,
                "distance": distance
            })
    
    # Sort by distance (closer first)
    nearby_blocks.sort(key=lambda b: b["distance"])
    
    # Create a simple visualization (placeholder - actual 3D rendering would be more complex)
    img = Image.new('RGB', (width, height), (135, 206, 235))  # Sky blue background
    draw = ImageDraw.Draw(img)
    
    # Draw text with camera info
    info_text = f"Pos: ({x:.1f}, {y:.1f}, {z:.1f})\nRot: ({rotation[0]:.1f}, {rotation[1]:.1f})\nBlocks: {len(nearby_blocks)}"
    draw.text((10, 10), info_text, fill=(255, 255, 255))
    
    # Draw a simple representation of nearby blocks
    # This is a placeholder - a real implementation would do proper 3D projection
    for i, block in enumerate(nearby_blocks[:100]):  # Limit to 100 closest blocks
        # Simple 2D projection based on distance
        bx, by, bz = block["position"]
        dx, dy, dz = bx - x, by - y, bz - z
        
        # Simple projection (not accurate but gives an idea)
        screen_x = int(width / 2 + dx * 10)
        screen_y = int(height / 2 - dy * 10)
        
        if 0 <= screen_x < width and 0 <= screen_y < height:
            # Draw a small square for each block
            size = max(1, int(10 / (1 + block["distance"] / 10)))
            color = _get_block_color(block["block_type"])
            draw.rectangle(
                [screen_x - size, screen_y - size, screen_x + size, screen_y + size],
                fill=color
            )
    
    # Convert to PNG bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return StreamingResponse(img_buffer, media_type="image/png")

def _get_block_color(block_type: str) -> Tuple[int, int, int]:
    """Get RGB color for a block type."""
    colors = {
        BlockType.GRASS: (34, 139, 34),
        BlockType.SAND: (238, 214, 175),
        BlockType.BRICK: (178, 34, 34),
        BlockType.STONE: (128, 128, 128),
        BlockType.WOOD: (139, 69, 19),
        BlockType.LEAF: (0, 128, 0),
        BlockType.WATER: (0, 105, 148),
        BlockType.CAMERA: (255, 0, 255),
    }
    return colors.get(block_type, (200, 200, 200))

async def run_http_api_server(host: str = '0.0.0.0', port: int = 8000):
    """Run the HTTP API server in the background."""
    config = uvicorn.Config(api_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def start_http_api_server_thread(host: str = '0.0.0.0', port: int = 8000):
    """Start the HTTP API server in a separate thread."""
    def run_server():
        asyncio.run(run_http_api_server(host, port))
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logging.info(f"HTTP API server started on http://{host}:{port}")
    logging.info(f"API documentation available at http://{host}:{port}/docs")
    return thread


def main():
    """Main entry point for the server."""
    server = MinecraftServer()
    
    # Set global server instance for API access
    set_minecraft_server(server)
    
    # Start HTTP API server in background thread
    start_http_api_server_thread(host='0.0.0.0', port=8000)
    
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
