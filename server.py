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
    MessageType, BlockType, Message, PlayerState, BlockUpdate,
    create_world_init_message, create_world_chunk_message, 
    create_world_update_message, create_player_list_message
)

# ---------- Constants ----------
SECTOR_SIZE = 16
WORLD_SIZE = 128
DEFAULT_CHUNK_SIZE = 16
DEFAULT_SPAWN_POSITION = (64, 100, 64)  # High spawn position for gravity testing
WATER_LEVEL = 15
GRASS_LEVEL = 18

# Physics constants
GRAVITY = 20.0
TERMINAL_VELOCITY = 50.0
PLAYER_HEIGHT = 1.8
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

    def _check_ground_collision(self, position: Tuple[float, float, float]) -> bool:
        """Check if a position would collide with the ground/blocks."""
        x, y, z = position
        # Check block positions below the player
        for dy in range(int(PLAYER_HEIGHT) + 1):
            check_pos = (int(x), int(y - dy), int(z))
            if check_pos in self.world.world:
                return True
        return False

    def _apply_physics(self, player: PlayerState, dt: float) -> None:
        """Apply server-side physics to a player."""
        if player.flying:
            return  # No gravity when flying
        
        # Apply gravity
        player.velocity[1] -= GRAVITY * dt
        # Apply terminal velocity
        if player.velocity[1] < -TERMINAL_VELOCITY:
            player.velocity[1] = -TERMINAL_VELOCITY
        
        # Calculate new position
        new_x = player.position[0] + player.velocity[0] * dt
        new_y = player.position[1] + player.velocity[1] * dt  
        new_z = player.position[2] + player.velocity[2] * dt
        
        # Check collision with ground
        test_position = (new_x, new_y, new_z)
        if self._check_ground_collision(test_position):
            if player.velocity[1] < 0:  # Falling down
                # Find the highest block at this x,z position
                max_y = 0
                for check_y in range(256):
                    check_pos = (int(new_x), check_y, int(new_z))
                    if check_pos in self.world.world:
                        max_y = max(max_y, check_y)
                
                # Place player on top of the highest block
                new_y = max_y + 1
                player.velocity[1] = 0  # Stop falling
                player.on_ground = True
            else:
                # Hitting something while going up, stop vertical movement
                player.velocity[1] = 0
        else:
            player.on_ground = False
        
        # Update player position
        player.position = (new_x, new_y, new_z)

    async def _physics_update_loop(self):
        """Main physics update loop running at PHYSICS_TICK_RATE."""
        while self.running:
            current_time = time.time()
            dt = current_time - self.last_physics_update
            
            # Update physics for all players
            for player in self.players.values():
                self._apply_physics(player, dt)
            
            # Broadcast player updates
            await self._broadcast_physics_updates()
            
            self.last_physics_update = current_time
            
            # Sleep to maintain physics tick rate
            await asyncio.sleep(1.0 / PHYSICS_TICK_RATE)

    async def _broadcast_physics_updates(self):
        """Broadcast physics updates for all players."""
        for player in self.players.values():
            if player.id in self.clients:
                update_msg = Message(MessageType.PLAYER_UPDATE, player.to_dict())
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
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
            
        json_msg = message.to_json()
        disconnected = []
        
        for pid, ws in list(self.clients.items()):
            if exclude_player == pid:
                continue
                
            try:
                await ws.send(json_msg)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(pid)
            except Exception as e:
                self.logger.error(f"Error sending message to {pid}: {e}")
                disconnected.append(pid)
        
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
        
        # Send world initialization
        await self.send_to_client(player_id, create_world_init_message(self.world.get_world_data()))
        
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
        """Handle player movement with delta updates."""
        if player_id not in self.players:
            raise InvalidPlayerDataError(f"Player {player_id} not found")
            
        try:
            delta = message.data["delta"]
            rotation = message.data["rotation"]
            
            if not isinstance(delta, (list, tuple)) or len(delta) != 3:
                raise InvalidPlayerDataError("Invalid delta format")
                
            if not isinstance(rotation, (list, tuple)) or len(rotation) != 2:
                raise InvalidPlayerDataError("Invalid rotation format")
                
            # Validate movement limits (anti-cheat)
            dx, dy, dz = delta
            if abs(dx) > 10 or abs(dy) > 10 or abs(dz) > 10:  # Reasonable movement limits
                raise InvalidPlayerDataError("Movement delta too large")
            
            player = self.players[player_id]
            x, y, z = player.position
            new_position = (x + dx, y + dy, z + dz)
            
            if not validate_position(new_position):
                raise InvalidPlayerDataError("Invalid target position")
                
            player.position = new_position
            player.rotation = tuple(rotation)

            # Broadcast to other players
            await self.broadcast_message(
                Message(MessageType.PLAYER_UPDATE, player.to_dict()), 
                exclude_player=player_id
            )

            # Send updated position back to player
            await self.send_to_client(player_id, Message(MessageType.PLAYER_UPDATE, player.to_dict()))
            
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
