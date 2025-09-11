#!/usr/bin/env python3
"""
Minecraft-like Client
Handles local game loop with Pyglet, connects via WebSocket, visualizes the world, 
sends player actions to server, receives updates to sync world state.
"""

import asyncio
import websockets
import json
import math
import sys
import time
import threading
from collections import deque
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for noise_gen import
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Pyglet components, but allow import to succeed even if they fail
try:
    import pyglet
    from pyglet.gl import *
    from pyglet import image
    from pyglet.graphics import TextureGroup
    from pyglet.window import key, mouse
    
    # Try to import gluPerspective
    try:
        from pyglet.gl import gluPerspective
    except ImportError:
        try:
            from OpenGL.GL import gluPerspective
        except ImportError:
            print("Warning: gluPerspective not available")
    
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
            print("Warning: OpenGL constants not available")

    PYGLET_AVAILABLE = True
except ImportError as e:
    print(f"❌ Pyglet not available: {e}")
    print("🔧 To fix this:")
    print("   - Install required libraries: sudo apt-get install libglu1-mesa-dev")
    print("   - For headless environments: use 'xvfb-run -a python3 client/client.py'")
    PYGLET_AVAILABLE = False
except Exception as e:
    print(f"❌ Display initialization failed: {e}")
    print("🔧 Solutions:")
    print("   - For headless environments: use 'xvfb-run -a python3 client/client.py'")
    print("   - Check X11 forwarding if using SSH: ssh -X")
    print("   - Ensure DISPLAY environment variable is set")
    PYGLET_AVAILABLE = False
    
    # Mock classes for testing
    class Window:
        def __init__(self, *args, **kwargs):
            pass
    
    pyglet = type('MockPyglet', (), {
        'window': type('MockWindow', (), {'Window': Window}),
        'graphics': type('MockGraphics', (), {'Batch': lambda: None}),
        'clock': type('MockClock', (), {'schedule_interval': lambda *args: None}),
        'app': type('MockApp', (), {'run': lambda: None})
    })
    
    key = type('MockKey', (), {
        'W': 'w', 'A': 'a', 'S': 's', 'D': 'd', 'SPACE': 'space',
        'LSHIFT': 'lshift', 'LCTRL': 'lctrl', 'TAB': 'tab', 'ESCAPE': 'escape',
        '_1': '1', '_2': '2', '_3': '3', '_4': '4', '_5': '5',
        '_6': '6', '_7': '7', '_8': '8', '_9': '9', '_0': '0'
    })
    
    mouse = type('MockMouse', (), {'LEFT': 'left', 'RIGHT': 'right'})
    
    # Mock GL functions
    def glClearColor(*args): pass
    def glEnable(*args): pass  
    def glTexParameteri(*args): pass
    def glViewport(*args): pass
    def glMatrixMode(*args): pass
    def glLoadIdentity(*args): pass
    def glRotatef(*args): pass
    def glTranslatef(*args): pass
    def glColor3f(*args): pass
    def glColor3d(*args): pass
    def glBegin(*args): pass
    def glVertex2f(*args): pass
    def glEnd(*args): pass
    def glDisable(*args): pass
    def glOrtho(*args): pass
    def glFogfv(*args): pass
    def glHint(*args): pass
    def glFogi(*args): pass
    def glFogf(*args): pass
    def gluPerspective(*args): pass
    
    # Mock GL constants
    GL_FOG = GL_FOG_COLOR = GL_FOG_HINT = GL_DONT_CARE = 0
    GL_FOG_MODE = GL_LINEAR = GL_FOG_START = GL_FOG_END = 0
    GL_QUADS = GL_DEPTH_TEST = GL_PROJECTION = GL_MODELVIEW = 0
    GL_FRONT_AND_BACK = GL_LINE = GL_FILL = GL_LINES = 0
    GL_CULL_FACE = GL_TEXTURE_2D = GL_TEXTURE_MIN_FILTER = 0
    GL_NEAREST = GL_TEXTURE_MAG_FILTER = 0
    GLfloat = float

# Game constants
TICKS_PER_SEC = 60
SECTOR_SIZE = 16

# Movement constants
WALKING_SPEED = 5
FLYING_SPEED = 15
CROUCH_SPEED = 2
SPRINT_SPEED = 7
SPRINT_FOV = SPRINT_SPEED / 2

GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50

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


TEXTURE_PATH = '../texture.png'

GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))

# Map server block types to texture coordinates
BLOCK_TEXTURES = {
    "GRASS": GRASS,
    "SAND": SAND,
    "BRICK": BRICK, 
    "STONE": STONE,
    "WOOD": WOOD,
    "LEAF": LEAF,
    "WATER": WATER
}

FACES = [
    (0, 1, 0),
    (0, -1, 0),
    (-1, 0, 0),
    (1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
]


def normalize(position):
    """Convert floating point position to block coordinates."""
    x, y, z = position
    return int(math.floor(x)), int(math.floor(y)), int(math.floor(z))


def sectorize(position):
    """Convert block coordinates to sector coordinates."""
    x, y, z = position
    return x // SECTOR_SIZE, z // SECTOR_SIZE


class ClientModel:
    """Client-side world model for rendering"""
    
    def __init__(self):
        # Rendering components
        if PYGLET_AVAILABLE:
            self.batch = pyglet.graphics.Batch()
            
            # Try to load texture, fallback if not found
            texture_path = TEXTURE_PATH
            if not os.path.exists(texture_path):
                texture_path = 'texture.png'  # Try in current directory
                
            if os.path.exists(texture_path):
                self.group = TextureGroup(image.load(texture_path).get_texture())
                print(f"✅ Texture loaded successfully: {texture_path}")
            else:
                print("⚠️  Warning: texture.png not found, using default")
                self.group = None
        else:
            print("❌ Pyglet not available - blocks will not be visible!")
            print("🔧 Run with: xvfb-run -a python3 client/client.py")
            self.batch = None
            self.group = None
        
        # World state (received from server)
        self.world = {}  # position -> texture
        self.shown = {}  # blocks currently being rendered
        self._shown = {}  # position -> vertex list
        self.sectors = {}  # sector -> list of positions
        
        # Rendering queue for show/hide operations
        self.queue = deque()
        
    def clear_world(self):
        """Clear all world data"""
        self.world.clear()
        self.shown.clear()
        for vertex_list in self._shown.values():
            vertex_list.delete()
        self._shown.clear()
        self.sectors.clear()
        
    def update_world_from_server(self, blocks_data):
        """Update world state from server data"""
        # Clear existing world
        self.clear_world()
        
        # Add blocks from server
        for block_data in blocks_data:
            pos = tuple(block_data["pos"])
            block_type = block_data["type"]
            
            if block_type in BLOCK_TEXTURES:
                texture = BLOCK_TEXTURES[block_type]
                self.world[pos] = texture
                self.sectors.setdefault(sectorize(pos), []).append(pos)
        
        print(f"📦 Received {len(blocks_data)} blocks from server")
        print(f"🌍 World now contains {len(self.world)} blocks")
        
        # Show blocks in the current area immediately
        self._show_nearby_blocks()
        
        if not PYGLET_AVAILABLE:
            print("❌ Blocks loaded but not visible - no display available")
            print("🔧 Use: xvfb-run -a python3 client/client.py")
        else:
            print(f"✅ {len(self._shown)} blocks rendered successfully")
    
    def _show_nearby_blocks(self):
        """Show blocks in all sectors that should be visible"""
        # Get all sectors that contain blocks
        for sector in self.sectors.keys():
            self.show_sector(sector)
        # Process the queue to ensure blocks are shown immediately
        self.process_entire_queue()
    
    def exposed(self, position):
        """Returns False if given position is surrounded on all 6 sides by blocks."""
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    
    def show_block(self, position, immediate=True):
        """Show the block at the given position."""
        texture = self.world[position]
        self.shown[position] = texture
        if immediate:
            self._show_block(position, texture)
        else:
            self._enqueue(self._show_block, position, texture)
    
    def _show_block(self, position, texture):
        """Private implementation of the show_block() method."""
        if not PYGLET_AVAILABLE or not self.batch:
            # Block data is stored but not rendered due to display limitations
            return
            
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        texture_data = list(texture)
        
        try:
            if self.group:
                vertex_list = self.batch.add(24, GL_QUADS, self.group,
                    ('v3f/static', vertex_data),
                    ('t2f/static', texture_data))
            else:
                vertex_list = self.batch.add(24, GL_QUADS, None,
                    ('v3f/static', vertex_data))
            
            self._shown[position] = vertex_list
        except Exception as e:
            print(f"⚠️  Warning: Failed to render block at {position}: {e}")
            # Continue without crashing - block data is still stored
    
    def hide_block(self, position, immediate=True):
        """Hide the block at the given position."""
        self.shown.pop(position, None)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)
    
    def _hide_block(self, position):
        """Private implementation of the hide_block() method."""
        if position in self._shown:
            self._shown.pop(position).delete()
    
    def show_sector(self, sector):
        """Ensure all blocks in the given sector are shown."""
        positions = self.sectors.get(sector, [])
        for position in positions:
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)
    
    def hide_sector(self, sector):
        """Ensure all blocks in the given sector are hidden."""
        positions = self.sectors.get(sector, [])
        for position in positions:
            if position in self.shown:
                self.hide_block(position, False)
    
    def change_sectors(self, before, after):
        """Move from sector before to sector after."""
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dz in xrange(-pad, pad + 1):
                if dx ** 2 + dz ** 2 > (pad + 1) ** 2:
                    continue
                if before:
                    x, z = before
                    before_set.add((x + dx, z + dz))
                if after:
                    x, z = after
                    after_set.add((x + dx, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)
    
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
        start = time.time()
        while self.queue and time.time() - start < 1.0 / TICKS_PER_SEC:
            self._dequeue()
    
    def process_entire_queue(self):
        """Process the entire queue with no breaks."""
        while self.queue:
            self._dequeue()


class MinecraftClient(pyglet.window.Window if PYGLET_AVAILABLE else object):
    """Main client window and game logic"""
    
    def __init__(self, *args, **kwargs):
        if PYGLET_AVAILABLE:
            super(MinecraftClient, self).__init__(*args, **kwargs)
        
        # Window state
        self.exclusive = False
        
        # Player state
        self.flying = False
        self.jumping = False
        self.jumped = False
        self.crouch = False
        self.sprinting = False
        self.fov_offset = 0
        self.collision_types = {"top": False, "bottom": False, "right": False, "left": False}
        
        # Movement
        self.strafe = [0, 0]
        self.position = [30.0, 50.0, 80.0]
        self.rotation = [0.0, 0.0]
        self.sector = None
        self.dy = 0  # vertical velocity
        
        # Inventory and blocks
        self.inventory = ["BRICK", "GRASS", "SAND", "WOOD", "LEAF"]
        self.block = self.inventory[0]
        if PYGLET_AVAILABLE:
            self.num_keys = [
                key._1, key._2, key._3, key._4, key._5,
                key._6, key._7, key._8, key._9, key._0]
        else:
            self.num_keys = []
        
        # World model
        self.model = ClientModel()
        
        # Network state
        self.websocket = None
        self.connected = False
        self.server_url = "ws://localhost:8765"
        self.player_name = f"Player{int(time.time()) % 10000}"
        
        # Other players
        self.other_players = {}
        
        # UI
        if PYGLET_AVAILABLE and hasattr(self, 'height'):
            self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
                                          x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
                                          color=(0, 0, 0, 255))
        else:
            self.label = None
        
        # Start network connection only in full mode
        if PYGLET_AVAILABLE:
            self._start_network_thread()
            
            # Schedule game loop
            pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
    
    def _start_network_thread(self):
        """Start the network thread for WebSocket communication"""
        self.network_thread = threading.Thread(target=self._run_network_loop, daemon=True)
        self.network_thread.start()
    
    def _run_network_loop(self):
        """Run the network event loop in a separate thread"""
        asyncio.run(self._network_loop())
    
    async def _network_loop(self):
        """Main network loop"""
        while True:
            try:
                if not self.connected:
                    await self._connect_to_server()
                else:
                    # If connected, just wait and check connection health
                    await asyncio.sleep(1.0)
                    await self._check_connection_health()
            except Exception as e:
                print(f"Network error: {e}")
                self.connected = False
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _check_connection_health(self):
        """Check if the connection is still healthy"""
        if self.websocket and not self.websocket.closed:
            try:
                # Send a ping to check if connection is alive
                await self.websocket.ping()
            except Exception:
                # Connection is dead, mark as disconnected
                self.connected = False
        else:
            # Connection is closed, mark as disconnected
            self.connected = False
    
    async def _connect_to_server(self):
        """Connect to the game server"""
        try:
            print(f"Connecting to server at {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            
            # Send join message
            join_msg = {
                "type": "join",
                "name": self.player_name
            }
            await self.websocket.send(json.dumps(join_msg))
            
            # Wait for welcome message
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get("type") == "welcome":
                self.connected = True
                print(f"Connected as {welcome_data.get('name')}")
                
                # Update position from server
                server_pos = welcome_data.get("position")
                if server_pos:
                    self.position = server_pos
                
                # Start listening for messages
                await self._listen_for_messages()
            else:
                print("Unexpected welcome message:", welcome_data)
                
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
    
    async def _listen_for_messages(self):
        """Listen for messages from the server"""
        try:
            async for message in self.websocket:
                await self._handle_server_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            print("Connection to server lost")
            self.connected = False
        except Exception as e:
            print(f"Error listening for messages: {e}")
            self.connected = False
    
    async def _handle_server_message(self, message_data):
        """Handle a message from the server"""
        message_type = message_data.get("type")
        
        if message_type == "world_update":
            # Update world from server
            blocks_data = message_data.get("blocks", [])
            self.model.update_world_from_server(blocks_data)
            
            # Update player data
            player_data = message_data.get("player")
            if player_data:
                self.position = player_data.get("pos", self.position)
            
            # Reset sector to ensure proper rendering after world update
            self.sector = None
                
        elif message_type == "update":
            # Update other players
            players_data = message_data.get("players", [])
            self.other_players = {p["name"]: p for p in players_data if p["name"] != self.player_name}
            
        elif message_type == "chat":
            # Handle chat message
            player = message_data.get("player", "Unknown")
            message = message_data.get("message", "")
            print(f"[{player}]: {message}")
    
    async def _send_to_server(self, message):
        """Send a message to the server"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error sending message: {e}")
                self.connected = False
    
    def send_position_update(self):
        """Send position update to server"""
        if self.connected:
            msg = {
                "type": "move",
                "pos": self.position,
                "rotation": self.rotation
            }
            # Send in background thread
            asyncio.run_coroutine_threadsafe(self._send_to_server(msg), 
                                           asyncio.get_event_loop())
    
    def send_block_action(self, action, position, block_type=None):
        """Send block placement/removal to server"""
        if self.connected:
            msg = {
                "type": "block",
                "action": action,
                "pos": list(position)
            }
            if block_type:
                msg["block_type"] = block_type
                
            asyncio.run_coroutine_threadsafe(self._send_to_server(msg),
                                           asyncio.get_event_loop())
    
    def set_exclusive_mouse(self, exclusive):
        """Capture or release the mouse cursor."""
        super(MinecraftClient, self).set_exclusive_mouse(exclusive)
        self.exclusive = exclusive
    
    def get_sight_vector(self):
        """Returns the current line of sight vector."""
        x, y = self.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1
        m = math.cos(math.radians(y))
        # dy ranges from -1 to 1
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)
    
    def get_motion_vector(self):
        """Returns the current motion vector."""
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
        """Main update loop called by pyglet clock."""
        self.model.process_queue()
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        m = 8
        dt = min(dt, 0.2)
        for _ in xrange(m):
            self._update(dt / m)
    
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

        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        
        # gravity
        if not self.flying:
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
            
        # collisions
        old_pos = self.position[:]
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = [x, y, z]

        # Send position update periodically
        if time.time() % 0.1 < dt:  # About 10 times per second
            self.send_position_update()

        # Sprint handling
        if old_pos[0] - self.position[0] == 0 and old_pos[2] - self.position[2] == 0:
            disable_fov = False
            if self.sprinting:
                disable_fov = True
            self.sprinting = False
            if disable_fov:
                self.fov_offset -= SPRINT_FOV
    
    def collide(self, position, height):
        """Check for collisions and adjust position."""
        # This is simplified - in full implementation would check against world blocks
        x, y, z = position
        
        # Simple ground collision at y=0
        if y < 1:
            y = 1
            self.dy = 0
            self.collision_types["top"] = True
        else:
            self.collision_types["top"] = False
            
        return x, y, z
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks for block placement/removal."""
        if self.exclusive:
            vector = self.get_sight_vector()
            # Simple hit test - in full implementation would use model.hit_test
            block_pos = normalize([self.position[i] + vector[i] * 5 for i in range(3)])
            
            if button == mouse.LEFT:
                # Remove block
                self.send_block_action("remove", block_pos)
            elif button == mouse.RIGHT:
                # Place block  
                self.send_block_action("place", block_pos, self.block)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion for camera rotation."""
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    
    def on_key_press(self, symbol, modifiers):
        """Handle key presses."""
        if symbol == key.W:
            self.strafe[0] -= 1
        elif symbol == key.S:
            self.strafe[0] += 1
        elif symbol == key.A:
            self.strafe[1] -= 1
        elif symbol == key.D:
            self.strafe[1] += 1
        elif symbol == key.SPACE:
            self.jumping = True
        elif symbol == key.LSHIFT:
            self.crouch = True
        elif symbol == key.LCTRL:
            self.sprinting = True
            if not self.flying and not self.crouch:
                self.fov_offset += SPRINT_FOV
        elif symbol == key.TAB:
            self.flying = not self.flying
        elif symbol == key.ESCAPE:
            self.set_exclusive_mouse(False)
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]
    
    def on_key_release(self, symbol, modifiers):
        """Handle key releases."""
        if symbol == key.W:
            self.strafe[0] += 1
        elif symbol == key.S:
            self.strafe[0] -= 1
        elif symbol == key.A:
            self.strafe[1] += 1
        elif symbol == key.D:
            self.strafe[1] -= 1
        elif symbol == key.SPACE:
            self.jumping = False
        elif symbol == key.LSHIFT:
            self.crouch = False
        elif symbol == key.LCTRL:
            self.sprinting = False
            if self.fov_offset > 0:
                self.fov_offset -= SPRINT_FOV
    
    def on_resize(self, width, height):
        """Handle window resize."""
        self.label.y = height - 10
        if width and height:
            # viewport
            glViewport(0, 0, width, height)
            # projection
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(PLAYER_FOV + self.fov_offset, width / float(height), 0.1, 60.0)
            # model
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            x, y = self.rotation
            glRotatef(x, 0, 1, 0)
            glRotatef(-y, math.cos(math.radians(x)), 0, math.sin(math.radians(x)))
            x, y, z = self.position
            glTranslatef(-x, -y, -z)
    
    def on_draw(self):
        """Render the scene."""
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.set_2d()
        self.draw_label()
        self.draw_reticle()
    
    def set_2d(self):
        """Configure OpenGL for 2D rendering."""
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
        """Configure OpenGL for 3D rendering."""
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
        glTranslatef(-x, -y, -z)
    
    def draw_label(self):
        """Draw the label in the top left of the screen."""
        x, y, z = self.position
        self.label.text = f'({x:.1f}, {y:.1f}, {z:.1f}) {len(self.model.world)} blocks'
        self.label.draw()
    
    def draw_reticle(self):
        """Draw the crosshairs in the center of the screen."""
        glColor3f(0, 0, 0)
        width, height = self.get_size()
        glBegin(GL_LINES)
        glVertex2f(width // 2 - 10, height // 2)
        glVertex2f(width // 2 + 10, height // 2)
        glVertex2f(width // 2, height // 2 - 10)
        glVertex2f(width // 2, height // 2 + 10)
        glEnd()
    
    def on_close(self):
        """Handle window close."""
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(),
                                           asyncio.get_event_loop())
        super().on_close()


def check_display_requirements():
    """Check if display requirements are met for rendering"""
    if not PYGLET_AVAILABLE:
        return False
    
    import os
    display = os.environ.get('DISPLAY')
    if not display:
        print("❌ No DISPLAY environment variable set")
        print("🔧 For headless environments:")
        print("   xvfb-run -a python3 client/client.py")
        print("🔧 For SSH with X11 forwarding:")
        print("   ssh -X username@hostname")
        return False
    
    return True


def setup_fog():
    """Configure the OpenGL fog properties."""
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)


def setup():
    """Basic OpenGL configuration."""
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()


def main():
    """Main entry point."""
    print("🎮 Starting Minecraft-like Client")
    print("==================================")
    
    # Check display requirements
    if not check_display_requirements():
        print("\n🚨 CRITICAL: Display not available - blocks will not be visible!")
        print("💡 This is likely why you're experiencing invisible blocks.")
        print("\n🛠️  Quick fixes:")
        print("   • For headless systems: xvfb-run -a python3 client/client.py")
        print("   • For SSH: use 'ssh -X' for X11 forwarding")
        print("   • For local systems: ensure X11/Wayland display is running")
        print("\nContinuing with limited functionality...")
        
    if PYGLET_AVAILABLE:
        window = MinecraftClient(width=1280, height=720, caption='Minecraft Client', resizable=True)
        window.set_exclusive_mouse(True)
        setup()
        pyglet.app.run()
    else:
        print("Running in headless mode - no window will be displayed")
        # Keep the process alive for testing purposes
        import time
        time.sleep(5)


if __name__ == '__main__':
    main()