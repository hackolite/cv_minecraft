#!/usr/bin/env python3
"""
Client de débogage - Version avec logs détaillés
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
    CardMaker, PerspectiveLens, Vec3, Point3,
    DirectionalLight, AmbientLight
)
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText

# Block types
GRASS = "grass"
SAND = "sand"
BRICK = "brick"
STONE = "stone"
WOOD = "wood"
LEAF = "leaf"
WATER = "water"
FROG = "frog"

def normalize(position):
    """Convert float position to integer block position."""
    x, y, z = position
    return (int(round(x)), int(round(y)), int(round(z)))

class DebugClient(ShowBase):
    """Client de débogage avec logs détaillés."""
    
    def __init__(self):
        ShowBase.__init__(self)
        print("=== DEBUT INITIALISATION CLIENT ===")
        
        # Network
        self.outgoing_messages = Queue()
        self.incoming_messages = Queue()
        self.connected = False
        
        # World
        self.blocks = {}
        self.block_types = {}
        
        # Player
        self.position = Vec3(32, 32, 25)  # Position initiale plus appropriée
        self.last_sent_position = None  # Track last sent position to avoid spam
        self.position_update_threshold = 0.5  # Minimum distance to send update
        
        # Setup basique
        self.setup_camera()
        self.setup_lighting()
        self.setup_ui()
        self.setup_controls()
        
        # Start network
        self.start_network_thread()
        
        # Update task
        self.taskMgr.add(self.update, "update")
        
        print("=== FIN INITIALISATION CLIENT ===")
    
    def setup_camera(self):
        """Setup camera."""
        print("Setting up camera...")
        # Enable mouse for camera control
        self.camera.setPos(self.position)
        self.camera.setHpr(0, 0, 0)
        
        # Enable depth testing for proper 3D rendering
        self.render.setDepthTest(True)
        self.render.setDepthWrite(True)
        
        # Set up proper perspective lens
        lens = PerspectiveLens()
        lens.setFov(70)
        lens.setNear(0.1)
        lens.setFar(1000.0)
        self.cam.node().setLens(lens)
        
        # Setup mouse controls for camera
        self.mouse_sensitivity = 0.15
        self.movement_speed = 1.5  # Units per key press
        self.camera_pitch = 0
        self.camera_yaw = 0
        
        print(f"Camera position: {self.camera.getPos()}")
        print("Depth testing enabled for proper 3D rendering")
        print("Mouse controls enabled for camera view changes")
    
    def setup_lighting(self):
        """Setup lighting."""
        print("Setting up lighting...")
        
        # Ambient light
        ambient_light = AmbientLight('ambient')
        ambient_light.setColor((0.5, 0.5, 0.5, 1))
        ambient_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_np)
        
        # Directional light
        sun_light = DirectionalLight('sun')
        sun_light.setColor((1, 1, 1, 1))
        sun_light.setDirection(Vec3(-1, -1, -1))
        sun_np = self.render.attachNewNode(sun_light)
        self.render.setLight(sun_np)
        
        print("Lighting setup complete")
    
    def setup_ui(self):
        """Setup UI."""
        print("Setting up UI...")
        
        self.status_text = OnscreenText(
            text="Initializing...",
            pos=(0, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1)
        )
        
        self.debug_text = OnscreenText(
            text="Debug info",
            pos=(-0.95, 0.8),
            scale=0.04,
            fg=(1, 1, 0, 1),
            align=1
        )
        
        print("UI setup complete")
    
    def setup_controls(self):
        """Setup basic controls."""
        print("Setting up controls...")
        
        # Debug controls
        self.accept("escape", sys.exit)
        self.accept("r", self.request_world_data)
        self.accept("t", self.test_add_block)
        
        # Camera movement controls (support both QWERTY and AZERTY)
        self.accept("w", self.move_forward)   # QWERTY forward
        self.accept("z", self.move_forward)   # AZERTY forward
        self.accept("s", self.move_backward)  # Same in both layouts
        self.accept("a", self.move_left)      # QWERTY left
        self.accept("q", self.move_left)      # AZERTY left
        self.accept("d", self.move_right)     # Same in both layouts
        self.accept("space", self.move_up)
        self.accept("c", self.move_down)
        
        # Camera rotation (keyboard fallback)
        self.accept("arrow_left", self.turn_left)
        self.accept("arrow_right", self.turn_right)
        self.accept("arrow_up", self.look_up)
        self.accept("arrow_down", self.look_down)
        
        # Mouse controls for camera
        self.accept("mouse1", self.mouse_click)  # Left click
        self.accept("mouse3", self.mouse_right_click)  # Right click
        
        # Enable mouse tracking for camera rotation
        self.mouse_enabled = True
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_x = self.mouseWatcherNode.getMouseX()
            self.last_mouse_y = self.mouseWatcherNode.getMouseY()
        else:
            self.last_mouse_x = 0
            self.last_mouse_y = 0
        
        print("Controls setup complete (including mouse camera controls)")
    
    def move_forward(self):
        """Move camera forward."""
        self.camera.setY(self.camera, self.movement_speed)
        self.update_camera_position()
        
    def move_backward(self):
        """Move camera backward.""" 
        self.camera.setY(self.camera, -self.movement_speed)
        self.update_camera_position()
        
    def move_left(self):
        """Move camera left."""
        self.camera.setX(self.camera, -self.movement_speed)
        self.update_camera_position()
        
    def move_right(self):
        """Move camera right."""
        self.camera.setX(self.camera, self.movement_speed)
        self.update_camera_position()
        
    def move_up(self):
        """Move camera up."""
        self.camera.setZ(self.camera.getZ() + self.movement_speed)
        self.update_camera_position()
        
    def move_down(self):
        """Move camera down."""
        self.camera.setZ(self.camera.getZ() - self.movement_speed)
        self.update_camera_position()
        
    def turn_left(self):
        """Turn camera left."""
        self.camera_yaw += 10
        self.update_camera_rotation()
        
    def turn_right(self):
        """Turn camera right."""
        self.camera_yaw -= 10
        self.update_camera_rotation()
        
    def look_up(self):
        """Look up."""
        self.camera_pitch = max(-90, self.camera_pitch + 10)
        self.update_camera_rotation()
        
    def look_down(self):
        """Look down."""
        self.camera_pitch = min(90, self.camera_pitch - 10)
        self.update_camera_rotation()
    
    def update_camera_rotation(self):
        """Update camera rotation based on pitch and yaw."""
        self.camera.setHpr(self.camera_yaw, self.camera_pitch, 0)
    
    def mouse_click(self):
        """Handle left mouse click."""
        print("Left mouse click detected")
    
    def mouse_right_click(self):
        """Handle right mouse click."""
        print("Right mouse click detected")
    
    def handle_mouse_movement(self):
        """Handle mouse movement for camera rotation."""
        if not self.mouse_enabled or not self.mouseWatcherNode.hasMouse():
            return
        
        # Get current mouse position
        mouse_x = self.mouseWatcherNode.getMouseX()
        mouse_y = self.mouseWatcherNode.getMouseY()
        
        # Calculate mouse movement delta
        delta_x = mouse_x - self.last_mouse_x
        delta_y = mouse_y - self.last_mouse_y
        
        # Update camera rotation based on mouse movement
        if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
            self.camera_yaw -= delta_x * self.mouse_sensitivity * 50  # Reduced from 100 to 50
            self.camera_pitch = max(-90, min(90, self.camera_pitch + delta_y * self.mouse_sensitivity * 50))
            self.update_camera_rotation()
        
        # Update last mouse position
        self.last_mouse_x = mouse_x
        self.last_mouse_y = mouse_y
        
    def update_camera_position(self):
        """Update camera position and send to server if needed."""
        self.position = self.camera.getPos()
        
        # Send position update to server only if moved significantly
        if self.connected:
            should_send = False
            
            if self.last_sent_position is None:
                should_send = True
            else:
                # Calculate distance moved since last update
                distance = (self.position - self.last_sent_position).length()
                if distance >= self.position_update_threshold:
                    should_send = True
            
            if should_send:
                position_data = {
                    'type': 'move',
                    'position': [self.position.x, self.position.y, self.position.z]
                }
                self.outgoing_messages.put(json.dumps(position_data))
                self.last_sent_position = Vec3(self.position)
    
    def request_world_data(self):
        """Demander les données du monde manuellement."""
        print("=== DEMANDE MANUELLE WORLD DATA ===")
        if self.connected:
            request = {'type': 'get_world'}
            self.outgoing_messages.put(json.dumps(request))
            print("World data request sent")
        else:
            print("Not connected!")
    
    def test_add_block(self):
        """Test d'ajout d'un bloc manuel."""
        print("=== TEST AJOUT BLOC MANUEL ===")
        test_pos = (32, 32, 26)  # Juste au-dessus de la position du joueur
        self.add_block_visual(test_pos, BRICK)
        print(f"Test block added at {test_pos}")
    
    def create_block_node(self, position, block_type):
        """Create a visual block - VERSION DEBUG."""
        print(f"=== CREATION BLOC VISUEL ===")
        print(f"Position: {position}, Type: {block_type}")
        
        try:
            # Create simple cube
            cm = CardMaker("block")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            print("CardMaker created")
            
            # Create node
            block_node = self.render.attachNewNode(f"block_{position}")
            print(f"Block node created: {block_node}")
            
            # Colors
            colors = {
                GRASS: (0.2, 0.8, 0.2, 1),
                SAND: (0.9, 0.8, 0.4, 1),
                BRICK: (0.8, 0.3, 0.2, 1),
                STONE: (0.5, 0.5, 0.5, 1),
                WOOD: (0.6, 0.4, 0.2, 1),
                LEAF: (0.1, 0.6, 0.1, 1),
                WATER: (0.2, 0.4, 0.8, 0.7),
                FROG: (0.8, 0.8, 0.2, 1)
            }
            
            color = colors.get(block_type, (1, 0, 1, 1))  # Magenta si type inconnu
            print(f"Using color: {color} for type: {block_type}")
            
            # Create faces
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
            
            print(f"Created {len(faces)} faces")
            
            # Position the block
            x, y, z = position
            block_node.setPos(x, y, z)
            print(f"Block positioned at: {block_node.getPos()}")
            
            # Verify visibility
            block_node.show()
            print(f"Block visibility: {not block_node.isHidden()}")
            print(f"Block parent: {block_node.getParent()}")
            
            return block_node
            
        except Exception as e:
            print(f"ERREUR CREATION BLOC: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_block_visual(self, position, block_type):
        """Add visual block - VERSION DEBUG."""
        print(f"\n=== ADD_BLOCK_VISUAL ===")
        print(f"Position: {position} (type: {type(position)})")
        print(f"Block type: {block_type} (type: {type(block_type)})")
        
        if position in self.blocks:
            print(f"Block already exists at {position}")
            return
        
        try:
            block_node = self.create_block_node(position, block_type)
            if block_node:
                self.blocks[position] = block_node
                self.block_types[position] = block_type
                print(f"Block successfully added. Total blocks: {len(self.blocks)}")
                
                # Verify render tree
                print(f"Block in render tree: {block_node.getParent() == self.render}")
                print(f"Render children count: {self.render.getNumChildren()}")
                
                # Test visibility from camera
                cam_pos = self.camera.getPos()
                block_pos = block_node.getPos()
                distance = (cam_pos - block_pos).length()
                print(f"Distance from camera: {distance}")
                
                return True
            else:
                print("FAILED TO CREATE BLOCK NODE")
                return False
                
        except Exception as e:
            print(f"ERREUR ADD_BLOCK_VISUAL: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def handle_server_message(self, data):
        """Handle server message - VERSION DEBUG."""
        message_type = data.get('type')
        print(f"\n=== MESSAGE SERVEUR: {message_type} ===")
        
        if message_type == 'welcome':
            print("Received welcome message")
            self.status_text.setText("Connected - Press R for world data")
            self.connected = True
            
            # Handle initial spawn position from server
            spawn_position = data.get('position')
            if spawn_position:
                print(f"Setting spawn position: {spawn_position}")
                # Convert to Vec3 and set camera position
                spawn_vec = Vec3(spawn_position[0], spawn_position[1], spawn_position[2])
                self.camera.setPos(spawn_vec)
                self.position = spawn_vec
                self.last_sent_position = Vec3(spawn_vec)  # Initialize last sent position
            
            # Auto-request world data
            print("Auto-requesting world data...")
            self.request_world_data()
            
        elif message_type == 'player_moved':
            # Handle other player movements (for multiplayer)
            position = data.get('position')
            if position:
                print(f"Other player moved to: {position}")
            
        elif message_type == 'world_data':
            blocks = data.get('blocks', [])
            textures = data.get('textures', {})
            
            print(f"WORLD_DATA received:")
            print(f"  - Blocks count: {len(blocks)}")
            print(f"  - Textures count: {len(textures)}")
            
            if blocks:
                print("First 3 blocks:")
                for i, block in enumerate(blocks[:3]):
                    print(f"  Block {i}: {block}")
                
                print(f"Last block: {blocks[-1]}")
            
            success_count = 0
            error_count = 0
            
            for i, block_data in enumerate(blocks):
                try:
                    if isinstance(block_data, dict):
                        position = block_data.get('position')
                        block_type = block_data.get('block_type')
                        
                        if position and block_type:
                            # Convert to tuple if it's a list
                            if isinstance(position, list):
                                position = tuple(position)
                            
                            success = self.add_block_visual(position, block_type)
                            if success:
                                success_count += 1
                            else:
                                error_count += 1
                        else:
                            print(f"Block {i}: Missing position or block_type: {block_data}")
                            error_count += 1
                    else:
                        print(f"Block {i}: Not a dict: {block_data}")
                        error_count += 1
                        
                except Exception as e:
                    print(f"Error processing block {i}: {e}")
                    error_count += 1
            
            print(f"WORLD_DATA processing complete:")
            print(f"  - Success: {success_count}")
            print(f"  - Errors: {error_count}")
            print(f"  - Total blocks in memory: {len(self.blocks)}")
            
            self.status_text.setText(f"Loaded: {success_count}, Errors: {error_count}")
            
        elif message_type == 'world_chunk':
            blocks = data.get('blocks', [])
            chunk_index = data.get('chunk_index', 0)
            total_chunks = data.get('total_chunks', 1)
            
            print(f"WORLD_CHUNK received: {chunk_index+1}/{total_chunks} ({len(blocks)} blocks)")
            
            success_count = 0
            error_count = 0
            
            for i, block_data in enumerate(blocks):
                try:
                    if isinstance(block_data, dict):
                        position = block_data.get('position')
                        block_type = block_data.get('block_type')
                        
                        if position and block_type:
                            # Convert to tuple if it's a list
                            if isinstance(position, list):
                                position = tuple(position)
                            
                            success = self.add_block_visual(position, block_type)
                            if success:
                                success_count += 1
                            else:
                                error_count += 1
                        else:
                            print(f"Block {i}: Missing position or block_type: {block_data}")
                            error_count += 1
                    else:
                        print(f"Block {i}: Not a dict: {block_data}")
                        error_count += 1
                        
                except Exception as e:
                    print(f"Error processing block {i}: {e}")
                    error_count += 1
            
            print(f"CHUNK {chunk_index+1} processed: Success: {success_count}, Errors: {error_count}")
            
            self.status_text.setText(f"Loading chunk {chunk_index+1}/{total_chunks}...")
            
        elif message_type == 'world_complete':
            total_blocks = data.get('total_blocks', 0)
            print(f"WORLD_COMPLETE: All {total_blocks} blocks loaded")
            print(f"Total blocks in memory: {len(self.blocks)}")
            self.status_text.setText(f"Loaded: {len(self.blocks)} blocks")
            
        else:
            print(f"Other message type: {message_type}")
            print(f"Data: {data}")
    
    def process_network_messages(self):
        """Process network messages."""
        while not self.incoming_messages.empty():
            try:
                message = self.incoming_messages.get_nowait()
                if isinstance(message, dict):
                    self.handle_server_message(message)
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def update(self, task):
        """Update task."""
        # Handle mouse movement for camera rotation
        self.handle_mouse_movement()
        
        # Process messages
        self.process_network_messages()
        
        # Update debug info
        cam_pos = self.camera.getPos()
        cam_hpr = self.camera.getHpr()
        self.debug_text.setText(
            f"Blocks: {len(self.blocks)}\n"
            f"Pos: ({cam_pos.x:.1f}, {cam_pos.y:.1f}, {cam_pos.z:.1f})\n"
            f"HPR: ({cam_hpr.x:.0f}, {cam_hpr.y:.0f}, {cam_hpr.z:.0f})\n"
            f"Connected: {self.connected}\n"
            f"WASD: Move, Space/C: Up/Down\n"
            f"Mouse: Look around, Arrows: Look (fallback)\n"
            f"R: Request world, T: Test block\n"
            f"ESC: Exit"
        )
        
        return task.cont
    
    def start_network_thread(self):
        """Start network thread."""
        print("Starting network thread...")
        self.network_thread = threading.Thread(target=self.network_worker)
        self.network_thread.daemon = True
        self.network_thread.start()
    
    def network_worker(self):
        """Network worker."""
        async def connect_and_communicate():
            try:
                uri = "ws://localhost:8765"
                print(f"Connecting to {uri}...")
                
                async with websockets.connect(uri) as websocket:
                    print("Connected!")
                    
                    # Send join
                    join_msg = {'type': 'join', 'name': 'DebugPlayer'}
                    await websocket.send(json.dumps(join_msg))
                    print("Join message sent")
                    
                    async def listen():
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                self.incoming_messages.put(data)
                            except Exception as e:
                                print(f"Error parsing message: {e}")
                                print(f"Message: {message[:200]}...")
                    
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
                import traceback
                traceback.print_exc()
        
        try:
            asyncio.run(connect_and_communicate())
        except Exception as e:
            print(f"Error in network worker: {e}")

# Alias for compatibility with tests
MinecraftClient = DebugClient

def main():
    """Main function."""
    print("=== LANCEMENT DEBUG CLIENT ===")
    app = DebugClient()
    app.run()

if __name__ == "__main__":
    main()
