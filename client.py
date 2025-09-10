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
        self.disableMouse()
        self.camera.setPos(self.position)
        self.camera.setHpr(0, 0, 0)
        print(f"Camera position: {self.camera.getPos()}")
    
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
        
        # Juste les controles de base pour le debug
        self.accept("escape", sys.exit)
        self.accept("r", self.request_world_data)
        self.accept("t", self.test_add_block)
        
        print("Controls setup complete")
    
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
            
            # Auto-request world data
            print("Auto-requesting world data...")
            self.request_world_data()
            
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
            print("Received world_chunk - processing same as world_data")
            # Process same as world_data
            self.handle_server_message({'type': 'world_data', **data})
            
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
        # Process messages
        self.process_network_messages()
        
        # Update debug info
        cam_pos = self.camera.getPos()
        self.debug_text.setText(
            f"Blocks: {len(self.blocks)}\n"
            f"Pos: ({cam_pos.x:.1f}, {cam_pos.y:.1f}, {cam_pos.z:.1f})\n"
            f"Connected: {self.connected}\n"
            f"Press R: Request world\n"
            f"Press T: Test block\n"
            f"Press ESC: Exit"
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

def main():
    """Main function."""
    print("=== LANCEMENT DEBUG CLIENT ===")
    app = DebugClient()
    app.run()

if __name__ == "__main__":
    main()
