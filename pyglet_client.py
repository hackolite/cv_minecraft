#!/usr/bin/env python3
"""
Minecraft-like Client using Pyglet
Connects to the server via WebSocket for multiplayer functionality
"""

import asyncio
import websockets
import json
import math
import random
import time
import sys
import threading
from queue import Queue
from collections import deque

import pyglet
from pyglet.gl import *
from pyglet import image
from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse

# Import missing GL constants if not available from pyglet
try:
    # These constants should be available after importing pyglet.gl
    GL_FOG
except NameError:
    # Fallback to PyOpenGL if constants are not available from pyglet
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

TICKS_PER_SEC = 60

# Size of sectors used to ease block loading.
SECTOR_SIZE = 16

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

# Block rendering variables
BLOCK_SIZE = 0.5
BLOCK_OUTLINE_SIZE = 0.51

# Mouse and camera variables
MOUSE_SENSITIVITY = 0.15

# For Python 2/3 compatibility
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

# Block type definitions
GRASS = "grass"
SAND = "sand"  
BRICK = "brick"
STONE = "stone"
WOOD = "wood"
LEAF = "leaf"
WATER = "water"
FROG = "frog"

# Texture mappings
BLOCK_TEXTURES = {
    GRASS: tex_coords((1, 0), (0, 1), (0, 0)),
    SAND: tex_coords((1, 1), (1, 1), (1, 1)),
    BRICK: tex_coords((2, 0), (2, 0), (2, 0)),
    STONE: tex_coords((2, 1), (2, 1), (2, 1)),
    WOOD: tex_coords((3, 1), (3, 1), (3, 1)),
    LEAF: tex_coords((3, 0), (3, 0), (3, 0)),
    WATER: tex_coords((0, 2), (0, 2), (0, 2)),
    FROG: tex_coords((1, 2), (1, 2), (1, 2))
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
    x, y, z = normalize(position)
    x, y, z = x // SECTOR_SIZE, y // SECTOR_SIZE, z // SECTOR_SIZE
    return (x, 0, z)

class NetworkModel(object):
    """Model that synchronizes with server via WebSocket."""
    
    def __init__(self):
        # Graphics batch for efficient rendering
        self.batch = pyglet.graphics.Batch()
        
        # Texture group for blocks
        try:
            self.group = TextureGroup(image.load(TEXTURE_PATH).get_texture())
        except:
            # Create a simple colored group if texture loading fails
            self.group = None
        
        # World state - blocks that exist on server
        self.world = {}
        
        # Shown blocks - blocks currently being rendered
        self.shown = {}
        
        # Pyglet vertex lists for shown blocks
        self._shown = {}
        
        # Sectors for efficient rendering
        self.sectors = {}
        
        # Queue for rendering operations
        self.queue = deque()
        
        # Network communication
        self.outgoing_messages = Queue()
        self.incoming_messages = Queue()
        self.connected = False
        
        # Start network thread
        self.start_network_thread()
    
    def start_network_thread(self):
        """Start network thread for WebSocket communication."""
        self.network_thread = threading.Thread(target=self.network_worker)
        self.network_thread.daemon = True
        self.network_thread.start()
    
    def network_worker(self):
        """Network worker for WebSocket communication."""
        async def connect_and_communicate():
            try:
                uri = "ws://localhost:8765"
                print(f"Connecting to {uri}...")
                
                async with websockets.connect(uri) as websocket:
                    print("Connected to server!")
                    self.connected = True
                    
                    # Send join message
                    join_msg = {'type': 'join', 'name': 'PygletPlayer'}
                    await websocket.send(json.dumps(join_msg))
                    
                    async def listen():
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                self.incoming_messages.put(data)
                            except Exception as e:
                                print(f"Error parsing message: {e}")
                    
                    async def send():
                        while True:
                            while not self.outgoing_messages.empty():
                                try:
                                    msg = self.outgoing_messages.get_nowait()
                                    await websocket.send(msg)
                                except Exception as e:
                                    print(f"Error sending: {e}")
                            await asyncio.sleep(0.01)
                    
                    await asyncio.gather(listen(), send())
                    
            except Exception as e:
                print(f"Network error: {e}")
                self.connected = False
        
        try:
            asyncio.run(connect_and_communicate())
        except Exception as e:
            print(f"Error in network worker: {e}")
    
    def send_message(self, message):
        """Send message to server."""
        if self.connected:
            self.outgoing_messages.put(json.dumps(message))
    
    def process_network_messages(self):
        """Process incoming network messages."""
        while not self.incoming_messages.empty():
            try:
                message = self.incoming_messages.get_nowait()
                self.handle_server_message(message)
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def handle_server_message(self, data):
        """Handle incoming server message."""
        message_type = data.get('type')
        
        if message_type == 'welcome':
            print("Welcome message received")
            # Auto-request world data
            self.send_message({'type': 'get_world'})
            
        elif message_type == 'world_data':
            blocks = data.get('blocks', [])
            print(f"Received {len(blocks)} blocks from server")
            
            for block_data in blocks:
                if isinstance(block_data, dict):
                    position = block_data.get('position')
                    block_type = block_data.get('block_type')
                    
                    if position and block_type:
                        if isinstance(position, list):
                            position = tuple(position)
                        self.add_block(position, BLOCK_TEXTURES.get(block_type, BLOCK_TEXTURES[STONE]), immediate=False)
        
        elif message_type == 'world_chunk':
            blocks = data.get('blocks', [])
            chunk_index = data.get('chunk_index', 0)
            total_chunks = data.get('total_chunks', 1)
            
            print(f"Received chunk {chunk_index+1}/{total_chunks} with {len(blocks)} blocks")
            
            for block_data in blocks:
                if isinstance(block_data, dict):
                    position = block_data.get('position')
                    block_type = block_data.get('block_type')
                    
                    if position and block_type:
                        if isinstance(position, list):
                            position = tuple(position)
                        self.add_block(position, BLOCK_TEXTURES.get(block_type, BLOCK_TEXTURES[STONE]), immediate=False)
        
        elif message_type == 'world_complete':
            print("World loading complete")
            # Process all queued block additions
            self.process_entire_queue()
        
        elif message_type == 'block_added':
            position = data.get('position')
            block_type = data.get('block_type')
            if position and block_type:
                if isinstance(position, list):
                    position = tuple(position)
                self.add_block(position, BLOCK_TEXTURES.get(block_type, BLOCK_TEXTURES[STONE]))
        
        elif message_type == 'block_removed':
            position = data.get('position')
            if position:
                if isinstance(position, list):
                    position = tuple(position)
                self.remove_block(position)
    
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
    
    def exposed(self, position):
        """Returns False if given position is surrounded on all 6 sides by blocks, True otherwise."""
        x, y, z = position
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.world:
                return True
        return False
    
    def add_block(self, position, texture, immediate=True):
        """Add a block with the given texture and position to the world."""
        if position in self.world:
            self.remove_block(position, immediate)
        self.world[position] = texture
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position)
            self.check_neighbors(position)
    
    def remove_block(self, position, immediate=True):
        """Remove the block at the given position."""
        if position not in self.world:
            return
        del self.world[position]
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbors(position)
    
    def check_neighbors(self, position):
        """Check all blocks surrounding position and ensure their visual state is current."""
        x, y, z = position
        for dx, dy, dz in FACES:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key)
            else:
                if key in self.shown:
                    self.hide_block(key)
    
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
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, BLOCK_SIZE)
        texture_data = list(texture)
        
        # Create vertex list
        if self.group:
            self._shown[position] = self.batch.add(24, GL_QUADS, self.group,
                ('v3f/static', vertex_data),
                ('t2f/static', texture_data))
        else:
            # Fallback to simple colored cubes if no texture
            self._shown[position] = self.batch.add(24, GL_QUADS, None,
                ('v3f/static', vertex_data))
    
    def hide_block(self, position, immediate=True):
        """Hide the block at the given position."""
        self.shown.pop(position, None)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)
    
    def _hide_block(self, position):
        """Private implementation of the hide_block() method."""
        vertex_list = self._shown.pop(position, None)
        if vertex_list:
            vertex_list.delete()
    
    def show_sector(self, sector):
        """Ensure all blocks in the given sector that should be shown are drawn to the canvas."""
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, False)
    
    def hide_sector(self, sector):
        """Ensure all blocks in the given sector that should be hidden are removed from the canvas."""
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)
    
    def change_sectors(self, before, after):
        """Move from sector before to sector after."""
        before_set = set()
        after_set = set()
        pad = 4
        for dx in xrange(-pad, pad + 1):
            for dy in [0]:
                for dz in xrange(-pad, pad + 1):
                    if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                        continue
                    if before:
                        x, y, z = before
                        before_set.add((x + dx, y + dy, z + dz))
                    if after:
                        x, y, z = after
                        after_set.add((x + dx, y + dy, z + dz))
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

class PygletMinecraftClient(pyglet.window.Window):
    """Main client window using Pyglet for rendering."""
    
    def __init__(self, *args, **kwargs):
        super(PygletMinecraftClient, self).__init__(*args, **kwargs)
        
        # Whether or not the window exclusively captures the mouse
        self.exclusive = False
        
        # When flying gravity has no effect and speed is increased
        self.flying = False
        
        # Used for constant jumping
        self.jumping = False
        self.jumped = False
        
        # If this is true, a crouch offset is added
        self.crouch = False
        
        # Player sprint
        self.sprinting = False
        
        # FOV offset for effects
        self.fov_offset = 0
        
        # Collision types
        self.collision_types = {"top": False, "bottom": False, "right": False, "left": False}
        
        # Strafing movement
        self.strafe = [0, 0]
        
        # Current (x, y, z) position in the world
        self.position = (30, 50, 80)
        
        # Rotation (horizontal, vertical) in degrees
        self.rotation = (0, 0)
        
        # Which sector the player is currently in
        self.sector = None
        
        # The crosshairs at the center of the screen
        self.reticle = None
        
        # Velocity in the y (upward) direction
        self.dy = 0
        
        # Block inventory
        self.inventory = [BRICK, GRASS, SAND, WOOD, LEAF, FROG]
        self.block = self.inventory[0]
        
        # Convenience list of num keys
        self.num_keys = [
            key._1, key._2, key._3, key._4, key._5,
            key._6, key._7, key._8, key._9, key._0]
        
        # Instance of the model that handles the world
        self.model = NetworkModel()
        
        # The label that is displayed in the top left of the canvas
        self.label = pyglet.text.Label('', font_name='Arial', font_size=18,
            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 255))
        
        # This call schedules the update() method to be called TICKS_PER_SEC times per second
        pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
    
    def set_exclusive_mouse(self, exclusive):
        """If exclusive is True, the game will capture the mouse."""
        super(PygletMinecraftClient, self).set_exclusive_mouse(exclusive)
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
        # Process network messages
        self.model.process_network_messages()
        
        # Process rendering queue
        self.model.process_queue()
        
        # Handle sector changes
        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector
        
        # Update physics
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

        d = dt * speed # distance covered this tick.
        dx, dy, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, dy * d, dz * d
        # gravity
        if not self.flying:
            # Update your vertical speed: if you are falling, speed up until you
            # hit terminal velocity; if you are jumping, slow down until you
            # start falling.
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        # collisions
        old_pos = self.position
        x, y, z = old_pos
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT)
        self.position = (x, y, z)
        
        # Send position update to server
        if self.model.connected:
            self.model.send_message({
                'type': 'move',
                'position': list(self.position)
            })

        # Sprinting logic
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
                # How much overlap you have with this dimension.
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
                    # If you are colliding with the ground or ceiling, stop
                    # falling / rising.
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
            if (button == mouse.RIGHT) or \
                    ((button == mouse.LEFT) and (modifiers & key.MOD_CTRL)):
                # Right click or Ctrl+Left click - place block
                if previous:
                    # Send add block message to server
                    block_type = list(BLOCK_TEXTURES.keys())[0]  # Default to first block type
                    for bt, texture in BLOCK_TEXTURES.items():
                        if texture == self.block:
                            block_type = bt
                            break
                    self.model.send_message({
                        'type': 'add_block',
                        'position': list(previous),
                        'block_type': block_type
                    })
            elif button == pyglet.window.mouse.LEFT and block:
                # Left click - remove block
                texture = self.model.world[block]
                # Don't remove stone blocks
                if texture != BLOCK_TEXTURES[STONE]:
                    self.model.send_message({
                        'type': 'remove_block',
                        'position': list(block)
                    })
        else:
            self.set_exclusive_mouse(True)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Called when the player moves the mouse."""
        if self.exclusive:
            x, y = self.rotation
            x, y = x + dx * MOUSE_SENSITIVITY, y + dy * MOUSE_SENSITIVITY
            y = max(-90, min(90, y))
            self.rotation = (x, y)
    
    def on_key_press(self, symbol, modifiers):
        """Called when the player presses a key."""
        if symbol == key.Z or symbol == key.W:  # Forward (AZERTY Z or QWERTY W)
            self.strafe[0] -= 1
        elif symbol == key.S:  # Backward (same in both layouts)
            self.strafe[0] += 1
        elif symbol == key.Q or symbol == key.A:  # Left (AZERTY Q or QWERTY A)
            self.strafe[1] -= 1
        elif symbol == key.D:  # Right (same in both layouts)
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
        elif symbol == key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif symbol in self.num_keys:
            index = (symbol - self.num_keys[0]) % len(self.inventory)
            self.block = self.inventory[index]
    
    def on_key_release(self, symbol, modifiers):
        """Called when the player releases a key."""
        if symbol == key.Z or symbol == key.W:  # Forward (AZERTY Z or QWERTY W)
            self.strafe[0] += 1
        elif symbol == key.S:  # Backward (same in both layouts)
            self.strafe[0] -= 1
        elif symbol == key.Q or symbol == key.A:  # Left (AZERTY Q or QWERTY A)
            self.strafe[1] += 1
        elif symbol == key.D:  # Right (same in both layouts)
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
        # Create crosshair vertex list
        try:
            self.reticle = pyglet.graphics.vertex_list(4, 
                ('v2f/static', (float(x - n), float(y), float(x + n), float(y), float(x), float(y - n), float(x), float(y + n)))
            )
        except:
            # Fallback for different Pyglet versions
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
            vertex_data = cube_vertices(x, y, z, BLOCK_OUTLINE_SIZE)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    
    def draw_label(self):
        """Draw the label in the top left of the screen."""
        x, y, z = self.position
        self.label.text = '%02d (%.2f, %.2f, %.2f) %d / %d' % (
            pyglet.clock.get_fps(), x, y, z,
            len(self.model._shown), len(self.model.world))
        self.label.draw()
    
    def draw_reticle(self):
        """Draw the crosshairs in the center of the screen."""
        glColor3d(0, 0, 0)
        if hasattr(self.reticle, 'draw'):
            try:
                self.reticle.draw(mode=GL_LINES)
            except TypeError:
                self.reticle.draw(GL_LINES)

def setup_fog():
    """Configure the OpenGL fog properties."""
    try:
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
        glHint(GL_FOG_HINT, GL_DONT_CARE)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 40.0)
        glFogf(GL_FOG_END, 60.0)
    except:
        # Fog not supported
        pass

def setup():
    """Basic OpenGL configuration."""
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()

def main():
    """Main function to start the pyglet client."""
    window = PygletMinecraftClient(width=1280, height=720, caption='Minecraft - Pyglet Client', resizable=True)
    window.set_exclusive_mouse(True)
    setup()
    print("Pyglet Minecraft Client started!")
    print("Controls:")
    print("  WASD/ZQSD: Move")
    print("  Space: Jump")
    print("  Tab: Toggle flying")
    print("  Mouse: Look around")
    print("  Left click: Remove block")
    print("  Right click: Place block")
    print("  1-6: Select block type")
    print("  ESC: Release mouse")
    pyglet.app.run()

if __name__ == "__main__":
    main()