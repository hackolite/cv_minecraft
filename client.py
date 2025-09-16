"""
Minecraft Client - Handles rendering and user interaction.
Modified from the original monolithic minecraft.py to work with a server.
"""

from __future__ import division

import sys
import math
import random
import time
import asyncio
import threading
import websockets
import json
from collections import deque

import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

# Import missing GL constants if not available from pyglet
try:
    GL_FOG
except NameError:
    try:
        from OpenGL.GL import (
            GL_FOG, GL_FOG_COLOR, GL_FOG_HINT, GL_DONT_CARE,
            GL_FOG_MODE, GL_LINEAR, GL_FOG_START, GL_FOG_END,
            GL_QUADS, GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW,
            GL_FRONT_AND_BACK, GL_LINE, GL_FILL, GL_LINES,
            GL_CULL_FACE, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
            GL_NEAREST, GL_TEXTURE_MAG_FILTER, GLfloat
        )
    except ImportError:
        raise ImportError("OpenGL constants not available. Please install PyOpenGL: pip install PyOpenGL")

try:
    from pyglet.graphics import get_default_shader
except ImportError:
    get_default_shader = None

from protocol import *

TICKS_PER_SEC = 60

# Movement variables
WALKING_SPEED = 5
FLYING_SPEED = 15
CROUCH_SPEED = 2
SPRINT_SPEED = 7
SPRINT_FOV = SPRINT_SPEED / 2

GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50

# Player variables
PLAYER_HEIGHT = 2
PLAYER_FOV = 80.0

if sys.version_info[0] >= 3:
    xrange = range

def cube_vertices(x, y, z, n):
    """Return the vertices of the cube at position x, y, z with size 2*n."""
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

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
    result.extend(top)
    result.extend(bottom)
    result.extend(side * 4)
    return result

TEXTURE_PATH = 'texture.png'

# Block texture definitions
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))

# Block type to texture mapping
BLOCK_TEXTURES = {
    BlockType.GRASS: GRASS,
    BlockType.SAND: SAND,
    BlockType.BRICK: BRICK,
    BlockType.STONE: STONE,
    BlockType.WOOD: WOOD,
    BlockType.LEAF: LEAF,
    BlockType.WATER: WATER
}

FACES = [
    ( 0, 1, 0),
    ( 0,-1, 0),
    (-1, 0, 0),
    ( 1, 0, 0),
    ( 0, 0, 1),
    ( 0, 0,-1),
]

def normalize(position):
    """Accepts position of arbitrary precision and returns the block containing that position."""
    x, y, z = position
    x, y, z = (int(round(x)), int(round(y)), int(round(z)))
    return (x, y, z)

def sectorize(position):
    """Returns a tuple representing the sector for the given position."""
    SECTOR_SIZE = 16
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class ClientModel:
    """Client-side world model that receives updates from server."""
    
    def __init__(self):
        # A Batch is a collection of vertex lists for batched rendering.
        self.batch = pyglet.graphics.Batch()
        
        # A TextureGroup manages an OpenGL texture.
        self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        
        # A mapping from position to the block type at that position.
        self.world = {}
        
        # Same mapping as `world` but only contains blocks that are shown.
        self.shown = {}
        
        # Mapping from position to a pyglet `VertextList` for all shown blocks.
        self._shown = {}
        
        # Mapping from sector to a list of positions inside that sector.
        self.sectors = {}
        
        # Simple function queue for rendering operations
        self.queue = deque()
        
        # Other players in the world
        self.other_players = {}
        
        # Cache for exposure calculations to improve performance
        self.exposure_cache = {}
    
    def invalidate_exposure_cache(self, position):
        """Invalidate exposure cache for a position and its neighbors."""
        positions_to_clear = [position] + list(self.neighbors(position))
        for pos in positions_to_clear:
            self.exposure_cache.pop(pos, None)
    
    def load_world_data(self, world_data):
        """Load initial world data from server."""
        # Just store basic world info, chunks will come separately
        self.world_size = world_data.get("world_size", 128)
        self.spawn_position = world_data.get("spawn_position", [30, 50, 80])
    
    def load_world_chunk(self, chunk_data):
        """Load a chunk of world data."""
        blocks = chunk_data.get("blocks", {})
        
        for pos_str, block_type in blocks.items():
            # Convert string position back to tuple
            x, y, z = map(int, pos_str.split(','))
            position = (x, y, z)
            self.add_block(position, block_type, immediate=False)
    
    def exposed(self, position):
        """Returns False if given position is surrounded on all 6 sides by blocks, True otherwise."""
        # Check cache first
        if position in self.exposure_cache:
            return self.exposure_cache[position]
        
        # Calculate exposure status
        x, y, z = position
        exposed = False
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                exposed = True
                break
        
        # Cache the result
        self.exposure_cache[position] = exposed
        return exposed
    
    def face_exposed(self, position, face_direction):
        """Check if a specific face of a block is exposed.
        
        Args:
            position: (x, y, z) position of the block
            face_direction: tuple (dx, dy, dz) representing the face direction
            
        Returns:
            True if the face is exposed (no neighboring block), False otherwise
        """
        x, y, z = position
        dx, dy, dz = face_direction
        neighbor_pos = (x + dx, y + dy, z + dz)
        return neighbor_pos not in self.world
    
    def get_exposed_faces(self, position):
        """Get all exposed faces of a block.
        
        Args:
            position: (x, y, z) position of the block
            
        Returns:
            List of face directions (dx, dy, dz) that are exposed
        """
        exposed_faces = []
        for face in FACES:
            if self.face_exposed(position, face):
                exposed_faces.append(face)
        return exposed_faces
    
    def add_block(self, position, block_type, immediate=True):
        """Add a block with the given block_type and position to the world."""
        if position in self.world:
            self.remove_block(position, immediate)
        
        self.world[position] = block_type
        self.sectors.setdefault(sectorize(position), []).append(position)
        
        # Invalidate exposure cache for this position and neighbors
        self.invalidate_exposure_cache(position)
        
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
    
    def remove_block(self, position, immediate=True):
        """Remove the block at the given position."""
        if position not in self.world:
            return
        
        del self.world[position]
        sector = sectorize(position)
        if sector in self.sectors and position in self.sectors[sector]:
            self.sectors[sector].remove(position)
        
        # Invalidate exposure cache for this position and neighbors
        self.invalidate_exposure_cache(position)
        
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
    
    def neighbors(self, position):
        """Generate all neighboring positions for a given position."""
        x, y, z = position
        for dx, dy, dz in FACES:
            yield (x + dx, y + dy, z + dz)
    
    def check_neighbors(self, position):
        """Check all blocks surrounding position and ensure their visual state is current."""
        for neighbor in self.neighbors(position):
            if neighbor not in self.world:
                continue
            if self.exposed(neighbor):
                if neighbor not in self.shown:
                    self.show_block(neighbor)
            else:
                if neighbor in self.shown:
                    self.hide_block(neighbor)
    
    def check_neighbors_batch(self, positions):
        """Check neighbors for multiple positions efficiently."""
        # Collect all unique neighbors to avoid duplicate processing
        neighbors_to_check = set()
        for position in positions:
            neighbors_to_check.update(self.neighbors(position))
        
        # Process each unique neighbor once
        for neighbor in neighbors_to_check:
            if neighbor not in self.world:
                continue
            if self.exposed(neighbor):
                if neighbor not in self.shown:
                    self.show_block(neighbor)
            else:
                if neighbor in self.shown:
                    self.hide_block(neighbor)
    
    def show_block(self, position, immediate=True):
        """Show the block at the given position."""
        if position not in self.world:
            return
        
        block_type = self.world[position]
        texture = BLOCK_TEXTURES.get(block_type, GRASS)
        self.shown[position] = texture
        
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)
    
    def _show_block(self, position, texture):
        """Private implementation of the show_block() method."""
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        
        # create vertex list
        self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
            ('v3f/static', vertex_data),
            ('t2f/static', texture_data))
    
    def hide_block(self, position, immediate=True):
        """Hide the block at the given position."""
        if position in self.shown:
            self.shown.pop(position)
        
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)
    
    def _hide_block(self, position):
        """Private implementation of the hide_block() method."""
        if position in self._shown:
            self._shown.pop(position).delete()
    
    def _enqueue(self, func, *args):
        """Add func to the internal queue."""
        self.queue.append((func, args))
    
    def _dequeue(self):
        """Pop the top function from the internal queue and call it."""
        if self.queue:
            func, args = self.queue.popleft()
            func(*args)
    
    def process_queue(self):
        """Process the entire queue while taking periodic breaks."""
        start = time.process_time()
        while self.queue and time.process_time() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()
    
    def process_entire_queue(self):
        """Process the entire queue with no breaks."""
        while self.queue:
            self._dequeue()
    
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

class NetworkClient:
    """Handles network communication with the server."""
    
    def __init__(self, window, server_url="ws://localhost:8765"):
        self.window = window
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.player_id = None
        self.loop = None
        self.network_thread = None
    
    def start_connection(self):
        """Start the network connection in a separate thread."""
        self.network_thread = threading.Thread(target=self._run_network_loop, daemon=True)
        self.network_thread.start()
    
    def _run_network_loop(self):
        """Run the asyncio event loop in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._connect_to_server())
        except Exception as e:
            print(f"Network error: {e}")
        finally:
            self.loop.close()
    
    async def _connect_to_server(self):
        """Connect to the server and handle messages."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            print(f"Connected to server at {self.server_url}")
            
            # Send join message
            join_msg = create_player_join_message("Player")
            await self.websocket.send(join_msg.to_json())
            
            # Listen for messages
            async for message_str in self.websocket:
                try:
                    message = Message.from_json(message_str)
                    # Schedule message handling on the main thread
                    pyglet.clock.schedule_once(lambda dt, msg=message: self._handle_server_message(msg), 0)
                except Exception as e:
                    print(f"Error parsing message: {e}")
        
        except Exception as e:
            print(f"Failed to connect to server: {e}")
        finally:
            self.connected = False
            self.websocket = None
    
    def _handle_server_message(self, message: Message):
        """Handle a message from the server (called on main thread)."""
        if message.type == MessageType.WORLD_INIT:
            # Load initial world info
            self.window.model.load_world_data(message.data)
        
        elif message.type == MessageType.WORLD_CHUNK:
            # Load world chunk
            self.window.model.load_world_chunk(message.data)
        
        elif message.type == MessageType.WORLD_UPDATE:
            # Apply block updates
            blocks = message.data.get("blocks", [])
            for block_data in blocks:
                block_update = BlockUpdate.from_dict(block_data)
                position = block_update.position
                
                if block_update.block_type == BlockType.AIR:
                    # Remove block
                    self.window.model.remove_block(position)
                else:
                    # Add/update block
                    self.window.model.add_block(position, block_update.block_type)
        
        elif message.type == MessageType.PLAYER_UPDATE:
            # Update other player positions
            player_data = message.data
            player_id = player_data["id"]
            
            if player_id != self.player_id:  # Don't update our own position
                self.window.model.other_players[player_id] = PlayerState.from_dict(player_data)
        
        elif message.type == MessageType.PLAYER_LIST:
            # Update player list
            players = message.data.get("players", [])
            self.window.model.other_players = {}
            
            for player_data in players:
                player = PlayerState.from_dict(player_data)
                if player.id != self.player_id:
                    self.window.model.other_players[player.id] = player
        
        elif message.type == MessageType.CHAT_BROADCAST:
            # Show chat message
            chat_text = message.data.get("text", "")
            print(f"[CHAT] {chat_text}")  # For now, just print to console
        
        elif message.type == MessageType.ERROR:
            error_msg = message.data.get("message", "Unknown error")
            print(f"Server error: {error_msg}")
    
    def send_message(self, message: Message):
        """Send a message to the server."""
        if not self.connected or not self.websocket:
            return
        
        # Schedule sending on the network thread
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_message_async(message), self.loop)
    
    async def _send_message_async(self, message: Message):
        """Send message asynchronously."""
        if self.websocket:
            try:
                await self.websocket.send(message.to_json())
            except Exception as e:
                print(f"Error sending message: {e}")
    
    def disconnect(self):
        """Disconnect from server."""
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)

class Window(pyglet.window.Window):
    """Main game window - handles rendering and input."""
    
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        
        # Whether or not the window exclusively captures the mouse.
        self.exclusive = False
        
        # When flying gravity has no effect and speed is increased.
        self.flying = False
        
        # Used for constant jumping.
        self.jumping = False
        self.jumped = False
        
        # If this is true, a crouch offset is added to the final glTranslate
        self.crouch = False
        
        # Player sprint
        self.sprinting = False
        
        # This is an offset value so stuff like speed potions can also be easily added
        self.fov_offset = 0
        
        self.collision_types = {"top": False, "bottom": False, "right": False, "left": False}
        
        # Strafing is moving lateral to the direction you are facing
        self.strafe = [0, 0]
        
        # Current (x, y, z) position in the world, specified with floats.
        self.position = (30, 50, 80)
        
        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        self.rotation = (0, 0)
        
        # Which sector the player is currently in.
        self.sector = None
        
        # The crosshairs at the center of the screen.
        self.reticle = None
        
        # Velocity in the y (upward) direction.
        self.dy = 0
        
        # A list of blocks the player can place. Hit num keys to cycle.
        self.inventory = [BlockType.BRICK, BlockType.GRASS, BlockType.SAND, BlockType.WOOD, BlockType.LEAF]
        
        # The current block the user can place. Hit num keys to cycle.
        self.block = self.inventory[0]
        
        # Convenience list of num keys.
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        
        # Instance of the model that handles the world.
        self.model = ClientModel()
        
        # Network client for server communication
        self.network = NetworkClient(self)
        
        # The label that is displayed in the top left of the canvas.
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 255))
        
        # This call schedules the `update()` method to be called
        # TICKS_PER_SEC. This is the main game event loop.
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
        
        # Start network connection
        self.network.start_connection()
    
    def set_exclusive_mouse(self, exclusive):
        """If exclusive is True, the game will capture the mouse."""
        super(Window, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    
    def get_sight_vector(self):
        """Returns the current line of sight vector indicating the direction the player is looking."""
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    
    def get_motion_vector(self):
        """Returns the current motion vector indicating the velocity of the player."""
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dy = 0.0
            dx = 0.0
            dz = 0.0
        return (dx, dy, dz)
    
    def update(self, dt):
        """This method is scheduled to be called repeatedly by the pyglet clock."""
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)
        
        # Send position update to server (throttled)
        if hasattr(self, '_last_position_update'):
            if time.time() - self._last_position_update > 0.1:  # 10 updates per second
                self._send_position_update()
        else:
            self._send_position_update()
    
    def _send_position_update(self):
        """Send player position update to server."""
        if self.network.connected:
            move_msg = create_player_move_message(self.position, self.rotation)
            self.network.send_message(move_msg)
            self._last_position_update = time.time()
    
    def _update(self, dt):
        """Private implementation of the update() method."""
        # walking
        if self.flying:
            speed = FLYING_SPEED
        elif self.sprinting:
            speed = SPRINT_SPEED
        elif self.crouch:
            speed = CROUCH_SPEED
        else:
            speed = WALKING_SPEED
        
        if self.jumping:
            if self.collision_types["top"]:
                self.dy = JUMP_SPEED
                self.jumped = True
        else:
            if self.collision_types["top"]:
                self.jumped = False
        
        if self.jumped:
            speed += 0.7
        
        d = dt * speed  # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        
        # gravity
        if not self.flying:
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        
        # collisions
        old_pos = self.position
        x, y, z = old_pos
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)
        
        # Sprinting stuff
        if old_pos[0]-self.position[0] == 0 and old_pos[2]-self.position[2] == 0:
            disablefov = False
            if self.sprinting:
                disablefov = True
            self.sprinting = False
            if disablefov:
                self.fov_offset -= SPRINT_FOV
    
    def collide(self, position, height):
        """Checks to see if the player at the given position and height is colliding with any blocks."""
        pad = 0.25
        p = list(position)
        np = normalize(position)
        self.collision_types = {"top":False,"bottom":False,"right":False,"left":False}
        
        for face in FACES:  # check all surrounding blocks
            for i in xrange(3):  # check each dimension independently
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in xrange(height):  # check each height
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face == (0, -1, 0):
                        self.collision_types["top"] = True
                        self.dy = 0
                    if face == (0, 1, 0):
                        self.collision_types["bottom"] = True
                        self.dy = 0
                    break
        return tuple(p)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Called when a mouse button is pressed."""
        if self.exclusive:
            vector = self.get_sight_vector()
            block, previous = self.model.hit_test(self.position, vector)
            
            if (button == mouse.RIGHT) or ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # Place block
                if previous:
                    place_msg = create_block_place_message(previous, self.block)
                    self.network.send_message(place_msg)
            
            elif button == pyglet.window.mouse.LEFT and block:
                # Destroy block
                destroy_msg = create_block_destroy_message(block)
                self.network.send_message(destroy_msg)
        else:
            self.set_exclusive_mouse(True)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Called when the player moves the mouse."""
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    
    def on_key_press(self, symbol, modifiers):
        """Called when the player presses a key."""
        if symbol == key.Z:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.Q:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.C:
            self.fov_offset -= 60.0
        elif symbol == key.SPACE:
            self.jumping = True
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol == key.LSHIFT:
            self.crouch = True
            if self.sprinting:
                self.fov_offset -= SPRINT_FOV
                self.sprinting = False
        elif symbol == key.R:
            if not self.crouch:
                if not self.sprinting:
                    self.fov_offset += SPRINT_FOV
                self.sprinting = True
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]
    
    def on_key_release(self, symbol, modifiers):
        """Called when the player releases a key."""
        if symbol == key.Z:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.Q:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
        elif symbol == key.SPACE:
            self.jumping = False
        elif symbol == key.LSHIFT:
            self.crouch = False
        elif symbol == key.C:
            self.fov_offset += 60.0
    
    def on_resize(self, width, height):
        """Called when the window is resized to a new width and height."""
        # label
        self.label.y = height - 10
        # reticle
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        
        # Create crosshair vertex list - compatible with Pyglet 2.1.8
        try:
            self.reticle = pyglet.graphics.vertex_list(4, 
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
            )
        except (AttributeError, TypeError):
            if get_default_shader is not None:
                try:
                    self.reticle = get_default_shader().vertex_list(4, GL_LINES,
                        position=('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
                    )
                except:
                    self.reticle = pyglet.graphics.vertex_list(4,
                        ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
                    )
            else:
                self.reticle = pyglet.graphics.vertex_list(4,
                    ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
                )
    
    def set_2d(self):
        """Configure OpenGL to draw in 2d."""
        width, height = self.get_size()
        glDisable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, max(1, width), 0, max(1, height), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
    def set_3d(self):
        """Configure OpenGL to draw in 3d."""
        width, height = self.get_size()
        glEnable(GL_DEPTH_TEST)
        viewport = self.get_viewport_size()
        glViewport(0, 0, max(1, viewport[0]), max(1, viewport[1]))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(PLAYER_FOV + self.fov_offset, width / float(height), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        x, y = self.rotation
        glRotatef(x, 0, 1, 0)
        glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
        x, y, z = self.position
        if self.crouch:
            glTranslatef(-x, -y+0.2, -z)
        else:
            glTranslatef(-x, -y, -z)
    
    def on_draw(self):
        """Called by pyglet to draw the canvas."""
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()
    
    def draw_focused_block(self):
        """Draw black edges around the block that is currently under the crosshairs."""
        vector = self.get_sight_vector()
        block = self.model.hit_test(self.position, vector)[0]
        if block:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    def draw_label(self):
        """Draw the label in the top left of the screen."""
        x, y, z = self.position
        connection_status = "Connected" if self.network.connected else "Disconnected"
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d [%s]' % (
            pyglet.clock.get_fps(), x, y, z,
            len(self.model._shown), len(self.model.world), connection_status)
        self.label.draw()
    
    def draw_reticle(self):
        """Draw the crosshairs in the center of the screen."""
        glColor3d(0, 0, 0)
        if hasattr(self.reticle, 'draw'):
            try:
                self.reticle.draw(mode=GL_LINES)
            except TypeError:
                self.reticle.draw(GL_LINES)
    
    def on_close(self):
        """Called when the window is closed."""
        self.network.disconnect()
        super().on_close()

def setup_fog():
    """Configure the OpenGL fog properties."""
    try:
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
        glHint(GL_FOG_HINT, GL_DONT_CARE)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 40.0)
        glFogf(GL_FOG_END, 60.0)
    except pyglet.gl.lib.GLException:
        pass

def setup():
    """Basic OpenGL configuration."""
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()

def main():
    """Main entry point for the client."""
    window = Window(width=1280, height=720, caption='Minecraft Client', resizable=True)
    window.set_exclusive_mouse(True)
    setup()
    pyglet.app.run()

if __name__ == "__main__":
    main()
