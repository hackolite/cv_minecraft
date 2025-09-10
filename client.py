#!/usr/bin/env python3
"""
Minecraft-like Client using Panda3D
Handles rendering, input, and server communication
"""

import asyncio
import websockets
import json
import math
import sys
import threading
from queue import Queue

# Panda3D imports
from panda3d.core import (
    CardMaker, PerspectiveLens, Vec3, Point3, BitMask32,
    CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue,
    CollisionRay, NodePath, TransformState, RenderState, Texture,
    TextureStage, Material, VBase4, DirectionalLight, AmbientLight,
    AntialiasAttrib, DepthTestAttrib, CullFaceAttrib, LightAttrib
)
from panda3d.physics import BaseIntegrator, LinearVectorForce, ForceNode
from direct.showbase.ShowBase import ShowBase
from direct.showbase import DirectObject
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from direct.actor.Actor import Actor

# Block types (same as server)
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
    result.extend(top)    # top
    result.extend(bottom) # bottom
    result.extend(side)   # left
    result.extend(side)   # right
    result.extend(side)   # front
    result.extend(side)   # back
    return result

# Block type definitions (must match server)
GRASS = tex_coords((1, 0), (0, 1), (0, 0))
SAND = tex_coords((1, 1), (1, 1), (1, 1))
BRICK = tex_coords((2, 0), (2, 0), (2, 0))
STONE = tex_coords((2, 1), (2, 1), (2, 1))
WOOD = tex_coords((3, 1), (3, 1), (3, 1))
LEAF = tex_coords((3, 0), (3, 0), (3, 0))
WATER = tex_coords((0, 2), (0, 2), (0, 2))
FROG = tex_coords((1, 2), (1, 2), (1, 2))

# Constants
WALKING_SPEED = 5
FLYING_SPEED = 15
GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.0
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
PLAYER_HEIGHT = 2

def normalize(position):
    """Convert float position to integer block position."""
    x, y, z = position
    return (int(round(x)), int(round(y)), int(round(z)))

class MinecraftClient(ShowBase):
    """Main client class using Panda3D for rendering."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Network
        self.websocket = None
        self.message_queue = Queue()
        self.connected = False
        
        # Player state
        self.position = Vec3(30, 50, 80)
        self.velocity = Vec3(0, 0, 0)
        self.flying = False
        self.jumping = False
        self.on_ground = False
        
        # Input state
        self.key_map = {
            'forward': False,
            'backward': False, 
            'left': False,
            'right': False,
            'jump': False
        }
        
        # World
        self.blocks = {}  # position -> NodePath
        self.block_types = {}  # position -> block_type
        
        # Inventory
        self.inventory = [BRICK, GRASS, SAND, WOOD, LEAF, FROG]
        self.current_block = 0
        
        # Setup
        self.setup_camera()
        self.setup_lighting()
        self.setup_controls()
        self.setup_ui()
        self.setup_collision()
        self.setup_physics()
        
        # Start network connection
        self.start_network_thread()
        
        # Start update task
        self.taskMgr.add(self.update, "update")
    
    def setup_camera(self):
        """Setup camera and disable default mouse controls."""
        self.disableMouse()
        
        # Set camera position and orientation
        self.camera.setPos(self.position)
        self.camera.setHpr(0, 0, 0)
        
        # Setup perspective camera
        lens = PerspectiveLens()
        lens.setFov(80)
        lens.setNear(0.1)
        lens.setFar(1000)
        self.cam.node().setLens(lens)
    
    def setup_lighting(self):
        """Setup basic lighting and render states."""
        # Ambient light
        ambient_light = AmbientLight('ambient')
        ambient_light.setColor((0.3, 0.3, 0.3, 1))
        ambient_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_np)
        
        # Directional light (sun)
        sun_light = DirectionalLight('sun')
        sun_light.setColor((0.8, 0.8, 0.6, 1))
        sun_light.setDirection(Vec3(-1, -1, -1))
        sun_np = self.render.attachNewNode(sun_light)
        self.render.setLight(sun_np)
        
        # Enable depth testing for proper block rendering
        self.render.setDepthTest(True)
        self.render.setDepthWrite(True)
    
    def setup_controls(self):
        """Setup keyboard controls."""
        # Accept key events
        self.accept("z", self.set_key, ["forward", True])
        self.accept("z-up", self.set_key, ["forward", False])
        self.accept("s", self.set_key, ["backward", True])
        self.accept("s-up", self.set_key, ["backward", False])
        self.accept("q", self.set_key, ["left", True])
        self.accept("q-up", self.set_key, ["left", False])
        self.accept("d", self.set_key, ["right", True])
        self.accept("d-up", self.set_key, ["right", False])
        self.accept("space", self.set_key, ["jump", True])
        self.accept("space-up", self.set_key, ["jump", False])
        
        # Block selection
        for i in range(1, 7):
            self.accept(str(i), self.select_block, [i-1])
        
        # Mouse events
        self.accept("mouse1", self.on_left_click)  # Remove block
        self.accept("mouse3", self.on_right_click)  # Place block
        
        # Toggle flying
        self.accept("tab", self.toggle_flying)
        
        # Mouse look
        self.mouse_sensitivity = 0.1
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Enable mouse look task
        self.taskMgr.add(self.mouse_look_task, "mouse_look")
    
    def setup_ui(self):
        """Setup UI elements."""
        # Status text
        self.status_text = OnscreenText(
            text="Connecting to server...",
            pos=(0, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=0  # center
        )
        
        # Block info
        self.block_text = OnscreenText(
            text="Block: Brick",
            pos=(-0.95, -0.95),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=1  # left
        )
        
        # Position info
        self.pos_text = OnscreenText(
            text="Position: (0, 0, 0)",
            pos=(0.95, -0.95),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=3  # right
        )
    
    def setup_collision(self):
        """Setup collision detection."""
        self.cTrav = CollisionTraverser()
        self.collision_queue = CollisionHandlerQueue()
        
        # Player collision sphere
        self.player_collision = CollisionNode('player')
        self.player_collision.addSolid(CollisionSphere(0, 0, 0, PLAYER_HEIGHT/2))
        self.player_collision_np = self.camera.attachNewNode(self.player_collision)
        self.cTrav.addCollider(self.player_collision_np, self.collision_queue)
    
    def setup_physics(self):
        """Setup physics (gravity)."""
        self.dt = 0
    
    def set_key(self, key, value):
        """Set key state."""
        self.key_map[key] = value
    
    def select_block(self, index):
        """Select block type."""
        if 0 <= index < len(self.inventory):
            self.current_block = index
            block_names = ['Brick', 'Grass', 'Sand', 'Wood', 'Leaf', 'Frog']
            self.block_text.setText(f"Block: {block_names[index]}")
    
    def toggle_flying(self):
        """Toggle flying mode."""
        self.flying = not self.flying
        if self.flying:
            self.velocity.z = 0  # Stop falling
    
    def mouse_look_task(self, task):
        """Handle mouse look."""
        if self.mouseWatcherNode.hasMouse():
            x = self.mouseWatcherNode.getMouseX()
            y = self.mouseWatcherNode.getMouseY()
            
            # Calculate mouse movement
            if hasattr(self, 'last_mouse_x'):
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y
                
                # Apply mouse sensitivity
                dx *= self.mouse_sensitivity * 100
                dy *= self.mouse_sensitivity * 100
                
                # Update camera rotation
                h, p, r = self.camera.getHpr()
                h -= dx
                p = max(-90, min(90, p - dy))
                self.camera.setHpr(h, p, r)
            
            self.last_mouse_x = x
            self.last_mouse_y = y
        
        return task.cont
    
    def get_look_vector(self):
        """Get the direction the camera is looking."""
        h, p, r = self.camera.getHpr()
        # Convert to radians
        h_rad = math.radians(h)
        p_rad = math.radians(p)
        
        # Calculate direction vector
        dx = math.sin(h_rad) * math.cos(p_rad)
        dy = -math.cos(h_rad) * math.cos(p_rad)
        dz = -math.sin(p_rad)
        
        return Vec3(dx, dy, dz)
    
    def ray_cast(self, origin, direction, max_distance=8):
        """Cast a ray and find the first block hit."""
        step = 0.1
        current_pos = Vec3(origin)
        
        for i in range(int(max_distance / step)):
            current_pos += direction * step
            block_pos = normalize((current_pos.x, current_pos.y, current_pos.z))
            
            if block_pos in self.blocks:
                # Find the position just before hitting the block
                prev_pos = current_pos - direction * step
                prev_block_pos = normalize((prev_pos.x, prev_pos.y, prev_pos.z))
                return block_pos, prev_block_pos
        
        return None, None
    
    def on_left_click(self):
        """Handle left mouse click (remove block)."""
        if not self.connected:
            return
            
        look_vector = self.get_look_vector()
        hit_pos, _ = self.ray_cast(self.camera.getPos(), look_vector)
        
        if hit_pos:
            # Send remove block message to server
            message = {
                'type': 'remove_block',
                'position': hit_pos
            }
            self.message_queue.put(json.dumps(message))
    
    def on_right_click(self):
        """Handle right mouse click (place block)."""
        if not self.connected:
            return
            
        look_vector = self.get_look_vector()
        hit_pos, place_pos = self.ray_cast(self.camera.getPos(), look_vector)
        
        if hit_pos and place_pos and place_pos not in self.blocks:
            # Send add block message to server
            message = {
                'type': 'add_block',
                'position': place_pos,
                'block_type': self.inventory[self.current_block]
            }
            self.message_queue.put(json.dumps(message))
    
    def update(self, task):
        """Main update loop."""
        dt = globalClock.getDt()
        self.dt = dt
        
        # Update movement
        self.update_movement(dt)
        
        # Update position text
        pos = self.camera.getPos()
        self.pos_text.setText(f"Position: ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})")
        
        # Process network messages
        self.process_network_messages()
        
        return task.cont
    
    def update_movement(self, dt):
        """Update player movement and physics."""
        # Calculate movement direction
        move_vector = Vec3(0, 0, 0)
        
        if self.key_map['forward']:
            move_vector.y -= 1
        if self.key_map['backward']:
            move_vector.y += 1
        if self.key_map['left']:
            move_vector.x -= 1
        if self.key_map['right']:
            move_vector.x += 1
        
        # Normalize movement vector
        if move_vector.length() > 0:
            move_vector.normalize()
        
        # Apply camera rotation to movement
        h, p, r = self.camera.getHpr()
        h_rad = math.radians(h)
        
        # Rotate movement vector by camera heading
        cos_h = math.cos(h_rad)
        sin_h = math.sin(h_rad)
        
        world_move = Vec3(
            move_vector.x * cos_h - move_vector.y * sin_h,
            move_vector.x * sin_h + move_vector.y * cos_h,
            0
        )
        
        # Apply speed
        if self.flying:
            speed = FLYING_SPEED
            if self.key_map['jump']:
                world_move.z += 1
        else:
            speed = WALKING_SPEED
            
            # Apply gravity
            self.velocity.z -= GRAVITY * dt
            
            # Handle jumping
            if self.key_map['jump'] and self.on_ground:
                self.velocity.z = JUMP_SPEED
                self.jumping = True
                self.on_ground = False
        
        # Apply movement
        world_move *= speed
        if not self.flying:
            world_move.z = self.velocity.z
        
        # Update position
        new_pos = self.camera.getPos() + world_move * dt
        self.camera.setPos(new_pos)
        
        # Simple ground check
        if not self.flying:
            if new_pos.z <= 1:  # Ground level
                new_pos.z = 1
                self.camera.setPos(new_pos)
                self.velocity.z = 0
                self.on_ground = True
                self.jumping = False
        
        # Send position update to server (throttle to avoid spam)
        if hasattr(self, 'last_pos_update'):
            if (new_pos - self.last_pos_update).length() > 0.5:
                self.send_position_update()
                self.last_pos_update = new_pos
        else:
            self.last_pos_update = new_pos
            self.send_position_update()
    
    def send_position_update(self):
        """Send position update to server."""
        if self.connected:
            pos = self.camera.getPos()
            message = {
                'type': 'move',
                'position': (pos.x, pos.y, pos.z)
            }
            self.message_queue.put(json.dumps(message))
    
    def create_block_node(self, position, block_type):
        """Create a visual block at the given position."""
        # Create cube geometry
        cm = CardMaker("block")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        
        # Create a simple cube by combining 6 cards
        block_node = self.render.attachNewNode("block")
        
        # For simplicity, create a basic colored cube
        # In a full implementation, you'd apply the texture coordinates
        colors = {
            str(GRASS): (0.2, 0.8, 0.2, 1),
            str(SAND): (0.9, 0.8, 0.4, 1),
            str(BRICK): (0.8, 0.3, 0.2, 1),
            str(STONE): (0.5, 0.5, 0.5, 1),
            str(WOOD): (0.6, 0.4, 0.2, 1),
            str(LEAF): (0.1, 0.6, 0.1, 1),
            str(WATER): (0.2, 0.4, 0.8, 0.7),
            str(FROG): (0.8, 0.8, 0.2, 1)
        }
        
        color = colors.get(str(block_type), (0.5, 0.5, 0.5, 1))
        
        # Create 6 faces for a proper 1x1x1 cube
        faces = [
            ((0, 0, 0.5), (0, 0, 0)),    # front
            ((0, 0, -0.5), (0, 180, 0)), # back
            ((-0.5, 0, 0), (0, 90, 0)),  # left
            ((0.5, 0, 0), (0, -90, 0)),  # right
            ((0, 0.5, 0), (-90, 0, 0)),  # top
            ((0, -0.5, 0), (90, 0, 0))   # bottom
        ]
        
        for i, (offset, rotation) in enumerate(faces):
            face = block_node.attachNewNode(cm.generate())
            face.setPos(*offset)
            face.setHpr(*rotation)
            face.setColor(*color)
        
        # Position the block
        x, y, z = position
        block_node.setPos(x, y, z)
        
        return block_node
    
    def add_block_visual(self, position, block_type):
        """Add a visual block to the world."""
        if position not in self.blocks:
            block_node = self.create_block_node(position, block_type)
            self.blocks[position] = block_node
            self.block_types[position] = block_type
    
    def remove_block_visual(self, position):
        """Remove a visual block from the world."""
        if position in self.blocks:
            self.blocks[position].removeNode()
            del self.blocks[position]
            if position in self.block_types:
                del self.block_types[position]
    
    def process_network_messages(self):
        """Process messages received from network thread."""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                if isinstance(message, dict):
                    self.handle_server_message(message)
            except:
                pass
    
    def handle_server_message(self, data):
        """Handle message from server."""
        message_type = data.get('type')
        
        if message_type == 'welcome':
            self.status_text.setText("Connected to server")
            self.connected = True
            # Request world data
            request = {'type': 'get_world'}
            self.message_queue.put(json.dumps(request))
            
        elif message_type == 'world_data':
            blocks = data.get('blocks', [])
            for block_data in blocks:
                position = tuple(block_data['position'])
                block_type = block_data['block_type']
                self.add_block_visual(position, block_type)
            print(f"Loaded {len(blocks)} blocks from server")
            
        elif message_type == 'block_added':
            position = tuple(data['position'])
            block_type = data['block_type']
            self.add_block_visual(position, block_type)
            
        elif message_type == 'block_removed':
            position = tuple(data['position'])
            self.remove_block_visual(position)
    
    def start_network_thread(self):
        """Start network thread for WebSocket communication."""
        self.network_thread = threading.Thread(target=self.network_worker)
        self.network_thread.daemon = True
        self.network_thread.start()
    
    def network_worker(self):
        """Network thread worker."""
        async def connect_and_communicate():
            try:
                uri = "ws://localhost:8765"
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    
                    # Send join message
                    join_message = {
                        'type': 'join',
                        'name': 'Player'
                    }
                    await websocket.send(json.dumps(join_message))
                    
                    # Start listening for messages
                    async def listen_for_messages():
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                self.message_queue.put(data)
                            except json.JSONDecodeError:
                                print(f"Invalid JSON: {message}")
                    
                    async def send_queued_messages():
                        while True:
                            try:
                                # Check for outgoing messages
                                while not self.message_queue.empty():
                                    try:
                                        msg = self.message_queue.get_nowait()
                                        if isinstance(msg, str):
                                            await websocket.send(msg)
                                    except:
                                        pass
                                await asyncio.sleep(0.01)
                            except:
                                break
                    
                    # Run both tasks concurrently
                    await asyncio.gather(
                        listen_for_messages(),
                        send_queued_messages()
                    )
                    
            except Exception as e:
                print(f"Network error: {e}")
                self.message_queue.put({
                    'type': 'error',
                    'message': str(e)
                })
        
        # Run the async network code
        asyncio.run(connect_and_communicate())

def main():
    """Main function to start the client."""
    client = MinecraftClient()
    client.run()

if __name__ == "__main__":
    main()