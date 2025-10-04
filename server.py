"""
Minecraft Server - Server-side game world and client connections
"""

import asyncio
import logging
import random
import time
import uuid
import websockets
from typing import Dict, Tuple, Optional, List, Any

from noise_gen import NoiseGen
from protocol import (
    MessageType, BlockType, Message, PlayerState, BlockUpdate, Cube,
    create_world_init_message, create_world_chunk_message, 
    create_world_update_message, create_player_list_message,
    create_player_update_message, create_cameras_list_message,
    create_users_list_message, create_blocks_list_message
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

# Water collision configuration
# When True, water blocks are solid (players walk on top of water)
# When False, water blocks have no collision (players can pass through water)
WATER_COLLISION_ENABLED = True

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
CAT = tex_coords((1, 3), (1, 3), (1, 3))  # Cat block

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
        BlockType.WATER, BlockType.CAMERA, BlockType.USER, BlockType.AIR,
        BlockType.CAT
    }
    return block_type in allowed_types


def get_block_collision(block_type: str) -> bool:
    """Get whether a block type has collision."""
    # Air never has collision
    if block_type == BlockType.AIR:
        return False
    
    # Water collision is configurable
    if block_type == BlockType.WATER:
        return WATER_COLLISION_ENABLED
    
    # All other blocks have collision
    return True


def create_block_data(block_type: str, block_id: Optional[str] = None, owner: Optional[str] = None) -> Dict[str, Any]:
    """Create block data dictionary with all required attributes.
    
    Args:
        block_type: Type of block (grass, camera, etc.)
        block_id: Unique identifier for camera and user blocks
        owner: Player ID who placed the block (for camera blocks)
    """
    return {
        "type": block_type,
        "collision": get_block_collision(block_type),
        "block_id": block_id,  # Only populated for camera and user types
        "owner": owner  # Only populated for camera blocks to track who placed it
    }

# ---------- Game World ----------

class GameWorld:
    """Game world management with spatial indexing and validation."""
    
    def __init__(self, reset_to_natural: bool = False):
        self.world = {}       # position -> block data dict {type, collision, block_id}
        self.sectors = {}     # sector -> list of positions
        self.block_id_map = {}  # block_id -> position (for camera and user blocks)
        self._initialize_world()
        
        # Reset to natural terrain if requested
        if reset_to_natural:
            self.reset_to_natural_terrain()

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
        
        for i, camera_pos in enumerate(camera_locations):
            # Assign block_id to camera blocks
            camera_block_id = f"camera_{i}"
            if self._add_block_internal(camera_pos, BlockType.CAMERA, block_id=camera_block_id):
                blocks_created += 1
                logging.info(f"Added camera block at position {camera_pos} with block_id {camera_block_id}")
        
        logging.info(f"Enhanced world initialized with {blocks_created} blocks including water, sand, grass, stone, trees, and {len(camera_locations)} camera blocks")

    def _add_block_internal(self, position: Tuple[int, int, int], block_type: str, block_id: Optional[str] = None, owner: Optional[str] = None) -> bool:
        """Internal method to add blocks without validation (for world generation)."""
        if position in self.world:
            return False
        
        x, y, z = position
        # Ensure position is within bounds before adding
        if not (0 <= x < WORLD_SIZE and y >= 0 and y < 256 and 0 <= z < WORLD_SIZE):
            return False
        
        # Create block data with collision, block_id, and owner attributes
        block_data = create_block_data(block_type, block_id, owner)
        self.world[position] = block_data
        self.sectors.setdefault(sectorize(position), []).append(position)
        
        # Track block_id if provided (for camera and user blocks)
        if block_id:
            self.block_id_map[block_id] = position
            
        return True

    def add_block(self, position: Tuple[int, int, int], block_type: str, block_id: Optional[str] = None, owner: Optional[str] = None) -> bool:
        """Add a block at the specified position."""
        if not validate_position(position):
            logging.warning(f"Invalid position for block placement: {position}")
            return False
            
        if not validate_block_type(block_type):
            logging.warning(f"Invalid block type: {block_type}")
            return False
            
        if position in self.world:
            return False  # Block already exists
        
        # Create block data with collision, block_id, and owner attributes
        block_data = create_block_data(block_type, block_id, owner)
        self.world[position] = block_data
        self.sectors.setdefault(sectorize(position), []).append(position)
        
        # Track block_id if provided (for camera and user blocks)
        if block_id:
            self.block_id_map[block_id] = position
            
        return True

    def remove_block(self, position: Tuple[int, int, int]) -> bool:
        """Remove a block at the specified position."""
        if not validate_position(position):
            logging.warning(f"Invalid position for block removal: {position}")
            return False
            
        if position not in self.world:
            return False  # No block to remove
        
        block_data = self.world[position]
        block_type = block_data.get("type") if isinstance(block_data, dict) else block_data
        
        # Prevent removal of stone blocks (bedrock protection)
        if block_type == BlockType.STONE:
            return False
        
        # Remove block_id mapping if it exists
        if isinstance(block_data, dict) and block_data.get("block_id"):
            block_id = block_data["block_id"]
            if block_id in self.block_id_map:
                del self.block_id_map[block_id]
            
        del self.world[position]
        sector = sectorize(position)
        if sector in self.sectors and position in self.sectors[sector]:
            self.sectors[sector].remove(position)
        return True

    def get_block(self, position: Tuple[int, int, int]) -> Optional[str]:
        """Get block type at specified position."""
        block_data = self.world.get(position)
        if block_data:
            # Handle both old string format and new dict format for compatibility
            if isinstance(block_data, dict):
                return block_data.get("type")
            return block_data
        return None

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
        
        for pos, block_data in self.world.items():
            x, y, z = pos
            if start_x <= x < end_x and start_z <= z < end_z:
                # Handle both old string format and new dict format
                if isinstance(block_data, dict):
                    block_type = block_data.get("type")
                else:
                    block_type = block_data
                blocks[f"{x},{y},{z}"] = block_type
                
        return {
            "chunk_x": chunk_x, 
            "chunk_z": chunk_z, 
            "blocks": blocks
        }

    def get_cameras(self) -> List[Dict[str, Any]]:
        """Get all camera blocks in the world."""
        cameras = []
        for pos, block_data in self.world.items():
            # Handle both old string format and new dict format
            if isinstance(block_data, dict):
                block_type = block_data.get("type")
                block_id = block_data.get("block_id")
                collision = block_data.get("collision", True)
                owner = block_data.get("owner")
            else:
                block_type = block_data
                block_id = None
                collision = get_block_collision(block_type)
                owner = None
            
            if block_type == BlockType.CAMERA:
                x, y, z = pos
                cameras.append({
                    "position": [x, y, z],
                    "block_type": block_type,
                    "block_id": block_id,
                    "collision": collision,
                    "owner": owner
                })
        return cameras

    def get_blocks_in_region(self, center: Tuple[float, float, float], radius: float) -> List[Dict[str, Any]]:
        """Get all blocks within a certain radius of a center point."""
        blocks = []
        cx, cy, cz = center
        
        for pos, block_data in self.world.items():
            x, y, z = pos
            # Calculate distance from center
            distance = ((x - cx)**2 + (y - cy)**2 + (z - cz)**2)**0.5
            
            if distance <= radius:
                # Handle both old string format and new dict format
                if isinstance(block_data, dict):
                    block_type = block_data.get("type")
                    block_id = block_data.get("block_id")
                    collision = block_data.get("collision", True)
                else:
                    block_type = block_data
                    block_id = None
                    collision = get_block_collision(block_type)
                
                blocks.append({
                    "position": [x, y, z],
                    "block_type": block_type,
                    "block_id": block_id,
                    "collision": collision
                })
        
        return blocks

    def get_blocks_in_view(self, position: Tuple[float, float, float], 
                           rotation: Tuple[float, float], 
                           view_distance: float = 50.0,
                           block_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get blocks visible from a position with given rotation (simplified view frustum).
        
        If block_id is provided, uses that block's position instead of the position parameter.
        """
        import math
        
        # If block_id is provided, look up the position
        if block_id:
            if block_id in self.block_id_map:
                position = self.block_id_map[block_id]
                # Convert to float tuple
                position = tuple(float(x) for x in position)
            else:
                # Block ID not found, return empty list
                logging.warning(f"Block ID {block_id} not found in block_id_map")
                return []
        
        blocks = []
        px, py, pz = position
        h_rotation, v_rotation = rotation  # horizontal and vertical rotation
        
        # For simplicity, use a cone-based approximation
        # This is a simplified version - a proper implementation would use a view frustum
        for pos, block_data in self.world.items():
            x, y, z = pos
            
            # Vector from position to block
            dx, dy, dz = x - px, y - py, z - pz
            distance = (dx**2 + dy**2 + dz**2)**0.5
            
            if distance > view_distance or distance < 0.1:
                continue
            
            # Handle both old string format and new dict format
            if isinstance(block_data, dict):
                block_type = block_data.get("type")
                blk_id = block_data.get("block_id")
                collision = block_data.get("collision", True)
            else:
                block_type = block_data
                blk_id = None
                collision = get_block_collision(block_type)
            
            # Calculate angle to block (simplified)
            # In a real implementation, this would properly check against the view frustum
            blocks.append({
                "position": [x, y, z],
                "block_type": block_type,
                "block_id": blk_id,
                "collision": collision,
                "distance": distance
            })
        
        return blocks
    
    def add_user_block(self, player_id: str, position: Tuple[float, float, float]) -> bool:
        """Add or update a user block at the player's position."""
        # Normalize position to block coordinates
        block_pos = normalize(position)
        
        # Remove old user block if player moved to a different block position
        if player_id in self.block_id_map:
            old_pos = self.block_id_map[player_id]
            if old_pos != block_pos and old_pos in self.world:
                old_block = self.world[old_pos]
                # Only remove if it's a user block with this player's ID
                if (isinstance(old_block, dict) and 
                    old_block.get("type") == BlockType.USER and 
                    old_block.get("block_id") == player_id):
                    del self.world[old_pos]
                    sector = sectorize(old_pos)
                    if sector in self.sectors and old_pos in self.sectors[sector]:
                        self.sectors[sector].remove(old_pos)
        
        # Don't overwrite existing solid blocks with user blocks
        if block_pos in self.world:
            existing = self.world[block_pos]
            if isinstance(existing, dict):
                existing_type = existing.get("type")
            else:
                existing_type = existing
            # Only overwrite if it's air, water, or another user block
            if existing_type not in {BlockType.AIR, BlockType.WATER, BlockType.USER}:
                return False
        
        # Add user block
        block_data = create_block_data(BlockType.USER, block_id=player_id)
        self.world[block_pos] = block_data
        self.sectors.setdefault(sectorize(block_pos), []).append(block_pos)
        self.block_id_map[player_id] = block_pos
        return True
    
    def remove_user_block(self, player_id: str) -> bool:
        """Remove a user block."""
        if player_id not in self.block_id_map:
            return False
        
        position = self.block_id_map[player_id]
        if position in self.world:
            block_data = self.world[position]
            # Verify it's actually a user block with this player's ID
            if (isinstance(block_data, dict) and 
                block_data.get("type") == BlockType.USER and 
                block_data.get("block_id") == player_id):
                del self.world[position]
                sector = sectorize(position)
                if sector in self.sectors and position in self.sectors[sector]:
                    self.sectors[sector].remove(position)
        
        del self.block_id_map[player_id]
        return True

    def reset_to_natural_terrain(self) -> int:
        """Remove all blocks that have owners, block_ids (cameras, users), or are player-added.
        
        Keeps only natural terrain blocks (grass, sand, stone, water, wood, leaf).
        Returns the number of blocks removed.
        """
        # Natural terrain block types that should be kept
        natural_blocks = {
            BlockType.GRASS,
            BlockType.SAND,
            BlockType.STONE,
            BlockType.WATER,
            BlockType.WOOD,
            BlockType.LEAF
        }
        
        blocks_to_remove = []
        
        # Identify blocks to remove
        for position, block_data in self.world.items():
            if isinstance(block_data, dict):
                block_type = block_data.get("type")
                block_id = block_data.get("block_id")
                owner = block_data.get("owner")
                
                # Remove if:
                # 1. Block has an owner (player-placed camera)
                # 2. Block has a block_id (camera or user block)
                # 3. Block type is not in natural terrain
                if owner is not None or block_id is not None or block_type not in natural_blocks:
                    blocks_to_remove.append(position)
            else:
                # Old format - if it's not in natural blocks, remove it
                block_type = block_data
                if block_type not in natural_blocks:
                    blocks_to_remove.append(position)
        
        # Remove identified blocks
        removed_count = 0
        for position in blocks_to_remove:
            block_data = self.world[position]
            
            # Remove from block_id_map if it has a block_id
            if isinstance(block_data, dict) and block_data.get("block_id"):
                block_id = block_data["block_id"]
                if block_id in self.block_id_map:
                    del self.block_id_map[block_id]
            
            # Remove from world
            del self.world[position]
            
            # Remove from sectors
            sector = sectorize(position)
            if sector in self.sectors and position in self.sectors[sector]:
                self.sectors[sector].remove(position)
            
            removed_count += 1
        
        logging.info(f"Reset world to natural terrain: removed {removed_count} blocks")
        return removed_count

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
    
    def __init__(self, host: str = 'localhost', port: int = 8765, reset_world: bool = False):
        self.host = host
        self.port = port
        self.world = GameWorld(reset_to_natural=reset_world)
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.players: Dict[str, PlayerState] = {}
        self.user_cubes: Dict[str, Cube] = {}  # Player ID -> Cube mapping
        self.camera_cubes: Dict[str, Cube] = {}  # Camera block_id -> Cube mapping
        self.rtsp_users: Dict[str, Any] = {}  # Kept for compatibility but unused
        self.running = False
        self.logger = logging.getLogger(__name__)
        # Physics tick timing
        self.last_physics_update = time.time()
        # Camera counter for auto-generating camera block_ids (starts at 5 since 0-4 are used in world init)
        self._camera_counter = 5
        
        
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
            
            # Remove user block
            self.world.remove_user_block(player_id)
            
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
            
            elif message.type == MessageType.GET_CAMERAS_LIST:
                await self._handle_get_cameras_list(player_id, message)
            
            elif message.type == MessageType.GET_USERS_LIST:
                await self._handle_get_users_list(player_id, message)
            
            elif message.type == MessageType.GET_BLOCKS_LIST:
                await self._handle_get_blocks_list(player_id, message)
                
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
        
        # Add user block for this player
        player = self.players[player_id]
        self.world.add_user_block(player_id, player.position)
        
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
            
            # Update user block position
            self.world.add_user_block(player_id, new_position)
            
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
            
            # Auto-generate block_id and owner for camera blocks
            block_id = None
            owner = None
            if block_type == BlockType.CAMERA:
                block_id = f"camera_{self._camera_counter}"
                self._camera_counter += 1
                owner = player_id  # Track who placed this camera
                self.logger.info(f"Auto-generated block_id '{block_id}' for camera block placed by {player_id}")
                
                # Create a Cube instance for this camera (like user cubes)
                camera_cube = Cube(
                    cube_id=block_id,
                    position=position,
                    cube_type="camera"
                )
                self.camera_cubes[block_id] = camera_cube
                self.logger.info(f"Created camera cube '{block_id}' owned by player {player_id}")
                
            if self.world.add_block(position, block_type, block_id=block_id, owner=owner):
                update_message = create_world_update_message([
                    BlockUpdate(position, block_type, player_id)
                ])
                await self.broadcast_message(update_message)
                self.logger.info(f"Player {player_id} placed {block_type} at {position}" + 
                               (f" with block_id {block_id}" if block_id else ""))
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
            
            # Get block data before removing to check if it's a camera
            block_data = self.world.world.get(position)
            camera_block_id = None
            if isinstance(block_data, dict):
                if block_data.get("type") == BlockType.CAMERA:
                    camera_block_id = block_data.get("block_id")
                
            if self.world.remove_block(position):
                # Clean up camera cube if this was a camera block
                if camera_block_id and camera_block_id in self.camera_cubes:
                    camera_cube = self.camera_cubes[camera_block_id]
                    # Clean up window if it exists
                    if camera_cube.window:
                        camera_cube.window.close()
                        camera_cube.window = None
                    del self.camera_cubes[camera_block_id]
                    self.logger.info(f"Cleaned up camera cube '{camera_block_id}'")
                    
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

    async def _handle_get_cameras_list(self, player_id: str, message: Message):
        """Handle request for list of camera blocks."""
        try:
            cameras = self.world.get_cameras()
            self.logger.info(f"Sending {len(cameras)} camera blocks to player {player_id}")
            response = create_cameras_list_message(cameras)
            await self.send_to_client(player_id, response)
        except Exception as e:
            self.logger.error(f"Error getting cameras list: {e}")
            raise InvalidWorldDataError(f"Failed to get cameras list: {e}")

    async def _handle_get_users_list(self, player_id: str, message: Message):
        """Handle request for list of users with their positions and info."""
        try:
            users = []
            for pid, player in self.players.items():
                user_info = {
                    "id": pid,
                    "name": player.name,
                    "position": list(player.position),
                    "rotation": list(player.rotation),
                    "is_connected": player.is_connected,
                    "is_rtsp_user": player.is_rtsp_user
                }
                users.append(user_info)
            
            self.logger.info(f"Sending {len(users)} users to player {player_id}")
            response = create_users_list_message(users)
            await self.send_to_client(player_id, response)
        except Exception as e:
            self.logger.error(f"Error getting users list: {e}")
            raise InvalidPlayerDataError(f"Failed to get users list: {e}")

    async def _handle_get_blocks_list(self, player_id: str, message: Message):
        """Handle request for list of blocks (optionally filtered by region or view).
        
        Supports querying by block_id for view queries.
        """
        try:
            # Check if request specifies a filter
            query_type = message.data.get("query_type", "region")
            
            if query_type == "region":
                # Get blocks in a region around a center point
                center = message.data.get("center", DEFAULT_SPAWN_POSITION)
                radius = message.data.get("radius", 50.0)
                
                if not isinstance(center, (list, tuple)) or len(center) != 3:
                    raise InvalidWorldDataError("Invalid center position")
                
                blocks = self.world.get_blocks_in_region(tuple(center), radius)
                
            elif query_type == "view":
                # Get blocks visible from a specific position and rotation
                # Can use block_id to specify the viewing position instead of explicit coordinates
                block_id = message.data.get("block_id")
                position = message.data.get("position")
                rotation = message.data.get("rotation")
                view_distance = message.data.get("view_distance", 50.0)
                
                # If block_id is provided, it takes precedence over position
                if block_id:
                    if not rotation:
                        raise InvalidWorldDataError("Rotation required for view query")
                    
                    if not isinstance(rotation, (list, tuple)) or len(rotation) != 2:
                        raise InvalidWorldDataError("Invalid rotation format")
                    
                    # Position will be looked up from block_id in get_blocks_in_view
                    blocks = self.world.get_blocks_in_view(
                        (0, 0, 0),  # Dummy position, will be replaced by block_id lookup
                        tuple(rotation),
                        view_distance,
                        block_id=block_id
                    )
                else:
                    # Use explicit position
                    if not position or not rotation:
                        raise InvalidWorldDataError("Position and rotation required for view query")
                    
                    if not isinstance(position, (list, tuple)) or len(position) != 3:
                        raise InvalidWorldDataError("Invalid position format")
                    
                    if not isinstance(rotation, (list, tuple)) or len(rotation) != 2:
                        raise InvalidWorldDataError("Invalid rotation format")
                    
                    blocks = self.world.get_blocks_in_view(
                        tuple(position), 
                        tuple(rotation), 
                        view_distance
                    )
            else:
                raise InvalidWorldDataError(f"Unknown query_type: {query_type}")
            
            self.logger.info(f"Sending {len(blocks)} blocks to player {player_id}")
            response = create_blocks_list_message(blocks)
            await self.send_to_client(player_id, response)
            
        except KeyError as e:
            raise InvalidWorldDataError(f"Missing required field: {e}")
        except Exception as e:
            self.logger.error(f"Error getting blocks list: {e}")
            raise InvalidWorldDataError(f"Failed to get blocks list: {e}")

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
    import argparse
    
    parser = argparse.ArgumentParser(description='Serveur Minecraft - Serveur de jeu multijoueur')
    parser.add_argument('--host', type=str, default='localhost', 
                        help='Adresse hôte du serveur (défaut: localhost)')
    parser.add_argument('--port', type=int, default=8765,
                        help='Port du serveur (défaut: 8765)')
    parser.add_argument('--reset-world', action='store_true',
                        help='Réinitialiser le monde au terrain naturel (supprime tous les blocs avec propriétaire, caméras, utilisateurs et blocs ajoutés)')
    
    args = parser.parse_args()
    
    if args.reset_world:
        logging.info("🔄 Mode réinitialisation du monde activé - suppression des blocs non-naturels au démarrage")
    
    server = MinecraftServer(host=args.host, port=args.port, reset_world=args.reset_world)
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
